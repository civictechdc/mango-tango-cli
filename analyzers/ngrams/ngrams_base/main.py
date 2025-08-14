import gc
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

import polars as pl

from analyzer_interface.context import PrimaryAnalyzerContext
from app.logger import get_logger

# from app.memory_aware_progress import MemoryAwareProgressManager  # Not needed for standard display
from app.utils import MemoryManager, MemoryPressureLevel, tokenize_text
from terminal_tools.progress import ProgressManager

# Initialize module-level logger
logger = get_logger(__name__)

from .interface import (
    COL_AUTHOR_ID,
    COL_MESSAGE_ID,
    COL_MESSAGE_NGRAM_COUNT,
    COL_MESSAGE_SURROGATE_ID,
    COL_MESSAGE_TEXT,
    COL_MESSAGE_TIMESTAMP,
    COL_NGRAM_ID,
    COL_NGRAM_LENGTH,
    COL_NGRAM_WORDS,
    OUTPUT_MESSAGE,
    OUTPUT_MESSAGE_NGRAMS,
    OUTPUT_NGRAM_DEFS,
    PARAM_MAX_N,
    PARAM_MIN_N,
)


def _stream_unique_to_temp_file(
    ldf_chunk: pl.LazyFrame, column_name: str = "ngram_text"
) -> pl.DataFrame:
    """
    Stream unique values from a LazyFrame chunk to a temporary file and read back as DataFrame.

    This helper function reduces memory usage by avoiding large in-memory collections
    during unique value extraction.

    Args:
        ldf_chunk: LazyFrame chunk to process
        column_name: Name of the column to extract unique values from

    Returns:
        DataFrame containing unique values

    Raises:
        Exception: If streaming operation fails
    """
    with tempfile.NamedTemporaryFile(
        mode="w+", suffix=".csv", delete=False
    ) as temp_file:
        temp_path = temp_file.name

    try:
        # Stream unique operation to temporary file
        (
            ldf_chunk.select(column_name)
            .unique()
            .sink_csv(temp_path, include_header=False)
        )

        # Read back as DataFrame
        result = pl.read_csv(temp_path, has_header=False, new_columns=[column_name])

        return result

    finally:
        # Always clean up temporary file
        try:
            os.unlink(temp_path)
        except OSError:
            pass


