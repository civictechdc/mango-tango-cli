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

    def __init__(self, memory_manager: MemoryManager, temp_dir: Optional[str] = None):
        self.memory_manager = memory_manager
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.temp_files = []
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
                    continue

                # Write sorted chunk to temporary file
                chunk_file = os.path.join(
                    self.temp_dir, f"ngram_chunk_{chunk_idx}.parquet"
                )
                chunk_df.write_parquet(chunk_file, compression="snappy")
                chunk_files.append(chunk_file)
                self.temp_files.append(chunk_file)

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
                continue

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

        # Use k-way merge with priority queue for efficiency
        heap = []
        chunk_iterators = []

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

        while heap:
            current_value, chunk_idx, chunk_iter = heapq.heappop(heap)

            # Skip duplicates
            if current_value != last_value:
                result_values.append(current_value)
                last_value = current_value

            # Get next value from this chunk
            try:
                next_value = next(chunk_iter)
                heapq.heappush(heap, (next_value, chunk_idx, chunk_iter))
            except StopIteration:
                continue

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
    memory pressure becomes critical.
    """
    extractor = ExternalSortUniqueExtractor(memory_manager)

    try:
        return extractor.extract_unique(ldf_data, column_name)
    except Exception as e:
        progress_manager.fail_step("extract_unique", f"External sort failed: {str(e)}")
        raise
