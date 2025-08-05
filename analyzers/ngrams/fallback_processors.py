"""
Disk-based fallback processing strategies for n-gram generation.

These functions provide alternative processing approaches when memory pressure
becomes critical, trading some performance for guaranteed memory bounds.
"""

import gc
import os
import tempfile
from typing import Optional

import polars as pl

from analyzers.ngrams.ngrams_base.interface import COL_MESSAGE_SURROGATE_ID
from app.logger import get_logger
from terminal_tools.progress import RichProgressManager
from app.utils import MemoryManager, MemoryPressureLevel

# Initialize module-level logger
logger = get_logger(__name__)


def generate_ngrams_disk_based(
    ldf: pl.LazyFrame,
    min_n: int,
    max_n: int,
    estimated_rows: int,
    memory_manager: Optional[MemoryManager] = None,
    progress_manager: Optional[RichProgressManager] = None,
) -> pl.LazyFrame:
    """
    Generate n-grams using disk-based approach for critical memory pressure.

    This approach processes data in very small chunks and uses temporary files
    to store intermediate results, allowing processing of arbitrarily large datasets.

    Args:
        ldf: LazyFrame with tokenized data
        min_n: Minimum n-gram length
        max_n: Maximum n-gram length
        estimated_rows: Pre-calculated row count to avoid memory-intensive counting
        memory_manager: Optional memory manager for optimization
        progress_manager: Optional progress manager for detailed chunk progress reporting
    """

    if memory_manager is None:
        memory_manager = MemoryManager()

    # Use extremely small chunks for critical memory conditions
    chunk_size = memory_manager.calculate_adaptive_chunk_size(25000, "ngram_generation")

    total_rows = estimated_rows
    total_chunks = (total_rows + chunk_size - 1) // chunk_size

    # Integrate with existing ngrams step as a sub-step instead of creating new step
    if progress_manager:
        progress_manager.add_substep(
            "ngrams", "disk_generation", "Processing data chunks", total_chunks
        )
        progress_manager.start_substep("ngrams", "disk_generation")

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
    import time

    try:
        # Process each chunk and write results to disk
        for chunk_idx in range(total_chunks):
            chunk_start = chunk_idx * chunk_size

            # Process small chunk in memory
            chunk_ldf = ldf.slice(chunk_start, chunk_size)

            # Generate n-grams for this chunk using memory-efficient method
            ngram_start = time.time()
            chunk_ngrams = _generate_ngrams_minimal_memory(chunk_ldf, min_n, max_n)
            ngram_end = time.time()
            logger.debug(
                "N-gram generation finished on chunk",
                extra={"elapsed_time": f"{ngram_end - ngram_start:.2f} seconds"},
            )

            # Write chunk results to temporary file
            temp_file = os.path.join(temp_dir, f"ngrams_chunk_{chunk_idx}.parquet")
            write_start = time.time()
            # chunk_ngrams.collect().write_parquet(temp_file, compression="snappy")
            chunk_ngrams.sink_parquet(temp_file)
            write_end = time.time()
            elapsed_time = f"{write_end - write_start:.2f} seconds"
            logger.debug("N-gram chunk written", extra={"elapsed_time": elapsed_time})

            temp_files.append(temp_file)

            # Immediate cleanup
            del chunk_ngrams

            # Only perform expensive cleanup if memory pressure is high
            if memory_manager.get_memory_pressure_level() in [
                MemoryPressureLevel.HIGH,
                MemoryPressureLevel.CRITICAL,
            ]:
                memory_manager.enhanced_gc_cleanup()
            else:
                gc.collect()  # Lightweight cleanup

            # Update progress with current chunk
            if progress_manager:
                try:
                    progress_manager.update_substep(
                        "ngrams", "disk_generation", chunk_idx + 1
                    )
                    completion_percentage = round(
                        ((chunk_idx + 1) / total_chunks) * 100, 2
                    )

                    logger.info(
                        "N-gram generation chunk progress",
                        extra={
                            "chunk_index": chunk_idx + 1,
                            "total_chunks": total_chunks,
                            "completion_percentage": completion_percentage,
                            "processing_mode": "disk_based",
                        },
                    )
                except Exception as e:
                    logger.warning(
                        "Progress update failed during disk-based processing - continuing",
                        extra={
                            "chunk_index": chunk_idx + 1,
                            "total_chunks": total_chunks,
                            "error": str(e),
                            "error_type": type(e).__name__,
                        },
                    )

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

        # Complete progress sub-step on success
        if progress_manager:
            progress_manager.complete_substep("ngrams", "disk_generation")

        return result_df.lazy()  # Return as LazyFrame for consistency

    except Exception as e:
        # Fail progress sub-step on error
        if progress_manager:
            progress_manager.fail_substep(
                "ngrams", "disk_generation", f"Disk-based generation failed: {str(e)}"
            )
        raise
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
    progress_manager: Optional[RichProgressManager],
    column_name: str = "ngram_text",
) -> pl.DataFrame:
    """
    Enhanced streaming unique extraction with smaller chunks for high memory pressure.

    This is an intermediate fallback between normal processing and external sorting.
    Integrates with the hierarchical progress structure by using the existing extract_unique sub-step.
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

    # Get total count for chunking - use estimated count if available in memory manager context
    # For now, we still need to get the count, but this should be optimized in future versions
    total_count = ldf_data.select(pl.len()).collect().item()
    total_chunks = (total_count + chunk_size - 1) // chunk_size

    # Use temporary files for intermediate storage
    temp_files = []

    try:
        # Process each chunk and stream unique values to separate temp files
        for chunk_idx in range(total_chunks):
            chunk_start = chunk_idx * chunk_size

            # Update progress before processing chunk - integrate with hierarchical structure
            try:
                # Use the hierarchical substep update for extract_unique
                progress_manager.update_substep(
                    "process_ngrams", "extract_unique", chunk_idx
                )
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

                # Only perform expensive cleanup if memory pressure is high
                if memory_manager.get_memory_pressure_level() in [
                    MemoryPressureLevel.HIGH,
                    MemoryPressureLevel.CRITICAL,
                ]:
                    memory_manager.enhanced_gc_cleanup()
                else:
                    gc.collect()  # Lightweight cleanup

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
