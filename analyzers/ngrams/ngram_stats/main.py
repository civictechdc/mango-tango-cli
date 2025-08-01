import os

import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq

from analyzer_interface.context import SecondaryAnalyzerContext
from terminal_tools.progress import RichProgressManager

from ..ngrams_base.interface import (
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
)
from .interface import (
    COL_NGRAM_DISTINCT_POSTER_COUNT,
    COL_NGRAM_REPS_PER_USER,
    COL_NGRAM_TOTAL_REPS,
    OUTPUT_NGRAM_FULL,
    OUTPUT_NGRAM_STATS,
)


def main(context: SecondaryAnalyzerContext):
    """
    Refactored ngram_stats analyzer using streaming architecture for memory efficiency.

    Uses lazy evaluation with pl.scan_parquet, chunked processing to avoid cardinality explosion,
    and RichProgressManager for detailed progress feedback.
    """
    # 1. Load inputs as LazyFrames for memory efficiency
    ldf_message_ngrams = pl.scan_parquet(
        context.base.table(OUTPUT_MESSAGE_NGRAMS).parquet_path
    )
    ldf_ngrams = pl.scan_parquet(context.base.table(OUTPUT_NGRAM_DEFS).parquet_path)
    ldf_messages = pl.scan_parquet(context.base.table(OUTPUT_MESSAGE).parquet_path)

    with RichProgressManager("N-gram Statistics Analysis") as progress_manager:
        # Add ALL steps upfront for better UX with the enhanced progress system
        # This provides users with a complete view of the entire analysis process
        progress_manager.add_step("analyze_structure", "Analyzing data structure")
        progress_manager.add_step("compute_stats", "Computing n-gram statistics")
        progress_manager.add_step("write_summary", "Writing summary output")

        # We'll add the full report step after determining its parameters during structure analysis
        # This is needed because we need the data structure info to calculate accurate totals

        # Step 1: Get counts for progress reporting and to determine full report processing approach
        progress_manager.start_step("analyze_structure")

        try:
            ngram_count = ldf_ngrams.select(pl.len()).collect().item()
            message_ngram_count = ldf_message_ngrams.select(pl.len()).collect().item()
            message_count = ldf_messages.select(pl.len()).collect().item()

            # Calculate estimated processing requirements for full report
            # This helps us determine if we need chunked processing and what the total will be
            estimated_chunk_size = max(
                1, min(1000, 100_000 // max(1, message_ngram_count // ngram_count))
            )
            estimated_full_report_chunks = (
                ngram_count + estimated_chunk_size - 1
            ) // estimated_chunk_size

            # Data structure info preserved in progress context instead of direct printing
            # Estimated full report processing info preserved in progress context

            # Now add the full report step with calculated total
            progress_manager.add_step(
                "write_full_report", "Writing full report", estimated_full_report_chunks
            )

            progress_manager.complete_step("analyze_structure")
        except Exception as e:
            progress_manager.fail_step(
                "analyze_structure", f"Failed during structure analysis: {str(e)}"
            )
            raise

        # Step 2: Calculate initial statistics using streaming-friendly aggregations
        progress_manager.start_step("compute_stats")

        try:
            # Calculate total repetitions and distinct poster counts per n-gram
            # Using lazy evaluation to avoid loading entire datasets into memory
            ldf_ngram_stats = (
                ldf_message_ngrams.group_by(COL_NGRAM_ID)
                .agg(
                    [
                        pl.col(COL_MESSAGE_NGRAM_COUNT)
                        .sum()
                        .alias(COL_NGRAM_TOTAL_REPS),
                        pl.col(COL_MESSAGE_SURROGATE_ID)
                        .n_unique()
                        .alias("temp_message_count"),
                    ]
                )
                .filter(pl.col(COL_NGRAM_TOTAL_REPS) > 1)
                # Join with messages to get distinct poster count efficiently
                .join(
                    ldf_message_ngrams.join(
                        ldf_messages.select([COL_MESSAGE_SURROGATE_ID, COL_AUTHOR_ID]),
                        on=COL_MESSAGE_SURROGATE_ID,
                    )
                    .group_by(COL_NGRAM_ID)
                    .agg(
                        pl.col(COL_AUTHOR_ID)
                        .n_unique()
                        .alias(COL_NGRAM_DISTINCT_POSTER_COUNT)
                    ),
                    on=COL_NGRAM_ID,
                    how="inner",
                )
                .select(
                    [
                        COL_NGRAM_ID,
                        COL_NGRAM_TOTAL_REPS,
                        COL_NGRAM_DISTINCT_POSTER_COUNT,
                    ]
                )
            )

            # Create the summary table by joining with n-gram definitions
            ldf_ngram_summary = ldf_ngrams.join(
                ldf_ngram_stats, on=COL_NGRAM_ID, how="inner"
            ).sort(
                [
                    COL_NGRAM_LENGTH,
                    COL_NGRAM_TOTAL_REPS,
                    COL_NGRAM_DISTINCT_POSTER_COUNT,
                ],
                descending=True,
            )

            # Collect and write the summary table
            df_ngram_summary = ldf_ngram_summary.collect(engine="streaming")
            progress_manager.complete_step("compute_stats")
        except Exception as e:
            progress_manager.fail_step(
                "compute_stats", f"Failed during statistics computation: {str(e)}"
            )
            raise

        # Step 3: Write summary output
        progress_manager.start_step("write_summary")

        try:
            df_ngram_summary.write_parquet(
                context.output(OUTPUT_NGRAM_STATS).parquet_path
            )
            progress_manager.complete_step("write_summary")
        except Exception as e:
            progress_manager.fail_step(
                "write_summary", f"Failed writing summary output: {str(e)}"
            )
            raise

        # Step 4: Generate the full report in chunks to avoid cardinality explosion
        progress_manager.start_step("write_full_report")

        try:
            total_ngrams_to_process = df_ngram_summary.height

            # Get schema information for the output file
            sample_full_report = _create_sample_full_report_row(
                ldf_message_ngrams, ldf_ngrams, ldf_messages, df_ngram_summary
            )

            # Process n-grams in chunks to manage memory efficiently
            # Use the actual counts to refine chunk size
            chunk_size = max(
                1, min(1000, 100_000 // max(1, message_ngram_count // ngram_count))
            )
            actual_total_chunks = (
                total_ngrams_to_process + chunk_size - 1
            ) // chunk_size

            # Processing full report info preserved in progress context

            # Initialize output file with schema
            first_chunk = True
            processed_count = 0

            try:
                for chunk_start in range(0, total_ngrams_to_process, chunk_size):
                    chunk_end = min(chunk_start + chunk_size, total_ngrams_to_process)
                    chunk_ngram_summary = df_ngram_summary.slice(
                        chunk_start, chunk_end - chunk_start
                    )

                    # Process this chunk of n-grams
                    chunk_output = _process_ngram_chunk(
                        chunk_ngram_summary, ldf_message_ngrams, ldf_messages
                    )

                    # Write chunk output efficiently
                    if first_chunk:
                        chunk_output.write_parquet(
                            context.output(OUTPUT_NGRAM_FULL).parquet_path
                        )
                        first_chunk = False
                    else:
                        # Use streaming append for better memory efficiency
                        temp_path = (
                            f"{context.output(OUTPUT_NGRAM_FULL).parquet_path}.tmp"
                        )
                        chunk_output.write_parquet(temp_path)

                        # Use PyArrow for efficient file concatenation
                        # Read both files as tables and concatenate
                        existing_table = pq.read_table(
                            context.output(OUTPUT_NGRAM_FULL).parquet_path
                        )
                        new_table = pq.read_table(temp_path)
                        combined_table = pa.concat_tables([existing_table, new_table])

                        # Write combined table back
                        pq.write_table(
                            combined_table,
                            context.output(OUTPUT_NGRAM_FULL).parquet_path,
                        )

                        # Clean up temp file
                        os.remove(temp_path)

                    processed_count += chunk_ngram_summary.height

                    # Update progress with error handling
                    try:
                        # Calculate current chunk number for progress
                        current_chunk = (chunk_start // chunk_size) + 1
                        progress_manager.update_step("write_full_report", current_chunk)
                    except Exception as e:
                        # Don't let progress reporting failures crash the analysis
                        print(
                            f"Warning: Progress update failed for full report chunk {current_chunk}: {e}"
                        )

            except Exception as e:
                progress_manager.fail_step(
                    "write_full_report", f"Failed during chunk processing: {str(e)}"
                )
                raise

            progress_manager.complete_step("write_full_report")
        except Exception as e:
            progress_manager.fail_step(
                "write_full_report", f"Failed during full report generation: {str(e)}"
            )
            raise


def _create_sample_full_report_row(
    ldf_message_ngrams, ldf_ngrams, ldf_messages, df_ngram_summary
):
    """Create a sample row to establish the schema for the full report."""
    if df_ngram_summary.height == 0:
        # Return empty DataFrame with correct schema
        return pl.DataFrame(
            {
                COL_NGRAM_ID: [],
                COL_NGRAM_LENGTH: [],
                COL_NGRAM_WORDS: [],
                COL_NGRAM_TOTAL_REPS: [],
                COL_NGRAM_DISTINCT_POSTER_COUNT: [],
                COL_AUTHOR_ID: [],
                COL_NGRAM_REPS_PER_USER: [],
                COL_MESSAGE_SURROGATE_ID: [],
                COL_MESSAGE_ID: [],
                COL_MESSAGE_TEXT: [],
                COL_MESSAGE_TIMESTAMP: [],
            }
        ).cast({COL_NGRAM_REPS_PER_USER: pl.Int32})

    # Get one n-gram to establish schema
    sample_ngram = df_ngram_summary.head(1)
    sample_output = _process_ngram_chunk(sample_ngram, ldf_message_ngrams, ldf_messages)
    return sample_output.head(0)  # Return empty DataFrame with correct schema


def _process_ngram_chunk(chunk_ngram_summary, ldf_message_ngrams, ldf_messages):
    """Process a chunk of n-grams to generate full report data."""
    # Get n-gram IDs for this chunk
    ngram_ids = chunk_ngram_summary.get_column(COL_NGRAM_ID).to_list()

    # Filter and join data for this chunk of n-grams only
    chunk_output = (
        chunk_ngram_summary.lazy()
        .join(
            ldf_message_ngrams.filter(pl.col(COL_NGRAM_ID).is_in(ngram_ids)),
            on=COL_NGRAM_ID,
        )
        .join(ldf_messages, on=COL_MESSAGE_SURROGATE_ID)
        .with_columns(
            pl.col(COL_MESSAGE_NGRAM_COUNT)
            .sum()
            .over([COL_NGRAM_ID, COL_AUTHOR_ID])
            .alias(COL_NGRAM_REPS_PER_USER)
            .cast(pl.Int32)
        )
        .select(
            [
                COL_NGRAM_ID,
                COL_NGRAM_LENGTH,
                COL_NGRAM_WORDS,
                COL_NGRAM_TOTAL_REPS,
                COL_NGRAM_DISTINCT_POSTER_COUNT,
                COL_AUTHOR_ID,
                COL_NGRAM_REPS_PER_USER,
                COL_MESSAGE_SURROGATE_ID,
                COL_MESSAGE_ID,
                COL_MESSAGE_TEXT,
                COL_MESSAGE_TIMESTAMP,
            ]
        )
        .sort(
            [
                COL_NGRAM_LENGTH,
                COL_NGRAM_TOTAL_REPS,
                COL_NGRAM_DISTINCT_POSTER_COUNT,
                COL_NGRAM_REPS_PER_USER,
                COL_AUTHOR_ID,
                COL_MESSAGE_SURROGATE_ID,
            ],
            descending=[True, True, True, True, False, False],
        )
        .collect(engine="streaming")
    )

    return chunk_output
