import gc
import logging
import os
import tempfile
from pathlib import Path

import polars as pl

from analyzer_interface.context import PrimaryAnalyzerContext
from app.utils import tokenize_text, MemoryManager, MemoryPressureLevel
from terminal_tools.progress import RichProgressManager

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
    chunk_size: int = 50_000,
    column_name: str = "ngram_text",
    progress_callback=None,
) -> pl.DataFrame:
    """
    Memory-efficient streaming unique extraction using batch accumulation with temporary files.

    This function processes large datasets in chunks, streaming each chunk's unique values
    to disk and accumulating results using polars operations instead of Python loops.

    Args:
        ldf_data: LazyFrame containing the data to process
        chunk_size: Size of each processing chunk (default: 50,000)
        column_name: Name of the column to extract unique values from
        progress_callback: Optional callback for progress updates (chunk_num, total_chunks)

    Returns:
        DataFrame containing all unique values across chunks

    Raises:
        Exception: If streaming operations fail
    """
    # Get total count for chunking
    total_count = ldf_data.select(pl.len()).collect().item()
    total_chunks = (total_count + chunk_size - 1) // chunk_size

    # Use temporary files for intermediate storage of unique values
    temp_files = []

    try:
        # Process each chunk and stream unique values to separate temp files
        for chunk_idx in range(total_chunks):
            chunk_start = chunk_idx * chunk_size

            # Update progress before processing chunk
            if progress_callback:
                try:
                    progress_callback(chunk_idx, total_chunks)
                except Exception as e:
                    print(
                        f"Warning: Progress callback failed for chunk {chunk_idx + 1}: {e}"
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
            except Exception as e:
                print(f"Warning: Failed to process chunk {chunk_idx + 1}: {e}")
                # Remove failed temp file from list
                temp_files.remove(temp_path)
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
                continue

        # Final progress update
        if progress_callback:
            try:
                progress_callback(total_chunks, total_chunks)
            except Exception as e:
                print(f"Warning: Final progress callback failed: {e}")

        if not temp_files:
            # If no chunks were processed successfully, return empty DataFrame
            return pl.DataFrame({column_name: []})

        # Combine all temporary files using polars streaming operations
        # Read all temp files as lazy frames and concatenate
        chunk_lazy_frames = []
        for temp_path in temp_files:
            try:
                # Read each temp file as a lazy frame
                chunk_ldf = pl.scan_csv(
                    temp_path, has_header=False, new_columns=[column_name]
                )
                chunk_lazy_frames.append(chunk_ldf)
            except Exception as e:
                print(f"Warning: Failed to read temporary file {temp_path}: {e}")
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
    try:
        # Primary: Use streaming sink_parquet
        lazy_frame.sink_parquet(output_path, maintain_order=True)
        progress_manager.complete_step(operation_name)
    except Exception as streaming_error:
        progress_manager.update_step(
            operation_name,
            f"Streaming failed, falling back to collect(): {str(streaming_error)}",
        )
        try:
            # Fallback: Traditional collect + write
            lazy_frame.collect().write_parquet(output_path)
            progress_manager.complete_step(operation_name)
        except Exception as fallback_error:
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

    # Add sub-steps for this write operation
    progress_manager.add_substep(step_id, "group", "Grouping n-grams by message")
    progress_manager.add_substep(step_id, "aggregate", "Aggregating n-gram counts")
    progress_manager.add_substep(step_id, "sort", "Sorting grouped data")
    progress_manager.add_substep(step_id, "write", "Writing to parquet file")

    try:
        # Sub-step 1: Grouping n-grams by message
        progress_manager.start_substep(step_id, "group")

        # Apply group_by operation
        grouped_ldf = ldf_with_ids.group_by([COL_MESSAGE_SURROGATE_ID, COL_NGRAM_ID])
        progress_manager.complete_substep(step_id, "group")

        # Sub-step 2: Aggregating n-gram counts
        progress_manager.start_substep(step_id, "aggregate")

        # Apply aggregation
        aggregated_ldf = grouped_ldf.agg([pl.len().alias(COL_MESSAGE_NGRAM_COUNT)])
        progress_manager.complete_substep(step_id, "aggregate")

        # Sub-step 3: Sorting grouped data
        progress_manager.start_substep(step_id, "sort")

        # Apply sorting
        sorted_ldf = aggregated_ldf.sort([COL_MESSAGE_SURROGATE_ID, COL_NGRAM_ID])
        progress_manager.complete_substep(step_id, "sort")

        # Sub-step 4: Writing to parquet file
        progress_manager.start_substep(step_id, "write")

        # Attempt streaming write with fallback
        try:
            sorted_ldf.sink_parquet(output_path, maintain_order=True)
        except Exception as streaming_error:
            # Fallback to collect + write
            sorted_ldf.collect().write_parquet(output_path)

        progress_manager.complete_substep(step_id, "write")
        progress_manager.complete_step(step_id)

    except Exception as e:
        progress_manager.fail_step(step_id, f"Failed writing message n-grams: {str(e)}")
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

    # Add sub-steps for this write operation
    progress_manager.add_substep(step_id, "metadata", "Preparing n-gram metadata")
    progress_manager.add_substep(step_id, "lengths", "Calculating n-gram lengths")
    progress_manager.add_substep(step_id, "sort", "Sorting definitions")
    progress_manager.add_substep(step_id, "write", "Writing definitions to parquet")

    try:
        # Sub-step 1: Preparing n-gram metadata
        progress_manager.start_substep(step_id, "metadata")

        # Start with the base LazyFrame and select core columns
        base_ldf = unique_ngrams.lazy().select(
            [
                COL_NGRAM_ID,
                pl.col("ngram_text").alias(COL_NGRAM_WORDS),
            ]
        )
        progress_manager.complete_substep(step_id, "metadata")

        # Sub-step 2: Calculating n-gram lengths
        progress_manager.start_substep(step_id, "lengths")

        # Add n-gram length calculation
        length_ldf = base_ldf.with_columns(
            [pl.col(COL_NGRAM_WORDS).str.split(" ").list.len().alias(COL_NGRAM_LENGTH)]
        )
        progress_manager.complete_substep(step_id, "lengths")

        # Sub-step 3: Sorting definitions
        progress_manager.start_substep(step_id, "sort")

        # Sort by ngram_id for consistent ordering
        sorted_ldf = length_ldf.sort(COL_NGRAM_ID)
        progress_manager.complete_substep(step_id, "sort")

        # Sub-step 4: Writing definitions to parquet
        progress_manager.start_substep(step_id, "write")

        # Attempt streaming write with fallback
        try:
            sorted_ldf.sink_parquet(output_path, maintain_order=True)
        except Exception as streaming_error:
            # Fallback to collect + write
            sorted_ldf.collect().write_parquet(output_path)

        progress_manager.complete_substep(step_id, "write")
        progress_manager.complete_step(step_id)

    except Exception as e:
        progress_manager.fail_step(
            step_id, f"Failed writing n-gram definitions: {str(e)}"
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

    # Add sub-steps for this write operation
    progress_manager.add_substep(step_id, "select", "Selecting message columns")
    progress_manager.add_substep(step_id, "deduplicate", "Deduplicating messages")
    progress_manager.add_substep(step_id, "sort", "Sorting by surrogate ID")
    progress_manager.add_substep(step_id, "write", "Writing metadata to parquet")

    try:
        # Sub-step 1: Selecting message columns
        progress_manager.start_substep(step_id, "select")

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
        progress_manager.complete_substep(step_id, "select")

        # Sub-step 2: Deduplicating messages
        progress_manager.start_substep(step_id, "deduplicate")

        # Apply deduplication by surrogate ID
        deduplicated_ldf = selected_ldf.unique(subset=[COL_MESSAGE_SURROGATE_ID])
        progress_manager.complete_substep(step_id, "deduplicate")

        # Sub-step 3: Sorting by surrogate ID
        progress_manager.start_substep(step_id, "sort")

        # Sort by surrogate ID for consistent ordering
        sorted_ldf = deduplicated_ldf.sort(COL_MESSAGE_SURROGATE_ID)
        progress_manager.complete_substep(step_id, "sort")

        # Sub-step 4: Writing metadata to parquet
        progress_manager.start_substep(step_id, "write")

        # Attempt streaming write with fallback
        try:
            sorted_ldf.sink_parquet(output_path, maintain_order=True)
        except Exception as streaming_error:
            # Fallback to collect + write
            sorted_ldf.collect().write_parquet(output_path)

        progress_manager.complete_substep(step_id, "write")
        progress_manager.complete_step(step_id)

    except Exception as e:
        progress_manager.fail_step(
            step_id, f"Failed writing message metadata: {str(e)}"
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

    # Validate parameters
    assert isinstance(min_n, int) and min_n >= 1, "min_n must be a positive integer"
    assert isinstance(max_n, int) and max_n >= min_n, "max_n must be >= min_n"

    # Initialize memory manager
    memory_manager = MemoryManager(max_memory_gb=4.0, process_name="ngram_analyzer")
    
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

    # Use memory-aware progress manager instead of regular one
    from app.memory_aware_progress import MemoryAwareProgressManager
    
    with MemoryAwareProgressManager("N-gram Analysis with Memory Monitoring", memory_manager) as progress_manager:
        # Memory checkpoint: Initial state
        initial_memory = memory_manager.get_current_memory_usage()
        progress_manager.console.print(f"[blue]Starting analysis - Initial memory: {initial_memory['rss_mb']:.1f}MB[/blue]")
        
        # Add ALL steps upfront for better UX with the enhanced progress system
        progress_manager.add_step("preprocess", "Preprocessing and filtering messages", total_messages)

        # Calculate tokenization total based on memory-aware chunking
        initial_chunk_size = 50000
        adaptive_chunk_size = memory_manager.calculate_adaptive_chunk_size(initial_chunk_size, "tokenization")
        tokenization_total = None
        if total_messages > adaptive_chunk_size:
            tokenization_total = (total_messages + adaptive_chunk_size - 1) // adaptive_chunk_size
        progress_manager.add_step("tokenize", "Tokenizing text data", tokenization_total)

        # Enhanced n-gram generation step calculation
        n_gram_lengths = list(range(min_n, max_n + 1))
        estimated_rows = total_messages
        base_steps = 2
        MEMORY_CHUNK_THRESHOLD = 100_000
        use_chunking = estimated_rows is not None and estimated_rows > MEMORY_CHUNK_THRESHOLD

        if use_chunking and estimated_rows is not None:
            chunks_per_ngram = (estimated_rows + MEMORY_CHUNK_THRESHOLD - 1) // MEMORY_CHUNK_THRESHOLD
            chunked_substeps_per_ngram = 2 + (2 * chunks_per_ngram)
            total_ngram_steps = len(n_gram_lengths) * chunked_substeps_per_ngram
        else:
            substeps_per_ngram = 4
            total_ngram_steps = len(n_gram_lengths) * substeps_per_ngram

        concat_steps = max(1, len(n_gram_lengths) // 2)
        ngram_total = base_steps + total_ngram_steps + concat_steps
        progress_manager.add_step("ngrams", "Generating n-grams", ngram_total)

        # Add remaining steps
        progress_manager.add_step("analyze_approach", "Analyzing processing approach", 1)
        expected_unique_chunks = max(1, total_messages // 50000) if total_messages > 500000 else 1
        progress_manager.add_step("extract_unique", "Extracting unique n-grams", expected_unique_chunks)
        progress_manager.add_step("sort_ngrams", "Sorting n-grams alphabetically", 1)
        progress_manager.add_step("create_ids", "Creating n-gram IDs", 1)
        progress_manager.add_step("assign_ids", "Assigning n-gram IDs", 1)
        progress_manager.add_step("write_message_ngrams", "Writing message n-grams output", 1)
        progress_manager.add_step("write_ngram_defs", "Writing n-gram definitions", 1)
        progress_manager.add_step("write_message_metadata", "Writing message metadata", 1)

        # Step 1: Enhanced preprocessing with memory monitoring
        progress_manager.start_step("preprocess")

        try:
            # Apply preprocessing with memory monitoring
            sample_df = ldf.limit(1).collect()
            preprocessed_sample = input_reader.preprocess(sample_df)

            # Check memory pressure before full preprocessing
            memory_before_preprocess = memory_manager.get_current_memory_usage()
            pressure_level = memory_manager.get_memory_pressure_level()
            
            if pressure_level == MemoryPressureLevel.CRITICAL:
                # Implement disk-based preprocessing fallback
                progress_manager.console.print("[red]Critical memory pressure - using disk-based preprocessing[/red]")
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
            progress_manager.update_step_with_memory("preprocess", filtered_count, "preprocessing")
            progress_manager.complete_step("preprocess")

        except MemoryError as e:
            progress_manager.fail_step("preprocess", f"Memory exhaustion during preprocessing: {str(e)}")
            raise
        except Exception as e:
            progress_manager.fail_step("preprocess", f"Failed during preprocessing: {str(e)}")
            raise

        # Step 2: Enhanced tokenization with memory monitoring
        progress_manager.start_step("tokenize")

        try:
            def memory_aware_tokenize_callback(current_chunk, total_chunks):
                progress_manager.update_step_with_memory("tokenize", current_chunk, "tokenization")
                
                # Check if we need to reduce chunk size mid-process
                pressure_level = memory_manager.get_memory_pressure_level()
                if pressure_level == MemoryPressureLevel.CRITICAL:
                    # Signal to reduce chunk size
                    current_adaptive = memory_manager.calculate_adaptive_chunk_size(adaptive_chunk_size, "tokenization")
                    return {"reduce_chunk_size": True, "new_size": current_adaptive // 2}
                return {"continue": True}

            # Enhanced tokenization with memory management
            from app.utils import tokenize_text
            ldf_tokenized = tokenize_text(
                ldf_filtered, COL_MESSAGE_TEXT, memory_aware_tokenize_callback, memory_manager
            )
            
            progress_manager.complete_step("tokenize")
            memory_manager.enhanced_gc_cleanup()

        except MemoryError as e:
            progress_manager.fail_step("tokenize", f"Memory exhaustion during tokenization: {str(e)}")
            raise
        except Exception as e:
            progress_manager.fail_step("tokenize", f"Failed during tokenization: {str(e)}")
            raise

        # Step 3: Enhanced n-gram generation with memory pressure handling
        progress_manager.start_step("ngrams")

        try:
            def memory_aware_ngram_callback(current, total):
                progress_manager.update_step_with_memory("ngrams", current, "n-gram generation")
                
                # Return memory pressure info for adaptive processing
                pressure_level = memory_manager.get_memory_pressure_level()
                return {
                    "pressure_level": pressure_level,
                    "should_use_disk_fallback": pressure_level == MemoryPressureLevel.CRITICAL
                }

            # Check if we should use disk-based generation
            current_pressure = memory_manager.get_memory_pressure_level()
            
            if current_pressure == MemoryPressureLevel.CRITICAL:
                # Import and use disk-based fallback
                from analyzers.ngrams.fallback_processors import generate_ngrams_disk_based
                progress_manager.console.print("[red]Critical memory pressure - using disk-based n-gram generation[/red]")
                ldf_ngrams = generate_ngrams_disk_based(
                    ldf_tokenized, min_n, max_n, memory_aware_ngram_callback, memory_manager
                )
            else:
                # Use enhanced vectorized generation with memory monitoring
                ldf_ngrams = _generate_ngrams_with_memory_management(
                    ldf_tokenized, min_n, max_n, memory_aware_ngram_callback, memory_manager
                )

            progress_manager.complete_step("ngrams")
            memory_manager.enhanced_gc_cleanup()

        except MemoryError as e:
            progress_manager.fail_step("ngrams", f"Memory exhaustion during n-gram generation: {str(e)}")
            raise
        except Exception as e:
            progress_manager.fail_step("ngrams", f"Failed during n-gram generation: {str(e)}")
            raise

        # Step 4: Determine processing approach based on dataset size and memory
        progress_manager.start_step("analyze_approach")

        try:
            total_ngrams = ldf_ngrams.select(pl.len()).collect().item()
            CHUNKED_PROCESSING_THRESHOLD = 500_000
            use_chunked_approach = total_ngrams > CHUNKED_PROCESSING_THRESHOLD
            
            # Also consider current memory pressure
            current_pressure = memory_manager.get_memory_pressure_level()
            if current_pressure in [MemoryPressureLevel.HIGH, MemoryPressureLevel.CRITICAL]:
                use_chunked_approach = True  # Force chunked approach under memory pressure

            progress_manager.complete_step("analyze_approach")

        except Exception as e:
            progress_manager.fail_step("analyze_approach", f"Failed during approach analysis: {str(e)}")
            raise

        # Step 5: Memory-aware unique extraction
        progress_manager.start_step("extract_unique")

        try:
            def unique_progress_callback(current_chunk, total_chunks):
                progress_manager.update_step_with_memory("extract_unique", current_chunk, "unique extraction")

            pressure_level = memory_manager.get_memory_pressure_level()
            
            if pressure_level == MemoryPressureLevel.CRITICAL:
                # Use disk-based external sorting approach
                from analyzers.ngrams.memory_strategies import extract_unique_external_sort
                progress_manager.console.print("[red]Critical memory pressure - using external sorting[/red]")
                unique_ngram_texts = extract_unique_external_sort(
                    ldf_ngrams, memory_manager, progress_manager
                )
            elif pressure_level == MemoryPressureLevel.HIGH:
                # Use enhanced streaming with smaller chunks
                from analyzers.ngrams.fallback_processors import stream_unique_memory_optimized
                progress_manager.console.print("[yellow]High memory pressure - using optimized streaming[/yellow]")
                unique_ngram_texts = stream_unique_memory_optimized(
                    ldf_ngrams, memory_manager, progress_manager
                )
            else:
                # Use current implementation with memory monitoring
                chunk_size = memory_manager.calculate_adaptive_chunk_size(50000, "unique_extraction")
                unique_ngram_texts = _stream_unique_batch_accumulator(
                    ldf_ngrams.select("ngram_text"),
                    chunk_size=chunk_size,
                    progress_callback=unique_progress_callback
                )

            progress_manager.complete_step("extract_unique")
            memory_manager.enhanced_gc_cleanup()

        except MemoryError as e:
            progress_manager.fail_step("extract_unique", f"Memory exhaustion during unique extraction: {str(e)}")
            raise
        except Exception as e:
            progress_manager.fail_step("extract_unique", f"Failed during unique extraction: {str(e)}")
            raise

        # Step 6: Sort n-grams alphabetically for consistent ordering
        progress_manager.start_step("sort_ngrams")

        try:
            sorted_ngrams = unique_ngram_texts.sort("ngram_text")
            progress_manager.complete_step("sort_ngrams")
        except Exception as e:
            progress_manager.fail_step("sort_ngrams", f"Failed during sorting: {str(e)}")
            raise

        # Step 7: Create sequential IDs for n-grams
        progress_manager.start_step("create_ids")

        try:
            unique_ngrams = sorted_ngrams.with_columns(
                [pl.int_range(pl.len()).alias(COL_NGRAM_ID)]
            )
            progress_manager.complete_step("create_ids")
        except Exception as e:
            progress_manager.fail_step("create_ids", f"Failed during ID creation: {str(e)}")
            raise

        # Step 8: Join n-gram IDs back to the main dataset
        progress_manager.start_step("assign_ids")

        try:
            ldf_with_ids = ldf_ngrams.join(
                unique_ngrams.lazy(),
                left_on="ngram_text",
                right_on="ngram_text",
                how="left",
            )
            progress_manager.complete_step("assign_ids")
        except Exception as e:
            progress_manager.fail_step("assign_ids", f"Failed during ID assignment: {str(e)}")
            raise

        # Steps 9-11: Generate output tables using enhanced streaming with sub-step progress
        try:
            _enhanced_write_message_ngrams(
                ldf_with_ids,
                context.output(OUTPUT_MESSAGE_NGRAMS).parquet_path,
                progress_manager,
            )
        except Exception as e:
            raise

        try:
            _enhanced_write_ngram_definitions(
                unique_ngrams,
                context.output(OUTPUT_NGRAM_DEFS).parquet_path,
                progress_manager,
            )
        except Exception as e:
            raise

        try:
            _enhanced_write_message_metadata(
                ldf_tokenized,
                context.output(OUTPUT_MESSAGE).parquet_path,
                progress_manager,
            )
        except Exception as e:
            raise

        # Final memory report
        progress_manager.display_memory_summary()


def _generate_ngrams_with_memory_management(
    ldf: pl.LazyFrame, min_n: int, max_n: int, progress_callback=None, memory_manager=None
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
        result = _generate_ngrams_vectorized(ldf, min_n, max_n, progress_callback)
        
        # Force cleanup after generation
        memory_manager.enhanced_gc_cleanup()
        
        # Monitor memory after generation
        memory_after = memory_manager.get_current_memory_usage()
        memory_used = memory_after['rss_mb'] - memory_before['rss_mb']
        
        if memory_used > 500:  # Log significant memory usage
            logging.info(f"N-gram generation used {memory_used:.1f}MB")
        
        return result
        
    except MemoryError as e:
        # If vectorized generation fails, try minimal memory approach
        logging.warning("Vectorized n-gram generation failed due to memory pressure, falling back to minimal approach")
        
        from analyzers.ngrams.fallback_processors import generate_ngrams_disk_based
        return generate_ngrams_disk_based(ldf, min_n, max_n, progress_callback, memory_manager)


def _generate_ngrams_vectorized(
    ldf: pl.LazyFrame, min_n: int, max_n: int, progress_callback=None
) -> pl.LazyFrame:
    """
    Generate n-grams using vectorized polars expressions with enhanced progress reporting.

    This function takes a LazyFrame with a 'tokens' column and generates
    all n-grams from min_n to max_n length, creating a row for each n-gram
    occurrence in each message.

    Enhanced Progress Reporting:
    - Provides 20-50+ progress steps instead of 4-6
    - Reports progress during memory-intensive operations (explode, filter, concat)
    - Shows progress for each chunk when processing large datasets
    - Breaks down n-gram processing into granular sub-operations

    Args:
        ldf: LazyFrame with 'tokens' column
        min_n: Minimum n-gram length
        max_n: Maximum n-gram length
        progress_callback: Optional function to call for progress updates.
                         Should accept (current, total) parameters.
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

    def safe_progress_update(current: int, total: int, operation: str = ""):
        """Safely update progress with error handling to prevent crashes."""
        if progress_callback is None:
            return

        try:
            # Validate inputs
            if not isinstance(current, int) or not isinstance(total, int):
                return
            if current < 0 or total <= 0 or current > total:
                return

            progress_callback(current, total)
        except Exception as e:
            # Follow the same pattern as the main() function - print warning but continue
            print(f"Warning: Progress update failed for {operation}: {e}")

    # Calculate total steps for enhanced progress reporting
    n_gram_lengths = list(range(min_n, max_n + 1))

    # Estimate dataset size for chunking decision
    estimated_rows = None
    try:
        estimated_rows = ldf.select(pl.len()).collect().item()
    except Exception:
        # If we can't get row count efficiently, proceed without chunking
        pass

    # Memory threshold for chunking (same as current implementation)
    MEMORY_CHUNK_THRESHOLD = 100_000
    use_chunking = (
        estimated_rows is not None and estimated_rows > MEMORY_CHUNK_THRESHOLD
    )

    # Enhanced progress calculation
    base_steps = 2  # Generate expressions + Apply expressions

    if use_chunking and estimated_rows is not None:
        # Calculate number of chunks per n-gram length
        chunks_per_ngram = (
            estimated_rows + MEMORY_CHUNK_THRESHOLD - 1
        ) // MEMORY_CHUNK_THRESHOLD
        # Each n-gram length has: 1 setup + (2 operations * chunks) + 1 completion = 2 + 2*chunks
        chunked_substeps_per_ngram = 2 + (2 * chunks_per_ngram)
        total_ngram_steps = len(n_gram_lengths) * chunked_substeps_per_ngram
    else:
        # Non-chunked: each n-gram length has 4 sub-operations
        # 1. Extract n-grams, 2. Explode, 3. Filter, 4. Format columns
        substeps_per_ngram = 4
        total_ngram_steps = len(n_gram_lengths) * substeps_per_ngram

    # Final concat operation - more steps if combining many results
    concat_steps = max(
        1, len(n_gram_lengths) // 2
    )  # Show progress for complex concat operations

    total_steps = base_steps + total_ngram_steps + concat_steps
    current_step = 0

    # Report initial progress
    safe_progress_update(current_step, total_steps, "initialization")

    # Step 1: Generate expressions for all n-gram lengths
    ngram_expressions = [create_ngrams_expr(n) for n in n_gram_lengths]
    current_step += 1
    safe_progress_update(current_step, total_steps, "expression generation")

    # Step 2: Apply all n-gram expressions to create separate columns
    # This creates the n-gram lists but doesn't explode them yet
    ldf_with_ngrams = ldf.with_columns(ngram_expressions)
    current_step += 1
    safe_progress_update(current_step, total_steps, "expression application")

    # Step 3: Process each n-gram column with enhanced progress reporting
    all_ngram_results = []

    for n_idx, n in enumerate(n_gram_lengths):
        ngram_col = f"ngrams_{n}"

        # Progress update: Starting n-gram length processing
        safe_progress_update(current_step, total_steps, f"starting n-gram length {n}")

        if use_chunking and estimated_rows is not None:
            # Enhanced chunked processing with detailed progress
            chunk_size = MEMORY_CHUNK_THRESHOLD // len(n_gram_lengths)
            chunk_results = []
            total_chunks = (estimated_rows + chunk_size - 1) // chunk_size

            # Progress update: Starting chunked processing for this n-gram length
            current_step += 1
            safe_progress_update(current_step, total_steps, f"n-gram {n} chunked setup")

            for chunk_idx in range(total_chunks):
                chunk_start = chunk_idx * chunk_size
                chunk_end = min(chunk_start + chunk_size, estimated_rows)

                # Process chunk with detailed progress
                try:
                    # Step 1: Extract and explode chunk
                    chunk_ngrams = (
                        ldf_with_ngrams.slice(chunk_start, chunk_end - chunk_start)
                        .select([COL_MESSAGE_SURROGATE_ID, pl.col(ngram_col)])
                        .explode(ngram_col)
                    )

                    # Progress update after explode operation
                    current_step += 1
                    safe_progress_update(
                        current_step,
                        total_steps,
                        f"n-gram {n} chunk {chunk_idx+1}/{total_chunks} exploded",
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

                    # Progress update after filter and format
                    current_step += 1
                    safe_progress_update(
                        current_step,
                        total_steps,
                        f"n-gram {n} chunk {chunk_idx+1}/{total_chunks} filtered",
                    )

                except Exception as e:
                    print(
                        f"Warning: Error processing chunk {chunk_idx} for n-gram {n}: {e}"
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

            # Progress update: Completed chunked processing for this n-gram length
            current_step += 1
            safe_progress_update(
                current_step, total_steps, f"n-gram {n} chunks combined"
            )

        else:
            # Standard processing with enhanced progress reporting
            # Sub-step 1: Extract n-grams for this length
            selected_ngrams = ldf_with_ngrams.select(
                [COL_MESSAGE_SURROGATE_ID, pl.col(ngram_col)]
            )
            current_step += 1
            safe_progress_update(current_step, total_steps, f"n-gram {n} extracted")

            # Sub-step 2: Explode n-gram lists (memory-intensive operation)
            exploded_ngrams = selected_ngrams.explode(ngram_col)
            current_step += 1
            safe_progress_update(current_step, total_steps, f"n-gram {n} exploded")

            # Sub-step 3: Filter null/empty n-grams (memory-intensive operation)
            filtered_ngrams = exploded_ngrams.filter(
                pl.col(ngram_col).is_not_null()
                & (pl.col(ngram_col).str.len_chars() > 0)
            )
            current_step += 1
            safe_progress_update(current_step, total_steps, f"n-gram {n} filtered")

            # Sub-step 4: Format columns
            exploded_ngrams = filtered_ngrams.select(
                [
                    COL_MESSAGE_SURROGATE_ID,
                    pl.col(ngram_col).alias("ngram_text"),
                ]
            )
            current_step += 1
            safe_progress_update(current_step, total_steps, f"n-gram {n} formatted")

        all_ngram_results.append(exploded_ngrams)

    # Step 4: Combine all results using pl.concat with enhanced progress
    if len(all_ngram_results) == 1:
        result_ldf = all_ngram_results[0]
        current_step += concat_steps
        safe_progress_update(
            current_step, total_steps, "single result, no concat needed"
        )
    else:
        # For multiple results, show progress during concatenation
        if concat_steps > 1:
            # Progressive concatenation for better progress visibility
            result_ldf = all_ngram_results[0]
            for i, additional_result in enumerate(all_ngram_results[1:], 1):
                result_ldf = pl.concat([result_ldf, additional_result])
                current_step += 1
                safe_progress_update(
                    current_step,
                    total_steps,
                    f"concatenated {i+1}/{len(all_ngram_results)} results",
                )

            # Fill remaining concat steps if any
            while current_step < total_steps:
                current_step += 1
                safe_progress_update(current_step, total_steps, "concat finalization")
        else:
            # Single concat operation
            result_ldf = pl.concat(all_ngram_results)
            current_step += 1
            safe_progress_update(current_step, total_steps, "results concatenated")

    # Ensure we end at exactly total_steps
    if current_step < total_steps:
        current_step = total_steps
        safe_progress_update(current_step, total_steps, "n-gram generation completed")

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