def _stream_unique_batch_accumulator(
    ldf_data: pl.LazyFrame,
    chunk_size: int = 150_000,
    column_name: str = "ngram_text",
    progress_manager=None,
) -> pl.DataFrame:
    """
    Memory-efficient streaming unique extraction using batch accumulation with temporary files.

    This function processes large datasets in chunks, streaming each chunk's unique values
    to disk and accumulating results using polars operations instead of Python loops.

    Enhanced with chunked progress tracking that provides real-time feedback during
    chunk processing, integrating with the hierarchical progress reporting system.

    Args:
        ldf_data: LazyFrame containing the data to process
        chunk_size: Size of each processing chunk (default: 50,000)
        column_name: Name of the column to extract unique values from
        progress_manager: Optional progress manager for detailed batch progress reporting.
                         Adds 'stream_batches' substep to 'process_ngrams' with chunk-level updates.

    Returns:
        DataFrame containing all unique values across chunks

    Raises:
        Exception: If streaming operations fail
    """
    # Get total count for chunking
    total_count = ldf_data.select(pl.len()).collect().item()
    total_chunks = (total_count + chunk_size - 1) // chunk_size

    logger.debug(
        "Stream unique batch accumulator initialized",
        extra={
            "total_count": total_count,
            "chunk_size": chunk_size,
            "total_chunks": total_chunks,
            "column_name": column_name,
            "chunking_efficiency": (
                total_count / chunk_size if chunk_size > 0 else "N/A"
            ),
        },
    )

    # Set up hierarchical progress tracking for batch processing
    if progress_manager:
        # Add substep for batch processing within the current context
        progress_manager.add_substep(
            "process_ngrams", "stream_batches", "Processing data batches", total_chunks
        )
        progress_manager.start_substep("process_ngrams", "stream_batches")

    # Use temporary files for intermediate storage of unique values
    temp_files = []

    try:
        # Process each chunk and stream unique values to separate temp files
        for chunk_idx in range(total_chunks):
            chunk_start = chunk_idx * chunk_size

            logger.debug(
                "Processing batch accumulator chunk",
                extra={
                    "chunk_index": chunk_idx + 1,
                    "total_chunks": total_chunks,
                    "chunk_start": chunk_start,
                    "chunk_size": chunk_size,
                    "progress_percent": round((chunk_idx / total_chunks) * 100, 1),
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

                # Update progress after successful chunk processing
                if progress_manager:
                    try:
                        progress_manager.update_substep(
                            "process_ngrams", "stream_batches", chunk_idx + 1
                        )
                    except Exception as progress_error:
                        logger.warning(
                            "Progress update failed during batch processing",
                            extra={
                                "chunk_index": chunk_idx + 1,
                                "total_chunks": total_chunks,
                                "error": str(progress_error),
                                "error_type": type(progress_error).__name__,
                            },
                        )

            except Exception as e:
                logger.warning(
                    "Failed to process chunk during unique extraction",
                    extra={
                        "chunk_index": chunk_idx + 1,
                        "total_chunks": total_chunks,
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

        # Processing complete - progress will be completed after successful result

        if not temp_files:
            # If no chunks were processed successfully, complete progress and return empty DataFrame
            if progress_manager:
                progress_manager.complete_substep("process_ngrams", "stream_batches")
            return pl.DataFrame({column_name: []})

        # Combine all temporary files using polars streaming operations
        # Read all temp files as lazy frames and concatenate
        chunk_lazy_frames = []

        logger.debug(
            "Starting temporary file combination phase",
            extra={
                "temp_files_count": len(temp_files),
                "temp_files_successfully_processed": len(
                    [f for f in temp_files if os.path.exists(f)]
                ),
                "combination_method": "polars_streaming",
            },
        )

        for temp_path in temp_files:
            try:
                # Read each temp file as a lazy frame
                chunk_ldf = pl.scan_csv(
                    temp_path, has_header=False, new_columns=[column_name]
                )
                chunk_lazy_frames.append(chunk_ldf)
            except Exception as e:
                logger.warning(
                    "Failed to read temporary file during unique extraction",
                    extra={
                        "temp_file_path": temp_path,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
                continue

        if not chunk_lazy_frames:
            # Complete progress and return empty DataFrame if no valid chunks
            if progress_manager:
                progress_manager.complete_substep("process_ngrams", "stream_batches")
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

            # Complete progress step on success
            if progress_manager:
                progress_manager.complete_substep("process_ngrams", "stream_batches")

            return result

        finally:
            # Clean up final temp file
            if final_temp_file:
                try:
                    os.unlink(final_temp_file)
                except OSError:
                    pass

    except Exception as e:
        # Fail progress step on error
        if progress_manager:
            progress_manager.fail_substep(
                "process_ngrams",
                "stream_batches",
                f"Streaming unique extraction failed: {str(e)}",
            )
        raise
    finally:
        # Always clean up all temporary files
        for temp_path in temp_files:
            try:
                os.unlink(temp_path)
            except OSError:
                pass


def _safe_streaming_write(lazy_frame, output_path, operation_name, progress_manager):
    """
    Attempt streaming write with fallback to collect() if streaming fails.
    This is the legacy single-step write function for backward compatibility.

    Args:
        lazy_frame: polars LazyFrame to write
        output_path: Path to write the parquet file
        operation_name: Name of the operation for progress reporting
        progress_manager: Progress manager for status updates

    Raises:
        Exception: If both streaming and fallback methods fail
    """
    logger.debug(
        "Attempting streaming write operation",
        extra={
            "operation": operation_name,
            "output_path": str(output_path),
            "write_method": "streaming_sink_parquet",
            "maintain_order": True,
        },
    )

    try:
        # Primary: Use streaming sink_parquet
        lazy_frame.sink_parquet(output_path, maintain_order=True)
        progress_manager.complete_step(operation_name)

        logger.debug(
            "Streaming write completed successfully",
            extra={
                "operation": operation_name,
                "output_path": str(output_path),
                "write_method": "streaming_sink_parquet",
            },
        )
    except Exception as streaming_error:
        logger.warning(
            "Streaming write failed, falling back to collect() method",
            extra={
                "operation": operation_name,
                "output_path": str(output_path),
                "streaming_error": str(streaming_error),
                "error_type": type(streaming_error).__name__,
            },
        )
        progress_manager.update_step(
            operation_name,
            f"Streaming failed, falling back to collect(): {str(streaming_error)}",
        )
        try:
            # Fallback: Traditional collect + write
            logger.debug(
                "Using fallback collect() write method",
                extra={
                    "operation": operation_name,
                    "output_path": str(output_path),
                    "write_method": "collect_write_parquet",
                },
            )
            lazy_frame.collect().write_parquet(output_path)
            progress_manager.complete_step(operation_name)

            logger.debug(
                "Fallback write completed successfully",
                extra={
                    "operation": operation_name,
                    "output_path": str(output_path),
                    "write_method": "collect_write_parquet",
                },
            )
        except Exception as fallback_error:
            logger.error(
                "Both streaming and fallback write methods failed",
                extra={
                    "operation": operation_name,
                    "output_path": str(output_path),
                    "streaming_error": str(streaming_error),
                    "fallback_error": str(fallback_error),
                    "fallback_error_type": type(fallback_error).__name__,
                },
                exc_info=True,
            )
            progress_manager.fail_step(
                operation_name,
                f"Both streaming and fallback failed: {str(fallback_error)}",
            )
            raise fallback_error


def _enhanced_write_message_ngrams(ldf_with_ids, output_path, progress_manager):
    """
    Enhanced message n-grams write operation with sub-step progress reporting.

    Breaks down the write operation into observable sub-steps:
    1. Grouping n-grams by message
    2. Aggregating n-gram counts
    3. Sorting grouped data
    4. Writing to parquet file

    Args:
        ldf_with_ids: LazyFrame with n-gram IDs assigned
        output_path: Path to write the parquet file
        progress_manager: Progress manager for status updates
    """
    step_id = "write_message_ngrams"

    # Use operation counts for sub-steps instead of row counts
    # Each sub-step is a single logical operation, so use 1 as total
    try:
        # Add sub-steps for this write operation with operation counts
        progress_manager.add_substep(step_id, "group", "Grouping n-grams by message", 1)
        progress_manager.add_substep(
            step_id, "aggregate", "Aggregating n-gram counts", 1
        )
        progress_manager.add_substep(step_id, "sort", "Sorting grouped data", 1)
        progress_manager.add_substep(step_id, "write", "Writing to parquet file", 1)
    except Exception:
        # Fallback to no totals if something fails
        progress_manager.add_substep(step_id, "group", "Grouping n-grams by message")
        progress_manager.add_substep(step_id, "aggregate", "Aggregating n-gram counts")
        progress_manager.add_substep(step_id, "sort", "Sorting grouped data")
        progress_manager.add_substep(step_id, "write", "Writing to parquet file")

    logger.debug(
        "Starting enhanced message n-grams write operation",
        extra={
            "operation": "write_message_ngrams",
            "output_path": str(output_path),
            "sub_steps": ["group", "aggregate", "sort", "write"],
        },
    )

    try:
        # Sub-step 1: Grouping n-grams by message
        progress_manager.start_substep(step_id, "group")
        try:
            # Apply group_by operation
            grouped_ldf = ldf_with_ids.group_by(
                [COL_MESSAGE_SURROGATE_ID, COL_NGRAM_ID]
            )
            # Update progress with completion (binary progress: operation complete)
            if hasattr(progress_manager, "update_substep"):
                try:
                    # Use 1 as progress to indicate completion (since total is 1)
                    progress_manager.update_substep(step_id, "group", 1)
                except:
                    pass
            progress_manager.complete_substep(step_id, "group")
        except Exception as e:
            progress_manager.fail_substep(
                step_id, "group", f"Grouping failed: {str(e)}"
            )
            raise

        # Sub-step 2: Aggregating n-gram counts
        progress_manager.start_substep(step_id, "aggregate")
        try:
            # Apply aggregation
            aggregated_ldf = grouped_ldf.agg([pl.len().alias(COL_MESSAGE_NGRAM_COUNT)])
            # Update progress with completion (binary progress: operation complete)
            if hasattr(progress_manager, "update_substep"):
                try:
                    # Use 1 as progress to indicate completion (since total is 1)
                    progress_manager.update_substep(step_id, "aggregate", 1)
                except:
                    pass
            progress_manager.complete_substep(step_id, "aggregate")
        except Exception as e:
            progress_manager.fail_substep(
                step_id, "aggregate", f"Aggregation failed: {str(e)}"
            )
            raise

        # Sub-step 3: Sorting grouped data
        progress_manager.start_substep(step_id, "sort")
        try:
            # Apply sorting
            sorted_ldf = aggregated_ldf.sort([COL_MESSAGE_SURROGATE_ID, COL_NGRAM_ID])
            # Update progress with completion (binary progress: operation complete)
            if hasattr(progress_manager, "update_substep"):
                try:
                    # Use 1 as progress to indicate completion (since total is 1)
                    progress_manager.update_substep(step_id, "sort", 1)
                except:
                    pass
            progress_manager.complete_substep(step_id, "sort")
        except Exception as e:
            progress_manager.fail_substep(step_id, "sort", f"Sorting failed: {str(e)}")
            raise

        # Sub-step 4: Writing to parquet file
        progress_manager.start_substep(step_id, "write")
        try:
            # Attempt streaming write with fallback
            try:
                sorted_ldf.sink_parquet(output_path, maintain_order=True)
            except Exception as streaming_error:
                logger.warning(
                    "Streaming write failed for message n-grams, using fallback",
                    extra={
                        "output_path": str(output_path),
                        "error": str(streaming_error),
                        "error_type": type(streaming_error).__name__,
                    },
                )
                # Fallback to collect + write
                sorted_ldf.collect().write_parquet(output_path)
            # Update progress with completion (binary progress: operation complete)
            if hasattr(progress_manager, "update_substep"):
                try:
                    # Use 1 as progress to indicate completion (since total is 1)
                    progress_manager.update_substep(step_id, "write", 1)
                except:
                    pass
            progress_manager.complete_substep(step_id, "write")
        except Exception as e:
            progress_manager.fail_substep(
                step_id, "write", f"Write operation failed: {str(e)}"
            )
            raise
        logger.debug(
            "Enhanced message n-grams write operation completed",
            extra={
                "operation": "write_message_ngrams",
                "output_path": str(output_path),
            },
        )

    except Exception as e:
        logger.error(
            "Enhanced message n-grams write operation failed",
            extra={
                "operation": "write_message_ngrams",
                "output_path": str(output_path),
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise


def _enhanced_write_ngram_definitions(unique_ngrams, output_path, progress_manager):
    """
    Enhanced n-gram definitions write operation with sub-step progress reporting.

    Breaks down the write operation into observable sub-steps:
    1. Preparing n-gram metadata
    2. Calculating n-gram lengths
    3. Sorting definitions
    4. Writing definitions to parquet

    Args:
        unique_ngrams: DataFrame with unique n-grams
        output_path: Path to write the parquet file
        progress_manager: Progress manager for status updates
    """
    step_id = "write_ngram_defs"

    # Use operation counts for sub-steps instead of n-gram counts
    # Each sub-step is a single logical operation, so use 1 as total
    try:
        # Add sub-steps for this write operation with operation counts
        progress_manager.add_substep(
            step_id, "metadata", "Preparing n-gram metadata", 1
        )
        progress_manager.add_substep(
            step_id, "lengths", "Calculating n-gram lengths", 1
        )
        progress_manager.add_substep(step_id, "sort", "Sorting definitions", 1)
        progress_manager.add_substep(
            step_id, "write", "Writing definitions to parquet", 1
        )
    except Exception:
        # Fallback to no totals if something fails
        progress_manager.add_substep(step_id, "metadata", "Preparing n-gram metadata")
        progress_manager.add_substep(step_id, "lengths", "Calculating n-gram lengths")
        progress_manager.add_substep(step_id, "sort", "Sorting definitions")
        progress_manager.add_substep(step_id, "write", "Writing definitions to parquet")

    logger.debug(
        "Starting enhanced n-gram definitions write operation",
        extra={
            "operation": "write_ngram_defs",
            "output_path": str(output_path),
            "sub_steps": ["metadata", "lengths", "sort", "write"],
        },
    )

    try:
        # Sub-step 1: Preparing n-gram metadata
        progress_manager.start_substep(step_id, "metadata")
        try:
            # Start with the base LazyFrame and select core columns
            base_ldf = unique_ngrams.lazy().select(
                [
                    COL_NGRAM_ID,
                    pl.col("ngram_text").alias(COL_NGRAM_WORDS),
                ]
            )
            # Update progress with completion (binary progress: operation complete)
            if hasattr(progress_manager, "update_substep"):
                try:
                    # Use 1 as progress to indicate completion (since total is 1)
                    progress_manager.update_substep(step_id, "metadata", 1)
                except:
                    pass
            progress_manager.complete_substep(step_id, "metadata")
        except Exception as e:
            progress_manager.fail_substep(
                step_id, "metadata", f"Metadata preparation failed: {str(e)}"
            )
            raise

        # Sub-step 2: Calculating n-gram lengths
        progress_manager.start_substep(step_id, "lengths")
        try:
            # Add n-gram length calculation
            length_ldf = base_ldf.with_columns(
                [
                    pl.col(COL_NGRAM_WORDS)
                    .str.split(" ")
                    .list.len()
                    .alias(COL_NGRAM_LENGTH)
                ]
            )
            # Update progress with completion (binary progress: operation complete)
            if hasattr(progress_manager, "update_substep"):
                try:
                    # Use 1 as progress to indicate completion (since total is 1)
                    progress_manager.update_substep(step_id, "lengths", 1)
                except:
                    pass
            progress_manager.complete_substep(step_id, "lengths")
        except Exception as e:
            progress_manager.fail_substep(
                step_id, "lengths", f"Length calculation failed: {str(e)}"
            )
            raise

        # Sub-step 3: Sorting definitions
        progress_manager.start_substep(step_id, "sort")
        try:
            # Sort by ngram_id for consistent ordering
            sorted_ldf = length_ldf.sort(COL_NGRAM_ID)
            # Update progress with completion (binary progress: operation complete)
            if hasattr(progress_manager, "update_substep"):
                try:
                    # Use 1 as progress to indicate completion (since total is 1)
                    progress_manager.update_substep(step_id, "sort", 1)
                except:
                    pass
            progress_manager.complete_substep(step_id, "sort")
        except Exception as e:
            progress_manager.fail_substep(step_id, "sort", f"Sorting failed: {str(e)}")
            raise

        # Sub-step 4: Writing definitions to parquet
        progress_manager.start_substep(step_id, "write")
        try:
            # Attempt streaming write with fallback
            try:
                sorted_ldf.sink_parquet(output_path, maintain_order=True)
            except Exception as streaming_error:
                logger.warning(
                    "Streaming write failed for n-gram definitions, using fallback",
                    extra={
                        "output_path": str(output_path),
                        "error": str(streaming_error),
                        "error_type": type(streaming_error).__name__,
                    },
                )
                # Fallback to collect + write
                sorted_ldf.collect().write_parquet(output_path)
            # Update progress with completion (binary progress: operation complete)
            if hasattr(progress_manager, "update_substep"):
                try:
                    # Use 1 as progress to indicate completion (since total is 1)
                    progress_manager.update_substep(step_id, "write", 1)
                except:
                    pass
            progress_manager.complete_substep(step_id, "write")
        except Exception as e:
            progress_manager.fail_substep(
                step_id, "write", f"Write operation failed: {str(e)}"
            )
            raise
        logger.debug(
            "Enhanced n-gram definitions write operation completed",
            extra={"operation": "write_ngram_defs", "output_path": str(output_path)},
        )

    except Exception as e:
        logger.error(
            "Enhanced n-gram definitions write operation failed",
            extra={
                "operation": "write_ngram_defs",
                "output_path": str(output_path),
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise


def _enhanced_write_message_metadata(ldf_tokenized, output_path, progress_manager):
    """
    Enhanced message metadata write operation with sub-step progress reporting.

    Breaks down the write operation into observable sub-steps:
    1. Selecting message columns
    2. Deduplicating messages
    3. Sorting by surrogate ID
    4. Writing metadata to parquet

    Args:
        ldf_tokenized: LazyFrame with tokenized data
        output_path: Path to write the parquet file
        progress_manager: Progress manager for status updates
    """
    step_id = "write_message_metadata"

    # Use operation counts for sub-steps instead of message counts
    # Each sub-step is a single logical operation, so use 1 as total
    try:
        # Add sub-steps for this write operation with operation counts
        progress_manager.add_substep(step_id, "select", "Selecting message columns", 1)
        progress_manager.add_substep(
            step_id, "deduplicate", "Deduplicating messages", 1
        )
        progress_manager.add_substep(step_id, "sort", "Sorting by surrogate ID", 1)
        progress_manager.add_substep(step_id, "write", "Writing metadata to parquet", 1)
    except Exception:
        # Fallback to no totals if something fails
        progress_manager.add_substep(step_id, "select", "Selecting message columns")
        progress_manager.add_substep(step_id, "deduplicate", "Deduplicating messages")
        progress_manager.add_substep(step_id, "sort", "Sorting by surrogate ID")
        progress_manager.add_substep(step_id, "write", "Writing metadata to parquet")

    logger.debug(
        "Starting enhanced message metadata write operation",
        extra={
            "operation": "write_message_metadata",
            "output_path": str(output_path),
            "sub_steps": ["select", "deduplicate", "sort", "write"],
        },
    )

    try:
        # Sub-step 1: Selecting message columns
        progress_manager.start_substep(step_id, "select")
        try:
            # Select the required columns
            selected_ldf = ldf_tokenized.select(
                [
                    COL_MESSAGE_SURROGATE_ID,
                    COL_MESSAGE_ID,
                    COL_MESSAGE_TEXT,
                    COL_AUTHOR_ID,
                    COL_MESSAGE_TIMESTAMP,
                ]
            )
            # Update progress with completion (binary progress: operation complete)
            if hasattr(progress_manager, "update_substep"):
                try:
                    # Use 1 as progress to indicate completion (since total is 1)
                    progress_manager.update_substep(step_id, "select", 1)
                except:
                    pass
            progress_manager.complete_substep(step_id, "select")
        except Exception as e:
            progress_manager.fail_substep(
                step_id, "select", f"Column selection failed: {str(e)}"
            )
            raise

        # Sub-step 2: Deduplicating messages
        progress_manager.start_substep(step_id, "deduplicate")
        try:
            # Apply deduplication by surrogate ID
            deduplicated_ldf = selected_ldf.unique(subset=[COL_MESSAGE_SURROGATE_ID])
            # Update progress with completion (binary progress: operation complete)
            if hasattr(progress_manager, "update_substep"):
                try:
                    # Use 1 as progress to indicate completion (since total is 1)
                    progress_manager.update_substep(step_id, "deduplicate", 1)
                except:
                    pass
            progress_manager.complete_substep(step_id, "deduplicate")
        except Exception as e:
            progress_manager.fail_substep(
                step_id, "deduplicate", f"Deduplication failed: {str(e)}"
            )
            raise

        # Sub-step 3: Sorting by surrogate ID
        progress_manager.start_substep(step_id, "sort")
        try:
            # Sort by surrogate ID for consistent ordering
            sorted_ldf = deduplicated_ldf.sort(COL_MESSAGE_SURROGATE_ID)
            # Update progress with completion (binary progress: operation complete)
            if hasattr(progress_manager, "update_substep"):
                try:
                    # Use 1 as progress to indicate completion (since total is 1)
                    progress_manager.update_substep(step_id, "sort", 1)
                except:
                    pass
            progress_manager.complete_substep(step_id, "sort")
        except Exception as e:
            progress_manager.fail_substep(step_id, "sort", f"Sorting failed: {str(e)}")
            raise

        # Sub-step 4: Writing metadata to parquet
        progress_manager.start_substep(step_id, "write")
        try:
            # Attempt streaming write with fallback
            try:
                sorted_ldf.sink_parquet(output_path, maintain_order=True)
            except Exception as streaming_error:
                logger.warning(
                    "Streaming write failed for message metadata, using fallback",
                    extra={
                        "output_path": str(output_path),
                        "error": str(streaming_error),
                        "error_type": type(streaming_error).__name__,
                    },
                )
                # Fallback to collect + write
                sorted_ldf.collect().write_parquet(output_path)
            # Update progress with completion (binary progress: operation complete)
            if hasattr(progress_manager, "update_substep"):
                try:
                    # Use 1 as progress to indicate completion (since total is 1)
                    progress_manager.update_substep(step_id, "write", 1)
                except:
                    pass
            progress_manager.complete_substep(step_id, "write")
        except Exception as e:
            progress_manager.fail_substep(
                step_id, "write", f"Write operation failed: {str(e)}"
            )
            raise
        logger.debug(
            "Enhanced message metadata write operation completed",
            extra={
                "operation": "write_message_metadata",
                "output_path": str(output_path),
            },
        )

    except Exception as e:
        logger.error(
            "Enhanced message metadata write operation failed",
            extra={
                "operation": "write_message_metadata",
                "output_path": str(output_path),
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise


def main(context: PrimaryAnalyzerContext):
    """
    Enhanced n-gram analyzer with comprehensive memory management.

    New Features:
    - Real-time memory monitoring throughout processing
    - Adaptive chunk sizing based on memory pressure
    - Automatic fallback strategies for high memory pressure
    - Memory-aware progress reporting with pressure warnings
    - Enhanced garbage collection at critical memory points
    """
    input_reader = context.input()

    # Get parameters from context
    min_n = context.params.get(PARAM_MIN_N, 3)
    max_n = context.params.get(PARAM_MAX_N, 5)

    # Log analysis start with key parameters
    logger.info(
        "Starting n-gram analysis",
        extra={
            "input_path": str(context.input().parquet_path),
            "output_path": str(context.output(OUTPUT_MESSAGE_NGRAMS).parquet_path),
            "min_n": min_n,
            "max_n": max_n,
            "analyzer_version": "enhanced_memory_managed",
        },
    )

    # Validate parameters
    assert isinstance(min_n, int) and min_n >= 1, "min_n must be a positive integer"
    assert isinstance(max_n, int) and max_n >= min_n, "max_n must be >= min_n"

    logger.debug(
        "Parameter validation completed",
        extra={
            "min_n": min_n,
            "max_n": max_n,
            "n_gram_range_size": max_n - min_n + 1,
            "validation_status": "passed",
        },
    )

    # Initialize memory manager
    memory_manager = MemoryManager(max_memory_gb=4.0, process_name="ngram_analyzer")

    # Debug: Log initial memory state and configuration
    initial_memory_debug = memory_manager.get_current_memory_usage()
    logger.debug(
        "Memory manager initialized",
        extra={
            "max_memory_gb": memory_manager.max_memory_gb,
            "process_name": "ngram_analyzer",
            "initial_rss_mb": initial_memory_debug["rss_mb"],
            "initial_vms_mb": initial_memory_debug["vms_mb"],
            "available_mb": initial_memory_debug.get("available_mb", "unknown"),
        },
    )

    # Get the raw column names from the project's column mappings
    required_raw_columns = [
        context.input_columns[COL_AUTHOR_ID].user_column_name,
        context.input_columns[COL_MESSAGE_ID].user_column_name,
        context.input_columns[COL_MESSAGE_TEXT].user_column_name,
        context.input_columns[COL_MESSAGE_TIMESTAMP].user_column_name,
    ]

    ldf = pl.scan_parquet(input_reader.parquet_path).select(required_raw_columns)

    # Count total messages for progress tracking
    total_messages = ldf.select(pl.len()).collect().item()

    # Use context-provided progress manager if available, otherwise create local one
    use_context_progress_manager = context.progress_manager is not None
    if use_context_progress_manager:
        progress_manager = context.progress_manager
        # Run analysis without creating a new context manager (already managed by caller)
        _run_ngram_analysis_with_progress_manager(
            progress_manager, context, input_reader, ldf, total_messages, min_n, max_n, memory_manager, logger
        )
    else:
        # Fall back to creating our own progress manager for backward compatibility
        with ProgressManager("N-gram Analysis Progress") as progress_manager:
            _run_ngram_analysis_with_progress_manager(
                progress_manager, context, input_reader, ldf, total_messages, min_n, max_n, memory_manager, logger
            )


def _run_ngram_analysis_with_progress_manager(
    progress_manager, context, input_reader, ldf, total_messages, min_n, max_n, memory_manager, logger
):
    # Memory checkpoint: Initial state
    initial_memory = memory_manager.get_current_memory_usage()
    logger.info(
        "Analysis started with initial memory state",
        extra={
            "initial_memory_mb": initial_memory['rss_mb'],
            "available_memory_mb": initial_memory.get('available_mb', 'unknown')
        }
    )
    logger.debug(
    "Initial memory state captured",
    extra={
        "rss_mb": initial_memory["rss_mb"],
        "vms_mb": initial_memory["vms_mb"],
        "available_mb": initial_memory.get("available_mb", "unknown"),
        "total_messages": total_messages,
    },
    )

    # Add ALL steps upfront for better UX with the enhanced progress system
    progress_manager.add_step(
        "preprocess", "Preprocessing and filtering messages", total_messages
    )

    # Calculate tokenization total based on memory-aware chunking
    initial_chunk_size = 150000
    adaptive_chunk_size = memory_manager.calculate_adaptive_chunk_size(
        initial_chunk_size, "tokenization"
    )
    tokenization_total = None
    if total_messages > adaptive_chunk_size:
        tokenization_total = (
            total_messages + adaptive_chunk_size - 1
        ) // adaptive_chunk_size

    logger.debug(
        "Tokenization chunking strategy calculated",
        extra={
            "initial_chunk_size": initial_chunk_size,
            "adaptive_chunk_size": adaptive_chunk_size,
            "total_messages": total_messages,
            "will_use_chunking": total_messages > adaptive_chunk_size,
            "tokenization_total": tokenization_total,
            "chunk_size_adjustment_factor": adaptive_chunk_size
            / initial_chunk_size,
        },
    )

    progress_manager.add_step(
        "tokenize", "Tokenizing text data", tokenization_total
    )

    # Enhanced n-gram generation step calculation
    n_gram_lengths = list(range(min_n, max_n + 1))
    estimated_rows = total_messages
    base_steps = 2

    # Dynamic chunk sizing based on dataset size and available memory
    def calculate_optimal_chunk_size(dataset_size: int, memory_manager=None) -> int:
        """
        Calculate optimal chunk size based on dataset size and available memory.

        Args:
            dataset_size: Number of rows in dataset
            memory_manager: Optional memory manager for capacity detection

        Returns:
            int: Optimal chunk size for the dataset and system
        """
        import psutil

        # Get memory capacity factor
        if memory_manager:
            total_gb = psutil.virtual_memory().total / 1024**3
            if total_gb >= 32:
                memory_factor = 2.0  # High-memory systems
            elif total_gb >= 16:
                memory_factor = 1.5  # Standard systems
            elif total_gb >= 8:
                memory_factor = 1.0  # Lower-memory systems
            else:
                memory_factor = 0.5  # Very constrained systems
        else:
            memory_factor = 1.0  # Default fallback

        # Base chunk sizes scaled by memory capacity
        if dataset_size <= 500_000:
            base_chunk = int(200_000 * memory_factor)
        elif dataset_size <= 2_000_000:
            base_chunk = int(150_000 * memory_factor)
        elif dataset_size <= 5_000_000:
            base_chunk = int(100_000 * memory_factor)
        else:
            base_chunk = int(75_000 * memory_factor)

        # Ensure reasonable bounds
        return max(10_000, min(base_chunk, 500_000))

    MEMORY_CHUNK_THRESHOLD = calculate_optimal_chunk_size(
        estimated_rows, memory_manager
    )
    use_chunking = (
        estimated_rows is not None and estimated_rows > MEMORY_CHUNK_THRESHOLD
    )

    # Log dynamic chunk sizing decision
    logger.info(
        "Dynamic chunk sizing calculated",
        extra={
            "dataset_size": estimated_rows,
            "calculated_chunk_size": MEMORY_CHUNK_THRESHOLD,
            "will_use_chunking": use_chunking,
        },
    )

    # Debug: Detailed chunking algorithm analysis
    import psutil

    system_memory_gb = psutil.virtual_memory().total / 1024**3
    logger.debug(
        "Detailed chunking calculation analysis",
        extra={
            "system_memory_gb": system_memory_gb,
            "memory_factor_applied": (
                2.0
                if system_memory_gb >= 32
                else (
                    1.5
                    if system_memory_gb >= 16
                    else (1.0 if system_memory_gb >= 8 else 0.5)
                )
            ),
            "dataset_size_category": (
                "small"
                if estimated_rows <= 500_000
                else (
                    "medium"
                    if estimated_rows <= 2_000_000
                    else ("large" if estimated_rows <= 5_000_000 else "very_large")
                )
            ),
            "chunk_threshold": MEMORY_CHUNK_THRESHOLD,
            "chunking_efficiency_ratio": (
                estimated_rows / MEMORY_CHUNK_THRESHOLD
                if MEMORY_CHUNK_THRESHOLD > 0
                else "N/A"
            ),
        },
    )

    if use_chunking and estimated_rows is not None:
        chunks_per_ngram = (
            estimated_rows + MEMORY_CHUNK_THRESHOLD - 1
        ) // MEMORY_CHUNK_THRESHOLD
        chunked_substeps_per_ngram = 2 + (2 * chunks_per_ngram)
        total_ngram_steps = len(n_gram_lengths) * chunked_substeps_per_ngram
    else:
        substeps_per_ngram = 4
        total_ngram_steps = len(n_gram_lengths) * substeps_per_ngram

    concat_steps = max(1, len(n_gram_lengths) // 2)
    ngram_total = base_steps + total_ngram_steps + concat_steps
    # Use percentage-based progress (0.0 to 100.0) for smooth n-gram progress display
    progress_manager.add_step("ngrams", "Generating n-grams")

    # Add n-gram processing step with hierarchical sub-steps (5 substeps total)
    progress_manager.add_step("process_ngrams", "Processing n-grams for output", 5)
    progress_manager.add_substep(
        "process_ngrams", "analyze_approach", "Analyzing processing approach"
    )
    progress_manager.add_substep(
        "process_ngrams", "extract_unique", "Extracting unique n-grams"
    )
    progress_manager.add_substep(
        "process_ngrams", "sort_ngrams", "Sorting n-grams alphabetically"
    )
    progress_manager.add_substep(
        "process_ngrams", "create_ids", "Creating n-gram IDs"
    )
    progress_manager.add_substep(
        "process_ngrams", "assign_ids", "Assigning n-gram IDs"
    )
    progress_manager.add_step(
        "write_message_ngrams", "Writing message n-grams output", 1
    )
    progress_manager.add_step("write_ngram_defs", "Writing n-gram definitions", 1)
    progress_manager.add_step(
        "write_message_metadata", "Writing message metadata", 1
    )

    # Step 1: Enhanced preprocessing with memory monitoring

    progress_manager.start_step("preprocess")
    # Refresh display after first step is started to ensure they are visible
    progress_manager.refresh_display()
    logger.info(
        "Starting preprocessing step",
        extra={"step": "preprocess", "total_messages": total_messages},
    )

    try:
        # Apply preprocessing with memory monitoring
        sample_df = ldf.limit(1).collect()
        preprocessed_sample = input_reader.preprocess(sample_df)

        # Check memory pressure before full preprocessing
        memory_before_preprocess = memory_manager.get_current_memory_usage()
        pressure_level = memory_manager.get_memory_pressure_level()

        logger.debug(
            "Memory state before preprocessing",
            extra={
                "memory_before_rss_mb": memory_before_preprocess["rss_mb"],
                "memory_before_vms_mb": memory_before_preprocess["vms_mb"],
                "pressure_level": pressure_level.value,
                "available_mb": memory_before_preprocess.get(
                    "available_mb", "unknown"
                ),
                "will_use_critical_fallback": pressure_level
                == MemoryPressureLevel.CRITICAL,
            },
        )

        if pressure_level == MemoryPressureLevel.CRITICAL:
            # Implement disk-based preprocessing fallback
            logger.warning(
                "Critical memory pressure detected, using enhanced preprocessing cleanup",
                extra={
                    "pressure_level": "CRITICAL",
                    "memory_usage_mb": memory_before_preprocess["rss_mb"],
                    "fallback_mechanism": "enhanced_gc_cleanup",
                },
            )
            logger.warning(
                "Critical memory pressure detected, using disk-based preprocessing",
                extra={"fallback_strategy": "disk_based_preprocessing"}
            )
            # For now, proceed with regular preprocessing but with enhanced cleanup
            full_df = ldf.collect()
            memory_manager.enhanced_gc_cleanup()
            preprocessed_df = input_reader.preprocess(full_df)
        else:
            full_df = ldf.collect()
            preprocessed_df = input_reader.preprocess(full_df)

        # Immediate cleanup after preprocessing
        del full_df
        cleanup_stats = memory_manager.enhanced_gc_cleanup()

        # Debug: Log cleanup effectiveness
        memory_after_cleanup = memory_manager.get_current_memory_usage()
        logger.debug(
            "Post-preprocessing cleanup completed",
            extra={
                "memory_before_cleanup_mb": memory_before_preprocess["rss_mb"],
                "memory_after_cleanup_mb": memory_after_cleanup["rss_mb"],
                "memory_freed_mb": memory_before_preprocess["rss_mb"]
                - memory_after_cleanup["rss_mb"],
                "cleanup_effectiveness_percent": (
                    (
                        (
                            memory_before_preprocess["rss_mb"]
                            - memory_after_cleanup["rss_mb"]
                        )
                        / memory_before_preprocess["rss_mb"]
                        * 100
                    )
                    if memory_before_preprocess["rss_mb"] > 0
                    else 0
                ),
            },
        )

        ldf_preprocessed = preprocessed_df.lazy()
        ldf_filtered = ldf_preprocessed.with_columns(
            [(pl.int_range(pl.len()) + 1).alias(COL_MESSAGE_SURROGATE_ID)]
        ).filter(
            pl.col(COL_MESSAGE_TEXT).is_not_null()
            & (pl.col(COL_MESSAGE_TEXT).str.len_chars() > 0)
            & pl.col(COL_AUTHOR_ID).is_not_null()
            & (pl.col(COL_AUTHOR_ID).str.len_chars() > 0)
        )

        filtered_count = ldf_filtered.select(pl.len()).collect().item()
        progress_manager.update_step("preprocess", filtered_count)
        progress_manager.complete_step("preprocess")

        # Update tokenization total with actual filtered count
        if hasattr(progress_manager, "update_step"):
            # For ProgressManager compatibility - update tokenization total based on filtered data
            adaptive_chunk_size = memory_manager.calculate_adaptive_chunk_size(
                50000, "tokenization"
            )
            updated_tokenization_total = None
            if filtered_count > adaptive_chunk_size:
                updated_tokenization_total = (
                    filtered_count + adaptive_chunk_size - 1
                ) // adaptive_chunk_size
            else:
                updated_tokenization_total = filtered_count

            # Try to update the tokenization step total if supported
            try:
                progress_manager.update_step(
                    "tokenize", 0, updated_tokenization_total
                )
                logger.debug(
                    "Updated tokenization total after preprocessing",
                    extra={
                        "original_total": total_messages,
                        "filtered_count": filtered_count,
                        "updated_tokenization_total": updated_tokenization_total,
                    },
                )
            except (AttributeError, TypeError):
                # Progress manager doesn't support dynamic total updates
                pass

        logger.info(
            "Preprocessing step completed",
            extra={
                "step": "preprocess",
                "original_count": total_messages,
                "filtered_count": filtered_count,
                "records_removed": total_messages - filtered_count,
            },
        )

    except MemoryError as e:
        logger.error(
            "Memory exhaustion during preprocessing",
            extra={"step": "preprocess", "memory_error": str(e)},
            exc_info=True,
        )
        progress_manager.fail_step(
            "preprocess", f"Memory exhaustion during preprocessing: {str(e)}"
        )
        raise
    except Exception as e:
        logger.exception(
            "Failed during preprocessing",
            extra={
                "step": "preprocess",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        progress_manager.fail_step(
            "preprocess", f"Failed during preprocessing: {str(e)}"
        )
        raise

    # Step 2: Enhanced tokenization with memory monitoring
    progress_manager.start_step("tokenize")
    logger.info(
        "Starting tokenization step",
        extra={"step": "tokenize", "records_to_tokenize": filtered_count},
    )

    try:

        # Direct progress manager usage - no callback needed

        # Enhanced tokenization with memory management
        from app.utils import tokenize_text

        ldf_tokenized = tokenize_text(
            ldf_filtered,
            COL_MESSAGE_TEXT,
            progress_manager,
            memory_manager,
        )

        progress_manager.complete_step("tokenize")
        memory_manager.enhanced_gc_cleanup()

        logger.info(
            "Tokenization step completed",
            extra={"step": "tokenize", "records_tokenized": filtered_count},
        )

    except MemoryError as e:
        logger.error(
            "Memory exhaustion during tokenization",
            extra={"step": "tokenize", "memory_error": str(e)},
            exc_info=True,
        )
        progress_manager.fail_step(
            "tokenize", f"Memory exhaustion during tokenization: {str(e)}"
        )
        raise
    except Exception as e:
        logger.exception(
            "Failed during tokenization",
            extra={
                "step": "tokenize",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        progress_manager.fail_step(
            "tokenize", f"Failed during tokenization: {str(e)}"
        )
        raise

    # Step 3: Enhanced n-gram generation with memory pressure handling
    progress_manager.start_step("ngrams")
    logger.info(
        "Starting n-gram generation step with percentage-based progress",
        extra={
            "step": "ngrams",
            "min_n": min_n,
            "max_n": max_n,
            "n_gram_lengths": list(range(min_n, max_n + 1)),
            "progress_total": 100.0,
            "progress_method": "percentage_based",
        },
    )

    try:

        # Direct progress manager usage - no callback needed

        # Check if we should use disk-based generation
        # Memory-aware fallback threshold based on system capacity
        if memory_manager:
            import psutil

            total_gb = psutil.virtual_memory().total / 1024**3
            if total_gb >= 32:
                DATASET_SIZE_FALLBACK_THRESHOLD = 3_000_000  # 3M rows
            elif total_gb >= 16:
                DATASET_SIZE_FALLBACK_THRESHOLD = 1_500_000  # 1.5M rows
            else:
                DATASET_SIZE_FALLBACK_THRESHOLD = 500_000  # 500K rows (current)
        else:
            DATASET_SIZE_FALLBACK_THRESHOLD = 500_000  # Fallback default

        should_use_disk_fallback = filtered_count > DATASET_SIZE_FALLBACK_THRESHOLD

        # Also check current memory pressure
        current_pressure = memory_manager.get_memory_pressure_level()

        # Debug: N-gram generation algorithm selection analysis
        current_memory_state = memory_manager.get_current_memory_usage()
        logger.debug(
            "N-gram generation algorithm selection analysis",
            extra={
                "filtered_count": filtered_count,
                "size_threshold": DATASET_SIZE_FALLBACK_THRESHOLD,
                "size_based_fallback_needed": should_use_disk_fallback,
                "current_pressure_level": current_pressure.value,
                "pressure_based_fallback_needed": current_pressure
                == MemoryPressureLevel.CRITICAL,
                "current_memory_mb": current_memory_state["rss_mb"],
                "system_memory_gb": system_memory_gb,
                "algorithm_selection": (
                    "disk_based"
                    if (
                        should_use_disk_fallback
                        or current_pressure == MemoryPressureLevel.CRITICAL
                    )
                    else "vectorized"
                ),
            },
        )

        if (
            should_use_disk_fallback
            or current_pressure == MemoryPressureLevel.CRITICAL
        ):
            # Import and use disk-based fallback
            fallback_reason = (
                "dataset_size" if should_use_disk_fallback else "memory_pressure"
            )
            logger.warning(
                "Using disk-based n-gram generation",
                extra={
                    "dataset_size": filtered_count,
                    "size_threshold": DATASET_SIZE_FALLBACK_THRESHOLD,
                    "dataset_exceeds_threshold": should_use_disk_fallback,
                    "pressure_level": current_pressure.value,
                    "fallback_reason": fallback_reason,
                    "fallback_mechanism": "disk_based_generation",
                    "min_n": min_n,
                    "max_n": max_n,
                },
            )
            from analyzers.ngrams.fallback_processors import (
                generate_ngrams_disk_based,
            )

            if should_use_disk_fallback:
                logger.info(
                    "Large dataset detected, using disk-based n-gram generation",
                    extra={
                        "row_count": filtered_count,
                        "strategy": "disk_based_generation_large_dataset"
                    }
                )
            else:
                logger.warning(
                    "Critical memory pressure, using disk-based n-gram generation", 
                    extra={"strategy": "disk_based_generation_memory_pressure"}
                )
            ldf_ngrams = generate_ngrams_disk_based(
                ldf_tokenized,
                min_n,
                max_n,
                filtered_count,  # Pass the known row count
                memory_manager,
                progress_manager,
            )
        else:
            # Use enhanced vectorized generation with memory monitoring
            ldf_ngrams = _generate_ngrams_with_memory_management(
                ldf_tokenized,
                min_n,
                max_n,
                filtered_count,  # Pass the known row count to avoid memory-intensive recalculation
                memory_manager,
                progress_manager,
            )

        progress_manager.complete_step("ngrams")
        memory_manager.enhanced_gc_cleanup()

        # Log completion with n-gram count
        try:
            ngram_count = ldf_ngrams.select(pl.len()).collect().item()
            logger.info(
                "N-gram generation step completed",
                extra={
                    "step": "ngrams",
                    "min_n": min_n,
                    "max_n": max_n,
                    "total_ngrams_generated": ngram_count,
                },
            )
        except Exception:
            logger.info(
                "N-gram generation step completed",
                extra={
                    "step": "ngrams",
                    "min_n": min_n,
                    "max_n": max_n,
                    "total_ngrams_generated": "unknown",
                },
            )

    except MemoryError as e:
        logger.error(
            "Memory exhaustion during n-gram generation",
            extra={
                "step": "ngrams",
                "min_n": min_n,
                "max_n": max_n,
                "memory_error": str(e),
            },
            exc_info=True,
        )
        progress_manager.fail_step(
            "ngrams", f"Memory exhaustion during n-gram generation: {str(e)}"
        )
        raise
    except Exception as e:
        logger.exception(
            "Failed during n-gram generation",
            extra={
                "step": "ngrams",
                "min_n": min_n,
                "max_n": max_n,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        progress_manager.fail_step(
            "ngrams", f"Failed during n-gram generation: {str(e)}"
        )
        raise

    # Step 4: Process n-grams for output (hierarchical step with 5 sub-steps)
    progress_manager.start_step("process_ngrams")
    logger.info(
        "Starting n-gram processing phase", extra={"step": "process_ngrams"}
    )

    # Sub-step 1: Determine processing approach based on dataset size and memory
    progress_manager.start_substep("process_ngrams", "analyze_approach")
    logger.info(
        "Starting approach analysis step", extra={"step": "analyze_approach"}
    )

    try:
        total_ngrams = ldf_ngrams.select(pl.len()).collect().item()
        CHUNKED_PROCESSING_THRESHOLD = 500_000
        use_chunked_approach = total_ngrams > CHUNKED_PROCESSING_THRESHOLD

        # Set processing substep totals using operation counts instead of n-gram counts
        if hasattr(progress_manager, "update_substep"):
            try:
                # Use operation counts for cleaner progress display
                # extract_unique: use 1 for simplicity since it's a single operation
                progress_manager.update_substep(
                    "process_ngrams", "extract_unique", 0, 1
                )

                # Other operations are also single logical operations
                progress_manager.update_substep(
                    "process_ngrams", "sort_ngrams", 0, 1
                )
                progress_manager.update_substep(
                    "process_ngrams", "create_ids", 0, 1
                )
                progress_manager.update_substep(
                    "process_ngrams", "assign_ids", 0, 1
                )

                logger.debug(
                    "Set processing substep totals using operation counts",
                    extra={
                        "total_ngrams": total_ngrams,
                        "progress_method": "operation_based",
                    },
                )
            except (AttributeError, TypeError):
                # Progress manager doesn't support dynamic total updates
                pass

        # Also consider current memory pressure
        current_pressure = memory_manager.get_memory_pressure_level()
        if current_pressure in [
            MemoryPressureLevel.HIGH,
            MemoryPressureLevel.CRITICAL,
        ]:
            use_chunked_approach = (
                True  # Force chunked approach under memory pressure
            )

        progress_manager.complete_substep("process_ngrams", "analyze_approach")

        logger.info(
            "Approach analysis step completed",
            extra={
                "step": "analyze_approach",
                "total_ngrams": total_ngrams,
                "chunked_threshold": CHUNKED_PROCESSING_THRESHOLD,
                "use_chunked_approach": use_chunked_approach,
                "memory_pressure": current_pressure.value,
                "memory_forced_chunking": current_pressure
                in [MemoryPressureLevel.HIGH, MemoryPressureLevel.CRITICAL],
            },
        )

    except Exception as e:
        logger.exception(
            "Failed during approach analysis",
            extra={
                "step": "analyze_approach",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        progress_manager.fail_substep(
            "process_ngrams",
            "analyze_approach",
            f"Failed during approach analysis: {str(e)}",
        )
        raise

    # Sub-step 2: Memory-aware unique extraction
    progress_manager.start_substep("process_ngrams", "extract_unique")
    logger.info(
        "Starting unique extraction step",
        extra={
            "step": "extract_unique",
            "total_ngrams": total_ngrams,
            "use_chunked_approach": use_chunked_approach,
        },
    )

    try:

        # Direct progress manager usage - no callback needed

        pressure_level = memory_manager.get_memory_pressure_level()

        # Debug: Unique extraction algorithm selection
        current_memory_debug = memory_manager.get_current_memory_usage()
        logger.debug(
            "Unique extraction algorithm selection",
            extra={
                "current_pressure": pressure_level.value,
                "current_memory_mb": current_memory_debug["rss_mb"],
                "total_ngrams": total_ngrams,
                "algorithm_selected": (
                    "external_sort"
                    if pressure_level == MemoryPressureLevel.CRITICAL
                    else (
                        "memory_optimized_streaming"
                        if pressure_level == MemoryPressureLevel.HIGH
                        else "batch_accumulator"
                    )
                ),
            },
        )

        if pressure_level == MemoryPressureLevel.CRITICAL:
            # Use disk-based external sorting approach
            from analyzers.ngrams.memory_strategies import (
                extract_unique_external_sort,
            )

            logger.warning(
                "Critical memory pressure detected, using external sorting",
                extra={"fallback_strategy": "external_sorting"}
            )
            unique_ngram_texts = extract_unique_external_sort(
                ldf_ngrams, memory_manager, progress_manager
            )
        elif pressure_level == MemoryPressureLevel.HIGH:
            # Use enhanced streaming with smaller chunks
            from analyzers.ngrams.fallback_processors import (
                stream_unique_memory_optimized,
            )

            logger.info(
                "High memory pressure detected, using optimized streaming",
                extra={"strategy": "optimized_streaming"}
            )
            unique_ngram_texts = stream_unique_memory_optimized(
                ldf_ngrams, memory_manager, progress_manager
            )
        else:
            # Use current implementation with memory monitoring
            chunk_size = memory_manager.calculate_adaptive_chunk_size(
                50000, "unique_extraction"
            )

            logger.debug(
                "Using batch accumulator for unique extraction",
                extra={
                    "base_chunk_size": 50000,
                    "adaptive_chunk_size": chunk_size,
                    "chunk_size_adjustment_factor": chunk_size / 50000,
                    "extraction_method": "batch_accumulator",
                },
            )

            unique_ngram_texts = _stream_unique_batch_accumulator(
                ldf_ngrams.select("ngram_text"),
                chunk_size=chunk_size,
                progress_manager=progress_manager,
            )

        progress_manager.complete_substep("process_ngrams", "extract_unique")
        memory_manager.enhanced_gc_cleanup()

        # Log completion with unique n-gram count
        try:
            unique_count = len(unique_ngram_texts)

            # Keep sorting and ID creation substeps using operation counts for consistency
            # (Already set to 1 above, no need for updates)
            logger.debug(
                "Using operation-based progress for sorting and ID creation steps",
                extra={
                    "unique_count": unique_count,
                    "progress_method": "operation_based",
                },
            )

            logger.info(
                "Unique extraction step completed",
                extra={
                    "step": "extract_unique",
                    "total_ngrams": total_ngrams,
                    "unique_ngrams": unique_count,
                    "reduction_ratio": (
                        (total_ngrams - unique_count) / total_ngrams
                        if total_ngrams > 0
                        else 0
                    ),
                },
            )
        except Exception:
            logger.info(
                "Unique extraction step completed",
                extra={"step": "extract_unique", "unique_ngrams": "unknown"},
            )

    except MemoryError as e:
        logger.error(
            "Memory exhaustion during unique extraction",
            extra={"step": "extract_unique", "memory_error": str(e)},
            exc_info=True,
        )
        progress_manager.fail_substep(
            "process_ngrams",
            "extract_unique",
            f"Memory exhaustion during unique extraction: {str(e)}",
        )
        raise
    except Exception as e:
        logger.exception(
            "Failed during unique extraction",
            extra={
                "step": "extract_unique",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        progress_manager.fail_substep(
            "process_ngrams",
            "extract_unique",
            f"Failed during unique extraction: {str(e)}",
        )
        raise

    # Sub-step 3: Sort n-grams alphabetically for consistent ordering
    progress_manager.start_substep("process_ngrams", "sort_ngrams")
    logger.info("Starting n-gram sorting step", extra={"step": "sort_ngrams"})

    try:
        # Update progress to show sorting is happening (mid-operation)
        if hasattr(progress_manager, "update_substep"):
            try:
                # Get the total for this substep and show 50% progress
                substep_info = progress_manager.substeps["process_ngrams"][
                    "sort_ngrams"
                ]
                total = substep_info.get("total", 1)
                progress_manager.update_substep(
                    "process_ngrams", "sort_ngrams", max(1, total // 2)
                )
            except:
                pass

        sorted_ngrams = unique_ngram_texts.sort("ngram_text")

        # Complete the progress (operation complete)
        if hasattr(progress_manager, "update_substep"):
            try:
                substep_info = progress_manager.substeps["process_ngrams"][
                    "sort_ngrams"
                ]
                total = substep_info.get("total", 1)
                progress_manager.update_substep(
                    "process_ngrams", "sort_ngrams", total
                )
            except:
                pass

        progress_manager.complete_substep("process_ngrams", "sort_ngrams")

        logger.info("N-gram sorting step completed", extra={"step": "sort_ngrams"})
    except Exception as e:
        logger.exception(
            "Failed during n-gram sorting",
            extra={
                "step": "sort_ngrams",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        progress_manager.fail_substep(
            "process_ngrams", "sort_ngrams", f"Failed during sorting: {str(e)}"
        )
        raise

    # Sub-step 4: Create sequential IDs for n-grams
    progress_manager.start_substep("process_ngrams", "create_ids")
    logger.info("Starting ID creation step", extra={"step": "create_ids"})

    try:
        # Update progress to show ID creation is happening (mid-operation)
        if hasattr(progress_manager, "update_substep"):
            try:
                substep_info = progress_manager.substeps["process_ngrams"][
                    "create_ids"
                ]
                total = substep_info.get("total", 1)
                progress_manager.update_substep(
                    "process_ngrams", "create_ids", max(1, total // 2)
                )
            except:
                pass

        unique_ngrams = sorted_ngrams.with_columns(
            [pl.int_range(pl.len()).alias(COL_NGRAM_ID)]
        )

        # Complete the progress (operation complete)
        if hasattr(progress_manager, "update_substep"):
            try:
                substep_info = progress_manager.substeps["process_ngrams"][
                    "create_ids"
                ]
                total = substep_info.get("total", 1)
                progress_manager.update_substep(
                    "process_ngrams", "create_ids", total
                )
            except:
                pass

        progress_manager.complete_substep("process_ngrams", "create_ids")

        logger.info("ID creation step completed", extra={"step": "create_ids"})
    except Exception as e:
        logger.exception(
            "Failed during ID creation",
            extra={
                "step": "create_ids",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        progress_manager.fail_substep(
            "process_ngrams", "create_ids", f"Failed during ID creation: {str(e)}"
        )
        raise

    # Sub-step 5: Join n-gram IDs back to the main dataset
    progress_manager.start_substep("process_ngrams", "assign_ids")
    logger.info("Starting ID assignment step", extra={"step": "assign_ids"})

    try:
        # Update progress to show ID assignment is happening (mid-operation)
        if hasattr(progress_manager, "update_substep"):
            try:
                substep_info = progress_manager.substeps["process_ngrams"][
                    "assign_ids"
                ]
                total = substep_info.get("total", 1)
                progress_manager.update_substep(
                    "process_ngrams", "assign_ids", max(1, total // 2)
                )
            except:
                pass

        ldf_with_ids = ldf_ngrams.join(
            unique_ngrams.lazy(),
            left_on="ngram_text",
            right_on="ngram_text",
            how="left",
        )

        # Complete the progress (operation complete)
        if hasattr(progress_manager, "update_substep"):
            try:
                substep_info = progress_manager.substeps["process_ngrams"][
                    "assign_ids"
                ]
                total = substep_info.get("total", 1)
                progress_manager.update_substep(
                    "process_ngrams", "assign_ids", total
                )
            except:
                pass

        progress_manager.complete_substep("process_ngrams", "assign_ids")
        progress_manager.complete_step("process_ngrams")

        logger.info("ID assignment step completed", extra={"step": "assign_ids"})
    except Exception as e:
        logger.exception(
            "Failed during ID assignment",
            extra={
                "step": "assign_ids",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        progress_manager.fail_substep(
            "process_ngrams", "assign_ids", f"Failed during ID assignment: {str(e)}"
        )
        raise

    # Steps 5-7: Generate output tables using enhanced streaming with sub-step progress
    logger.info(
        "Starting output generation steps",
        extra={
            "step": "output_generation",
            "outputs": ["message_ngrams", "ngram_definitions", "message_metadata"],
        },
    )

    try:
        logger.info(
            "Writing message n-grams output", extra={"output": "message_ngrams"}
        )
        progress_manager.start_step("write_message_ngrams")
        _enhanced_write_message_ngrams(
            ldf_with_ids,
            context.output(OUTPUT_MESSAGE_NGRAMS).parquet_path,
            progress_manager,
        )
        progress_manager.complete_step("write_message_ngrams")
        logger.info(
            "Message n-grams output completed", extra={"output": "message_ngrams"}
        )
    except Exception as e:
        progress_manager.fail_step(
            "write_message_ngrams", f"Failed writing message n-grams: {str(e)}"
        )
        logger.exception(
            "Failed writing message n-grams output",
            extra={
                "output": "message_ngrams",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise

    try:
        logger.info(
            "Writing n-gram definitions output",
            extra={"output": "ngram_definitions"},
        )
        progress_manager.start_step("write_ngram_defs")
        _enhanced_write_ngram_definitions(
            unique_ngrams,
            context.output(OUTPUT_NGRAM_DEFS).parquet_path,
            progress_manager,
        )
        progress_manager.complete_step("write_ngram_defs")
        logger.info(
            "N-gram definitions output completed",
            extra={"output": "ngram_definitions"},
        )
    except Exception as e:
        progress_manager.fail_step(
            "write_ngram_defs", f"Failed writing n-gram definitions: {str(e)}"
        )
        logger.exception(
            "Failed writing n-gram definitions output",
            extra={
                "output": "ngram_definitions",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise

    try:
        logger.info(
            "Writing message metadata output", extra={"output": "message_metadata"}
        )
        progress_manager.start_step("write_message_metadata")
        _enhanced_write_message_metadata(
            ldf_tokenized,
            context.output(OUTPUT_MESSAGE).parquet_path,
            progress_manager,
        )
        progress_manager.complete_step("write_message_metadata")
        logger.info(
            "Message metadata output completed",
            extra={"output": "message_metadata"},
        )
    except Exception as e:
        progress_manager.fail_step(
            "write_message_metadata", f"Failed writing message metadata: {str(e)}"
        )
        logger.exception(
            "Failed writing message metadata output",
            extra={
                "output": "message_metadata",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise

    # Final memory report and log successful completion with key metrics
    final_memory = memory_manager.get_current_memory_usage()
    logger.info(
        "N-gram analysis completed successfully",
        extra={
            "final_memory_mb": final_memory['rss_mb'],
            "available_memory_mb": final_memory.get('available_mb', 'unknown'),
            "analysis_status": "completed"
        }
    )
    logger.info(
        "N-gram analysis completed successfully",
        extra={
            "min_n": min_n,
            "max_n": max_n,
            "total_messages_processed": total_messages,
            "initial_memory_mb": initial_memory["rss_mb"],
            "final_memory_mb": final_memory["rss_mb"],
            "memory_delta_mb": final_memory["rss_mb"] - initial_memory["rss_mb"],
            "analyzer_version": "enhanced_memory_managed",
        },
    )


def _generate_ngrams_with_memory_management(
    ldf: pl.LazyFrame,
    min_n: int,
    max_n: int,
    estimated_rows: int,
    memory_manager=None,
    progress_manager=None,
) -> pl.LazyFrame:
    """
    Enhanced n-gram generation with memory management integration.

    This function wraps the existing _generate_ngrams_vectorized function
    with additional memory monitoring and cleanup.
    """
    if memory_manager is None:
        memory_manager = MemoryManager()

    try:
        # Monitor memory before generation
        memory_before = memory_manager.get_current_memory_usage()

        # Use existing vectorized generation with enhanced progress reporting
        result = _generate_ngrams_vectorized(
            ldf, min_n, max_n, estimated_rows, progress_manager, memory_manager
        )

        # Force cleanup after generation
        memory_manager.enhanced_gc_cleanup()

        # Monitor memory after generation
        memory_after = memory_manager.get_current_memory_usage()
        memory_used = memory_after["rss_mb"] - memory_before["rss_mb"]

        if memory_used > 500:  # Log significant memory usage
            logger.debug(
                "Significant memory usage during n-gram generation",
                extra={
                    "memory_used_mb": memory_used,
                    "memory_before_mb": memory_before["rss_mb"],
                    "memory_after_mb": memory_after["rss_mb"],
                },
            )

        return result

    except MemoryError as e:
        # If vectorized generation fails, try minimal memory approach
        logger.warning(
            "Vectorized n-gram generation failed due to memory pressure, falling back to minimal approach",
            extra={
                "memory_error": str(e),
                "fallback_mechanism": "disk_based_generation",
            },
        )

        from analyzers.ngrams.fallback_processors import generate_ngrams_disk_based

        return generate_ngrams_disk_based(
            ldf, min_n, max_n, estimated_rows, memory_manager, progress_manager
        )


def _create_dynamic_substeps(progress_manager, min_n: int, max_n: int):
    """Create dynamic sub-steps based on n-gram configuration.

    This function creates phase-based sub-steps that provide clear visibility
    into the different processing stages of vectorized n-gram generation:

    1. Expression setup phase
    2. Individual n-gram length processing phases (one per n-gram length)
    3. Result combination phase

    Args:
        progress_manager: The progress manager to add sub-steps to
        min_n: Minimum n-gram length
        max_n: Maximum n-gram length
    """
    if progress_manager is None:
        return

    try:
        # Setup phase
        progress_manager.add_substep(
            "ngrams", "setup_expressions", "Creating and applying n-gram expressions"
        )

        # N-gram processing phases - one for each n-gram length
        for n in range(min_n, max_n + 1):
            substep_id = f"process_{n}grams"
            description = f"Processing {n}-grams"
            progress_manager.add_substep("ngrams", substep_id, description)

        # Combination phase
        progress_manager.add_substep(
            "ngrams", "combine_results", "Combining n-gram results"
        )
    except Exception as e:
        # Log error but don't break the analysis - fall back to original approach
        logger.warning(
            "Failed to create dynamic sub-steps for vectorized generation",
            extra={
                "min_n": min_n,
                "max_n": max_n,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )


def _generate_ngrams_vectorized(
    ldf: pl.LazyFrame,
    min_n: int,
    max_n: int,
    estimated_rows: int,
    progress_manager: Optional[ProgressManager] = None,
    memory_manager=None,
) -> pl.LazyFrame:
    """
    Generate n-grams using vectorized polars expressions with enhanced phase-based progress reporting.

    This function takes a LazyFrame with a 'tokens' column and generates
    all n-grams from min_n to max_n length, creating a row for each n-gram
    occurrence in each message.

    Enhanced Phase-Based Progress Reporting:
    - Expression setup phase: Creating and applying n-gram expressions
    - Individual n-gram processing phases (one per n-gram length)
    - Result combination phase: Combining all n-gram results
    - Clear visibility into which operation and n-gram length is being processed
    - Memory-aware progress updates during intensive operations

    Args:
        ldf: LazyFrame with 'tokens' column
        min_n: Minimum n-gram length
        max_n: Maximum n-gram length
        estimated_rows: Estimated number of rows for memory management
        progress_manager: Optional progress manager for detailed progress reporting.
    """

    def create_ngrams_expr(n: int) -> pl.Expr:
        """Create an expression to generate n-grams of length n with memory-optimized map_elements."""

        # Optimized map_elements with generator expression and early exit
        def generate_ngrams_optimized(tokens_list):
            """Generate n-grams with memory optimization and error handling."""
            # Handle edge cases - convert polars Series to list if needed
            if hasattr(tokens_list, "to_list"):
                tokens_list = tokens_list.to_list()

            if not tokens_list:
                return []

            if len(tokens_list) < n:
                return []

            # Pre-calculate number of n-grams and pre-allocate list
            num_ngrams = len(tokens_list) - n + 1
            if num_ngrams <= 0:
                return []

            result = [None] * num_ngrams  # Pre-allocate with exact size

            try:
                for i in range(num_ngrams):
                    # Use slice and join efficiently, handle None tokens
                    token_slice = tokens_list[i : i + n]
                    if all(
                        token is not None and str(token).strip()
                        for token in token_slice
                    ):
                        result[i] = " ".join(str(token) for token in token_slice)
                    else:
                        result[i] = None

                # Filter out any empty or None n-grams
                return [ngram for ngram in result if ngram and ngram.strip()]

            except (IndexError, AttributeError, TypeError) as e:
                # Log error if needed and return empty list for robustness
                return []

        return (
            pl.col("tokens")
            .map_elements(generate_ngrams_optimized, return_dtype=pl.List(pl.Utf8))
            .alias(f"ngrams_{n}")
        )

    # Calculate n-gram lengths for processing
    n_gram_lengths = list(range(min_n, max_n + 1))

    logger.debug(
        "Vectorized n-gram generation initialized",
        extra={
            "min_n": min_n,
            "max_n": max_n,
            "n_gram_lengths": n_gram_lengths,
            "total_n_gram_types": len(n_gram_lengths),
            "estimated_rows": estimated_rows,
        },
    )

    # Dynamic memory threshold for chunking based on dataset size and available memory
    def calculate_optimal_chunk_size(dataset_size: int, memory_manager=None) -> int:
        """
        Calculate optimal chunk size based on dataset size and available memory.

        Args:
            dataset_size: Number of rows in dataset
            memory_manager: Optional memory manager for capacity detection

        Returns:
            int: Optimal chunk size for the dataset and system
        """
        import psutil

        # Get memory capacity factor
        if memory_manager:
            total_gb = psutil.virtual_memory().total / 1024**3
            if total_gb >= 32:
                memory_factor = 2.0  # High-memory systems
            elif total_gb >= 16:
                memory_factor = 1.5  # Standard systems
            elif total_gb >= 8:
                memory_factor = 1.0  # Lower-memory systems
            else:
                memory_factor = 0.5  # Very constrained systems
        else:
            memory_factor = 1.0  # Default fallback

        # Base chunk sizes scaled by memory capacity
        if dataset_size <= 500_000:
            base_chunk = int(200_000 * memory_factor)
        elif dataset_size <= 2_000_000:
            base_chunk = int(150_000 * memory_factor)
        elif dataset_size <= 5_000_000:
            base_chunk = int(100_000 * memory_factor)
        else:
            base_chunk = int(75_000 * memory_factor)

        # Ensure reasonable bounds
        return max(10_000, min(base_chunk, 500_000))

    MEMORY_CHUNK_THRESHOLD = (
        calculate_optimal_chunk_size(estimated_rows, memory_manager)
        if estimated_rows
        else 100_000
    )
    use_chunking = (
        estimated_rows is not None and estimated_rows > MEMORY_CHUNK_THRESHOLD
    )

    logger.debug(
        "Vectorized generation chunking strategy determined",
        extra={
            "memory_chunk_threshold": MEMORY_CHUNK_THRESHOLD,
            "estimated_rows": estimated_rows,
            "use_chunking": use_chunking,
            "chunking_reason": (
                "dataset_size_exceeds_threshold"
                if use_chunking
                else "dataset_fits_in_memory"
            ),
        },
    )

    # Create dynamic sub-steps based on n-gram configuration
    _create_dynamic_substeps(progress_manager, min_n, max_n)

    try:
        # Phase 1: Expression Setup
        if progress_manager is not None:
            progress_manager.start_substep("ngrams", "setup_expressions")

        try:
            # Step 1: Generate expressions for all n-gram lengths
            ngram_expressions = [create_ngrams_expr(n) for n in n_gram_lengths]

            # Step 2: Apply all n-gram expressions to create separate columns
            # This creates the n-gram lists but doesn't explode them yet
            ldf_with_ngrams = ldf.with_columns(ngram_expressions)

            if progress_manager is not None:
                progress_manager.complete_substep("ngrams", "setup_expressions")

        except Exception as e:
            if progress_manager is not None:
                progress_manager.fail_substep(
                    "ngrams", "setup_expressions", f"Expression setup failed: {str(e)}"
                )
            raise

        # Phase 2: Process each n-gram length with dedicated sub-steps
        all_ngram_results = []

        logger.debug(
            "Starting individual n-gram length processing phase",
            extra={
                "n_gram_lengths": n_gram_lengths,
                "total_lengths_to_process": len(n_gram_lengths),
                "use_chunking": use_chunking,
                "chunk_threshold": MEMORY_CHUNK_THRESHOLD if use_chunking else "N/A",
            },
        )

        for n_idx, n in enumerate(n_gram_lengths):
            substep_id = f"process_{n}grams"
            ngram_col = f"ngrams_{n}"

            logger.debug(
                "Processing specific n-gram length",
                extra={
                    "n_gram_length": n,
                    "index_in_sequence": n_idx + 1,
                    "total_lengths": len(n_gram_lengths),
                    "substep_id": substep_id,
                    "ngram_column": ngram_col,
                },
            )

            if progress_manager is not None:
                progress_manager.start_substep("ngrams", substep_id)

            try:
                if use_chunking and estimated_rows is not None:
                    # Enhanced chunked processing with detailed progress
                    chunk_size = MEMORY_CHUNK_THRESHOLD // len(n_gram_lengths)
                    chunk_results = []
                    total_chunks = (estimated_rows + chunk_size - 1) // chunk_size

                    logger.debug(
                        "Using chunked processing for n-gram length",
                        extra={
                            "n_gram_length": n,
                            "base_threshold": MEMORY_CHUNK_THRESHOLD,
                            "adjusted_chunk_size": chunk_size,
                            "total_chunks_for_length": total_chunks,
                            "estimated_rows": estimated_rows,
                            "chunk_adjustment_factor": (
                                chunk_size / MEMORY_CHUNK_THRESHOLD
                                if MEMORY_CHUNK_THRESHOLD > 0
                                else "N/A"
                            ),
                        },
                    )

                    for chunk_idx in range(total_chunks):
                        chunk_start = chunk_idx * chunk_size
                        chunk_end = min(chunk_start + chunk_size, estimated_rows)

                        # Process chunk with detailed progress
                        try:
                            # Step 1: Extract and explode chunk
                            chunk_ngrams = (
                                ldf_with_ngrams.slice(
                                    chunk_start, chunk_end - chunk_start
                                )
                                .select([COL_MESSAGE_SURROGATE_ID, pl.col(ngram_col)])
                                .explode(ngram_col)
                            )

                            # Step 2: Filter and format chunk
                            chunk_ngrams = (
                                chunk_ngrams.filter(
                                    pl.col(ngram_col).is_not_null()
                                    & (pl.col(ngram_col).str.len_chars() > 0)
                                )
                                .select(
                                    [
                                        COL_MESSAGE_SURROGATE_ID,
                                        pl.col(ngram_col).alias("ngram_text"),
                                    ]
                                )
                                .collect()  # Collect chunk to manage memory
                            )

                            chunk_results.append(chunk_ngrams)

                            # Update substep progress for this chunk (ensure integers)
                            if progress_manager is not None:
                                try:
                                    # Calculate progress as: chunks completed / total chunks (integers only)
                                    chunk_progress = int(chunk_idx + 1)
                                    total_chunk_count = int(total_chunks)
                                    # Validate progress doesn't exceed total
                                    chunk_progress = min(
                                        chunk_progress, total_chunk_count
                                    )
                                    progress_manager.update_substep(
                                        "ngrams",
                                        substep_id,
                                        chunk_progress,
                                        total_chunk_count,
                                    )
                                except Exception as progress_error:
                                    # Don't let progress reporting failures crash the analysis
                                    logger.warning(
                                        "Progress update failed for n-gram chunk",
                                        extra={
                                            "chunk_index": chunk_idx + 1,
                                            "total_chunks": total_chunks,
                                            "ngram_length": n,
                                            "error": str(progress_error),
                                            "error_type": type(progress_error).__name__,
                                        },
                                    )

                            # Aggressive garbage collection after each chunk
                            gc.collect()

                        except Exception as e:
                            logger.warning(
                                "Error processing chunk during n-gram generation",
                                extra={
                                    "chunk_index": chunk_idx,
                                    "ngram_length": n,
                                    "total_chunks": total_chunks,
                                    "error": str(e),
                                    "error_type": type(e).__name__,
                                },
                            )
                            continue

                    # Combine chunks for this n-gram length
                    if chunk_results:
                        exploded_ngrams = pl.concat(chunk_results).lazy()
                    else:
                        # Empty result with correct schema
                        exploded_ngrams = (
                            ldf_with_ngrams.select(
                                [COL_MESSAGE_SURROGATE_ID, pl.col(ngram_col)]
                            )
                            .limit(0)
                            .select(
                                [
                                    COL_MESSAGE_SURROGATE_ID,
                                    pl.col(ngram_col).alias("ngram_text"),
                                ]
                            )
                        )

                else:
                    # Standard processing with enhanced progress reporting
                    # Total of 4 sub-operations for non-chunked processing
                    total_operations = 4

                    logger.debug(
                        "Using standard processing for n-gram length",
                        extra={
                            "n_gram_length": n,
                            "processing_method": "standard_non_chunked",
                            "total_operations": total_operations,
                            "estimated_rows": estimated_rows,
                        },
                    )

                    # Sub-step 1: Extract n-grams for this length
                    selected_ngrams = ldf_with_ngrams.select(
                        [COL_MESSAGE_SURROGATE_ID, pl.col(ngram_col)]
                    )
                    if progress_manager is not None:
                        try:
                            progress_manager.update_substep(
                                "ngrams", substep_id, 1, int(total_operations)
                            )
                        except Exception:
                            pass  # Ignore progress update failures

                    # Sub-step 2: Explode n-gram lists (memory-intensive operation)
                    exploded_ngrams = selected_ngrams.explode(ngram_col)
                    if progress_manager is not None:
                        try:
                            progress_manager.update_substep(
                                "ngrams", substep_id, 2, int(total_operations)
                            )
                        except Exception:
                            pass  # Ignore progress update failures

                    # Sub-step 3: Filter null/empty n-grams (memory-intensive operation)
                    filtered_ngrams = exploded_ngrams.filter(
                        pl.col(ngram_col).is_not_null()
                        & (pl.col(ngram_col).str.len_chars() > 0)
                    )
                    if progress_manager is not None:
                        try:
                            progress_manager.update_substep(
                                "ngrams", substep_id, 3, int(total_operations)
                            )
                        except Exception:
                            pass  # Ignore progress update failures

                    # Sub-step 4: Format columns
                    exploded_ngrams = filtered_ngrams.select(
                        [
                            COL_MESSAGE_SURROGATE_ID,
                            pl.col(ngram_col).alias("ngram_text"),
                        ]
                    )
                    if progress_manager is not None:
                        try:
                            progress_manager.update_substep(
                                "ngrams", substep_id, 4, int(total_operations)
                            )
                        except Exception:
                            pass  # Ignore progress update failures

                all_ngram_results.append(exploded_ngrams)

                # Complete this n-gram length processing
                if progress_manager is not None:
                    progress_manager.complete_substep("ngrams", substep_id)

                # Aggressive garbage collection between n-gram lengths
                gc.collect()

            except Exception as e:
                if progress_manager is not None:
                    progress_manager.fail_substep(
                        "ngrams", substep_id, f"Processing {n}-grams failed: {str(e)}"
                    )
                raise

        # Phase 3: Combine all results
        logger.debug(
            "Starting n-gram results combination phase",
            extra={
                "total_results_to_combine": len(all_ngram_results),
                "combination_method": (
                    "single_result" if len(all_ngram_results) == 1 else "polars_concat"
                ),
            },
        )

        if progress_manager is not None:
            progress_manager.start_substep("ngrams", "combine_results")

        try:
            if len(all_ngram_results) == 1:
                result_ldf = all_ngram_results[0]
            else:
                # Combine all results using pl.concat
                result_ldf = pl.concat(all_ngram_results)

            if progress_manager is not None:
                progress_manager.complete_substep("ngrams", "combine_results")

        except Exception as e:
            if progress_manager is not None:
                progress_manager.fail_substep(
                    "ngrams", "combine_results", f"Result combination failed: {str(e)}"
                )
            raise

    except Exception as e:
        # Log the error for debugging
        logger.error(
            "Vectorized n-gram generation failed",
            extra={
                "min_n": min_n,
                "max_n": max_n,
                "estimated_rows": estimated_rows,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise

    return result_ldf


def _generate_ngrams_simple(ldf: pl.LazyFrame, min_n: int, max_n: int) -> pl.LazyFrame:
    """
    Alternative simpler n-gram generation using explode operations.

    This approach is more straightforward but may be less efficient for
    very large datasets. Used as fallback if the vectorized approach
    has issues.
    """

    def create_ngrams_for_length(n: int) -> pl.Expr:
        """Create n-grams of specific length n using optimized map_elements."""

        def generate_ngrams_optimized(tokens):
            """Generate n-grams with memory optimization and error handling."""
            # Handle edge cases - convert polars Series to list if needed
            if hasattr(tokens, "to_list"):
                tokens = tokens.to_list()

            if not tokens:
                return []

            if len(tokens) < n:
                return []

            # Pre-calculate and pre-allocate for efficiency
            num_ngrams = len(tokens) - n + 1
            if num_ngrams <= 0:
                return []

            result = [None] * num_ngrams

            try:
                for i in range(num_ngrams):
                    token_slice = tokens[i : i + n]
                    if all(
                        token is not None and str(token).strip()
                        for token in token_slice
                    ):
                        result[i] = " ".join(str(token) for token in token_slice)
                    else:
                        result[i] = None

                return [ngram for ngram in result if ngram and ngram.strip()]

            except (IndexError, AttributeError, TypeError):
                return []

        return pl.col("tokens").map_elements(
            generate_ngrams_optimized,
            return_dtype=pl.List(pl.Utf8),
        )

    # Generate n-grams for all lengths
    ngram_columns = []
    for n in range(min_n, max_n + 1):
        ngram_columns.append(create_ngrams_for_length(n).alias(f"ngrams_{n}"))

    # Apply all n-gram generation
    ldf_with_ngrams = ldf.with_columns(ngram_columns)

    # Collect all n-grams and explode
    all_ngrams_expr = []
    for n in range(min_n, max_n + 1):
        all_ngrams_expr.append(pl.col(f"ngrams_{n}"))

    return (
        ldf_with_ngrams.with_columns(
            [pl.concat_list(all_ngrams_expr).alias("all_ngrams")]
        )
        .select(
            [
                COL_MESSAGE_SURROGATE_ID,
                pl.col("all_ngrams").list.explode().alias("ngram_text"),
            ]
        )
        .filter(
            pl.col("ngram_text").is_not_null()
            & (pl.col("ngram_text").str.len_chars() > 0)
        )
    )
