"""
Advanced memory management strategies for n-gram processing.

This module contains fallback processing strategies for when memory pressure
becomes critical during n-gram analysis.
"""

import heapq
import os
import tempfile
from typing import List, Optional

import polars as pl

from app.logger import get_logger
from app.utils import MemoryManager


class ExternalSortUniqueExtractor:
    """
    Disk-based unique extraction using external sorting for critical memory pressure.

    Uses merge sort algorithm with temporary files to handle datasets that exceed
    available memory while maintaining reasonable performance.
    """

    def __init__(self, memory_manager: MemoryManager, temp_dir: Optional[str] = None, progress_manager=None):
        self.memory_manager = memory_manager
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.temp_files = []
        self.progress_manager = progress_manager
        self.logger = get_logger(f"{__name__}.ExternalSortUniqueExtractor")

    def extract_unique(
        self, ldf_data: pl.LazyFrame, column_name: str = "ngram_text"
    ) -> pl.DataFrame:
        """Extract unique values using external sorting."""

        try:
            # Phase 1: Sort and split data into sorted chunks
            sorted_chunks = self._create_sorted_chunks(ldf_data, column_name)

            # Phase 2: Merge sorted chunks while eliminating duplicates
            result = self._merge_sorted_chunks(sorted_chunks, column_name)

            return result

        finally:
            # Phase 3: Always cleanup temporary files
            self._cleanup_temp_files()

    def _create_sorted_chunks(
        self, ldf_data: pl.LazyFrame, column_name: str
    ) -> List[str]:
        """Create sorted temporary files from input data."""
        chunk_files = []

        # Use very small chunks for critical memory pressure
        chunk_size = self.memory_manager.calculate_adaptive_chunk_size(
            10000, "unique_extraction"
        )

        total_count = ldf_data.select(pl.len()).collect().item()
        total_chunks = (total_count + chunk_size - 1) // chunk_size

        self.logger.info(
            "Starting external sort chunk creation",
            extra={
                "total_chunks": total_chunks,
                "chunk_size": chunk_size,
                "column_name": column_name,
                "processing_mode": "external_sort",
            },
        )

        # Add sub-substep for chunk creation progress tracking
        if self.progress_manager:
            try:
                self.progress_manager.add_substep(
                    "extract_unique", "create_chunks", f"Creating {total_chunks} sorted chunks", total=total_chunks
                )
                self.progress_manager.start_substep("extract_unique", "create_chunks")
            except Exception as e:
                self.logger.warning("Failed to set up chunk creation progress", extra={"error": str(e)})

        for chunk_idx in range(total_chunks):
            chunk_start = chunk_idx * chunk_size

            try:
                # Process chunk in memory
                chunk_df = (
                    ldf_data.slice(chunk_start, chunk_size)
                    .select(column_name)
                    .unique()
                    .sort(column_name)
                    .collect()
                )

                if len(chunk_df) == 0:
                    # Update progress even for empty chunks
                    if self.progress_manager:
                        try:
                            self.progress_manager.update_substep("extract_unique", "create_chunks", chunk_idx + 1)
                        except Exception as e:
                            self.logger.warning("Progress update failed for empty chunk", extra={"error": str(e)})
                    continue

                # Write sorted chunk to temporary file
                chunk_file = os.path.join(
                    self.temp_dir, f"ngram_chunk_{chunk_idx}.parquet"
                )
                chunk_df.write_parquet(chunk_file, compression="snappy")
                chunk_files.append(chunk_file)
                self.temp_files.append(chunk_file)

                # Update progress after successful chunk creation
                if self.progress_manager:
                    try:
                        self.progress_manager.update_substep("extract_unique", "create_chunks", chunk_idx + 1)
                    except Exception as e:
                        self.logger.warning("Progress update failed for chunk creation", extra={"error": str(e)})

                # Force cleanup after each chunk
                del chunk_df
                self.memory_manager.enhanced_gc_cleanup()

            except Exception as e:
                self.logger.warning(
                    "Failed to process external sort chunk",
                    extra={
                        "chunk_index": chunk_idx,
                        "chunk_start": chunk_start,
                        "chunk_size": chunk_size,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
                # Update progress even for failed chunks to show we attempted them
                if self.progress_manager:
                    try:
                        self.progress_manager.update_substep("extract_unique", "create_chunks", chunk_idx + 1)
                    except Exception as e:
                        self.logger.warning("Progress update failed for failed chunk", extra={"error": str(e)})
                continue

        # Complete chunk creation substep
        if self.progress_manager:
            try:
                self.progress_manager.complete_substep("extract_unique", "create_chunks")
            except Exception as e:
                self.logger.warning("Failed to complete chunk creation progress", extra={"error": str(e)})

        return chunk_files

    def _merge_sorted_chunks(
        self, chunk_files: List[str], column_name: str
    ) -> pl.DataFrame:
        """Merge sorted chunks using k-way merge algorithm."""
        if not chunk_files:
            return pl.DataFrame({column_name: []})

        if len(chunk_files) == 1:
            return pl.read_parquet(chunk_files[0])

        self.logger.info(
            "Starting k-way merge of sorted chunks",
            extra={
                "chunk_file_count": len(chunk_files),
                "merge_algorithm": "k_way_heap_merge",
            },
        )

        # Add sub-substep for merge progress tracking
        if self.progress_manager:
            try:
                self.progress_manager.add_substep(
                    "extract_unique", "merge_chunks", f"Merging {len(chunk_files)} sorted chunks", total=len(chunk_files)
                )
                self.progress_manager.start_substep("extract_unique", "merge_chunks")
            except Exception as e:
                self.logger.warning("Failed to set up merge progress", extra={"error": str(e)})

        # Use k-way merge with priority queue for efficiency
        heap = []
        chunk_iterators = []
        active_chunks = 0

        # Open all chunk files and initialize heap
        for i, chunk_file in enumerate(chunk_files):
            try:
                chunk_data = pl.read_parquet(chunk_file)

                if len(chunk_data) > 0:
                    chunk_iter = iter(chunk_data[column_name].to_list())
                    try:
                        first_value = next(chunk_iter)
                        heapq.heappush(heap, (first_value, i, chunk_iter))
                        chunk_iterators.append(chunk_iter)
                        active_chunks += 1
                    except StopIteration:
                        continue

            except Exception as e:
                self.logger.warning(
                    "Failed to read chunk file during merge",
                    extra={
                        "chunk_file": chunk_file,
                        "chunk_index": i,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
                continue

        # Perform k-way merge
        result_values = []
        last_value = None
        processed_items = 0
        update_interval = max(1, active_chunks // 20)  # Update progress ~20 times during merge

        while heap:
            current_value, chunk_idx, chunk_iter = heapq.heappop(heap)

            # Skip duplicates
            if current_value != last_value:
                result_values.append(current_value)
                last_value = current_value

            # Update progress periodically during merge operation
            processed_items += 1
            if processed_items % update_interval == 0 and self.progress_manager:
                try:
                    # Progress is based on the conceptual progress through the merge
                    # We use processed_items as a proxy, but cap it at the total chunks
                    progress_value = min(processed_items // update_interval, len(chunk_files))
                    self.progress_manager.update_substep("extract_unique", "merge_chunks", progress_value)
                except Exception as e:
                    self.logger.warning("Progress update failed during merge", extra={"error": str(e)})

            # Get next value from this chunk
            try:
                next_value = next(chunk_iter)
                heapq.heappush(heap, (next_value, chunk_idx, chunk_iter))
            except StopIteration:
                # This chunk is exhausted - update progress to show one chunk completed
                active_chunks -= 1
                if self.progress_manager:
                    try:
                        completed_chunks = len(chunk_files) - active_chunks
                        self.progress_manager.update_substep("extract_unique", "merge_chunks", completed_chunks)
                    except Exception as e:
                        self.logger.warning("Progress update failed for completed chunk", extra={"error": str(e)})
                continue

        # Complete merge substep
        if self.progress_manager:
            try:
                self.progress_manager.complete_substep("extract_unique", "merge_chunks")
            except Exception as e:
                self.logger.warning("Failed to complete merge progress", extra={"error": str(e)})

        return pl.DataFrame({column_name: result_values})

    def _cleanup_temp_files(self):
        """Clean up all temporary files."""
        for temp_file in self.temp_files:
            try:
                os.unlink(temp_file)
            except OSError as e:
                self.logger.warning(
                    "Failed to delete temporary file",
                    extra={
                        "temp_file": temp_file,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
        self.temp_files.clear()


def extract_unique_external_sort(
    ldf_data: pl.LazyFrame,
    memory_manager: MemoryManager,
    progress_manager,
    column_name: str = "ngram_text",
) -> pl.DataFrame:
    """
    Convenience function to perform external sort unique extraction.

    This is the primary interface for using external sorting when
    memory pressure becomes critical. Integrates with hierarchical progress structure.
    """
    extractor = ExternalSortUniqueExtractor(memory_manager, progress_manager=progress_manager)

    try:
        return extractor.extract_unique(ldf_data, column_name)
    except Exception as e:
        # Use hierarchical progress structure - external sort happens within extract_unique substep
        if progress_manager:
            try:
                progress_manager.fail_substep(
                    "process_ngrams", "extract_unique", f"External sort failed: {str(e)}"
                )
            except Exception as progress_error:
                # Log but don't let progress failure mask the original error
                logger = get_logger(f"{__name__}.extract_unique_external_sort")
                logger.warning("Failed to update progress on error", extra={"error": str(progress_error)})
        raise
