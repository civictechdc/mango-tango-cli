"""
Disk-based fallback processing strategies for n-gram generation.

These functions provide alternative processing approaches when memory pressure
becomes critical, trading some performance for guaranteed memory bounds.
"""

import gc
import os
import tempfile
from typing import Callable, Optional

import polars as pl

from analyzers.ngrams.ngrams_base.interface import COL_MESSAGE_SURROGATE_ID
from app.logger import get_logger
from app.utils import MemoryManager

# Initialize module-level logger
logger = get_logger(__name__)


def generate_ngrams_disk_based(
    ldf: pl.LazyFrame,
    min_n: int,
    max_n: int,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    memory_manager: Optional[MemoryManager] = None,
) -> pl.LazyFrame:
    """
    Generate n-grams using disk-based approach for critical memory pressure.

    This approach processes data in very small chunks and uses temporary files
    to store intermediate results, allowing processing of arbitrarily large datasets.
    """

    if memory_manager is None:
        memory_manager = MemoryManager()

    # Use extremely small chunks for critical memory conditions
    chunk_size = memory_manager.calculate_adaptive_chunk_size(5000, "ngram_generation")

    total_rows = ldf.select(pl.len()).collect().item()
    total_chunks = (total_rows + chunk_size - 1) // chunk_size

    logger.info(
        "Starting disk-based n-gram generation",
        extra={
            "total_chunks": total_chunks,
            "chunk_size": chunk_size,
            "min_n": min_n,
            "max_n": max_n,
            "processing_mode": "disk_based",
        },
    )

    # Create temporary directory for intermediate results
    temp_dir = tempfile.mkdtemp(prefix="ngram_disk_")
    temp_files = []

    try:
        # Process each chunk and write results to disk
        for chunk_idx in range(total_chunks):
            chunk_start = chunk_idx * chunk_size

            # Process small chunk in memory
            chunk_ldf = ldf.slice(chunk_start, chunk_size)

            # Generate n-grams for this chunk using memory-efficient method
            chunk_ngrams = _generate_ngrams_minimal_memory(chunk_ldf, min_n, max_n)

            # Write chunk results to temporary file
            temp_file = os.path.join(temp_dir, f"ngrams_chunk_{chunk_idx}.parquet")
            chunk_ngrams.collect().write_parquet(temp_file, compression="snappy")
            temp_files.append(temp_file)

            # Immediate cleanup
            del chunk_ngrams
            memory_manager.enhanced_gc_cleanup()

            # Report progress
            if progress_callback:
                progress_callback(chunk_idx + 1, total_chunks)

        # Combine all temporary files using streaming
        if not temp_files:
            return (
                ldf.select([COL_MESSAGE_SURROGATE_ID])
                .limit(0)
                .with_columns([pl.lit("").alias("ngram_text")])
            )

        # Stream all temp files together and collect immediately
        # to avoid file cleanup race condition
        chunk_lazyframes = [pl.scan_parquet(f) for f in temp_files]
        result_ldf = pl.concat(chunk_lazyframes)
        
        # Collect the result before cleanup to avoid file access issues
        result_df = result_ldf.collect()
        
        return result_df.lazy()  # Return as LazyFrame for consistency

    finally:
        # Always cleanup temporary files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except OSError as e:
                logger.warning(
                    "Failed to delete temporary file",
                    extra={
                        "temp_file": temp_file,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
        try:
            os.rmdir(temp_dir)
        except OSError as e:
            logger.warning(
                "Failed to delete temporary directory",
                extra={
                    "temp_dir": temp_dir,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )


def _generate_ngrams_minimal_memory(
    ldf: pl.LazyFrame, min_n: int, max_n: int
) -> pl.LazyFrame:
    """
    Generate n-grams with minimal memory usage - processes one n-gram length at a time.
    """
    all_results = []

    for n in range(min_n, max_n + 1):
        # Process only one n-gram length at a time to minimize memory
        ngram_expr = (
            pl.col("tokens")
            .map_elements(
                lambda tokens: [
                    " ".join(tokens[i : i + n])
                    for i in range(len(tokens) - n + 1)
                    if len(tokens) >= n
                ],
                return_dtype=pl.List(pl.Utf8),
            )
            .alias("ngrams")
        )

        # Process and immediately collect to control memory
        result = (
            ldf.with_columns([ngram_expr])
            .select([COL_MESSAGE_SURROGATE_ID, "ngrams"])
            .explode("ngrams")
            .filter(
                pl.col("ngrams").is_not_null() & (pl.col("ngrams").str.len_chars() > 0)
            )
            .select([COL_MESSAGE_SURROGATE_ID, pl.col("ngrams").alias("ngram_text")])
        )

        all_results.append(result)

        # Force cleanup between n-gram lengths
        gc.collect()

    # Combine results
    if len(all_results) == 1:
        return all_results[0]
    else:
        return pl.concat(all_results)


def stream_unique_memory_optimized(
    ldf_data: pl.LazyFrame,
    memory_manager: MemoryManager,
    progress_manager,
    column_name: str = "ngram_text",
) -> pl.DataFrame:
    """
    Enhanced streaming unique extraction with smaller chunks for high memory pressure.

    This is an intermediate fallback between normal processing and external sorting.
    """

    # Use smaller chunks than normal streaming
    chunk_size = memory_manager.calculate_adaptive_chunk_size(
        25000, "unique_extraction"
    )

    logger.info(
        "Starting memory-optimized streaming",
        extra={
            "chunk_size": chunk_size,
            "column_name": column_name,
            "processing_mode": "memory_optimized_streaming",
        },
    )

    # Get total count for chunking
    total_count = ldf_data.select(pl.len()).collect().item()
    total_chunks = (total_count + chunk_size - 1) // chunk_size

    # Use temporary files for intermediate storage
    temp_files = []

    try:
        # Process each chunk and stream unique values to separate temp files
        for chunk_idx in range(total_chunks):
            chunk_start = chunk_idx * chunk_size

            # Update progress before processing chunk
            try:
                progress_manager.update_step("extract_unique", chunk_idx)
            except Exception as e:
                logger.warning(
                    "Progress update failed for streaming chunk",
                    extra={
                        "chunk_index": chunk_idx + 1,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )

            # Create temporary file for this chunk's unique values
            with tempfile.NamedTemporaryFile(
                mode="w+", suffix=".csv", delete=False
            ) as temp_file:
                temp_path = temp_file.name
                temp_files.append(temp_path)

            try:
                # Stream unique values for this chunk to temporary file
                (
                    ldf_data.slice(chunk_start, chunk_size)
                    .select(column_name)
                    .unique()
                    .sink_csv(temp_path, include_header=False)
                )

                # Force cleanup after each chunk
                memory_manager.enhanced_gc_cleanup()

            except Exception as e:
                logger.warning(
                    "Failed to process streaming chunk",
                    extra={
                        "chunk_index": chunk_idx + 1,
                        "chunk_start": chunk_start,
                        "chunk_size": chunk_size,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
                # Remove failed temp file from list
                temp_files.remove(temp_path)
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
                continue

        if not temp_files:
            # If no chunks were processed successfully, return empty DataFrame
            return pl.DataFrame({column_name: []})

        # Combine all temporary files using polars streaming operations
        chunk_lazy_frames = []
        for temp_path in temp_files:
            try:
                # Read each temp file as a lazy frame
                chunk_ldf = pl.scan_csv(
                    temp_path, has_header=False, new_columns=[column_name]
                )
                chunk_lazy_frames.append(chunk_ldf)
            except Exception as e:
                logger.warning(
                    "Failed to read temporary file",
                    extra={
                        "temp_path": temp_path,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
                continue

        if not chunk_lazy_frames:
            return pl.DataFrame({column_name: []})

        # Concatenate all chunks and extract final unique values using streaming
        final_temp_file = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w+", suffix=".csv", delete=False
            ) as temp_file:
                final_temp_file = temp_file.name

            # Stream the final unique operation across all chunks
            (
                pl.concat(chunk_lazy_frames)
                .unique()
                .sink_csv(final_temp_file, include_header=False)
            )

            # Read back the final result
            result = pl.read_csv(
                final_temp_file, has_header=False, new_columns=[column_name]
            )

            return result

        finally:
            # Clean up final temp file
            if final_temp_file:
                try:
                    os.unlink(final_temp_file)
                except OSError:
                    pass

    finally:
        # Always clean up all temporary files
        for temp_path in temp_files:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
