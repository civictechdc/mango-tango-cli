import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq

from analyzer_interface.context import SecondaryAnalyzerContext
from terminal_tools import ProgressReporter

from ..ngrams_base.interface import (
    COL_AUTHOR_ID,
    COL_MESSAGE_ID,
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


def _compute_ngram_statistics(
    df_message_ngrams: pl.DataFrame, df_messages: pl.DataFrame
) -> pl.DataFrame:
    """
    Compute basic statistics for each n-gram.

    Args:
        df_message_ngrams: DataFrame with message_surrogate_id and ngram_id
        df_messages: DataFrame with message_surrogate_id and user_id

    Returns:
        DataFrame with columns [ngram_id, ngram_total_reps, ngram_distinct_poster_count]
        Filters out n-grams with only 1 repetition.
    """
    dict_authors_by_message = {
        row[COL_MESSAGE_SURROGATE_ID]: row[COL_AUTHOR_ID]
        for row in df_messages.iter_rows(named=True)
    }

    return (
        df_message_ngrams.group_by(COL_NGRAM_ID)
        .agg(
            pl.len().alias(COL_NGRAM_TOTAL_REPS),  # count nr. times ngram detected
            pl.col(COL_MESSAGE_SURROGATE_ID)
            .replace_strict(dict_authors_by_message)
            .n_unique()
            .alias(COL_NGRAM_DISTINCT_POSTER_COUNT),
        )
        .filter(pl.col(COL_NGRAM_TOTAL_REPS) > 1)
    )


def _create_summary_table(
    df_ngrams: pl.DataFrame, df_ngram_stats: pl.DataFrame
) -> pl.DataFrame:
    """
    Join n-gram definitions with statistics and sort by frequency.

    Args:
        df_ngrams: DataFrame with ngram_id, ngram_words, ngram_length
        df_ngram_stats: DataFrame with ngram_id, ngram_total_reps, ngram_distinct_poster_count

    Returns:
        Joined and sorted DataFrame
    """
    return df_ngrams.join(df_ngram_stats, on=COL_NGRAM_ID, how="inner").sort(
        [COL_NGRAM_LENGTH, COL_NGRAM_TOTAL_REPS, COL_NGRAM_DISTINCT_POSTER_COUNT],
        descending=True,
    )


def _create_full_report_slice(
    df_ngram_summary_slice: pl.DataFrame,
    df_message_ngrams: pl.DataFrame,
    df_messages: pl.DataFrame,
) -> pl.DataFrame:
    """
    Create detailed report for a slice of n-grams with message details.

    Args:
        df_ngram_summary_slice: Slice of summary DataFrame
        df_message_ngrams: DataFrame with message_surrogate_id and ngram_id
        df_messages: DataFrame with message details

    Returns:
        Detailed report DataFrame with per-user repetition counts, sorted
    """
    return (
        (
            df_ngram_summary_slice.join(df_message_ngrams, on=COL_NGRAM_ID).join(
                df_messages, on=COL_MESSAGE_SURROGATE_ID
            )
        )
        # count how many times a user posted distint ngrams
        .with_columns(
            pl.len()
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
    )


def main(context: SecondaryAnalyzerContext):
    df_message_ngrams = pl.read_parquet(
        context.base.table(OUTPUT_MESSAGE_NGRAMS).parquet_path
    )
    df_ngrams = pl.read_parquet(context.base.table(OUTPUT_NGRAM_DEFS).parquet_path)
    df_messages = pl.read_parquet(context.base.table(OUTPUT_MESSAGE).parquet_path)

    with ProgressReporter("Computing ngram statistics"):
        df_ngram_stats = _compute_ngram_statistics(df_message_ngrams, df_messages)

    with ProgressReporter("Creating the summary table"):
        df_ngram_summary = _create_summary_table(df_ngrams, df_ngram_stats)
        df_ngram_summary.write_parquet(context.output(OUTPUT_NGRAM_STATS).parquet_path)

    df_messages_schema = df_messages.to_arrow().schema
    df_message_ngrams_schema = df_message_ngrams.to_arrow().schema
    df_ngram_summary_schema = df_ngram_summary.to_arrow().schema

    average_cardinality_explosion_factor = df_message_ngrams.height // df_ngrams.height

    with ProgressReporter("Writing full report") as progress:
        with pq.ParquetWriter(
            context.output(OUTPUT_NGRAM_FULL).parquet_path,
            schema=pa.schema(
                [
                    df_message_ngrams_schema.field(COL_NGRAM_ID),
                    df_ngram_summary_schema.field(COL_NGRAM_LENGTH),
                    df_ngram_summary_schema.field(COL_NGRAM_WORDS),
                    df_ngram_summary_schema.field(COL_NGRAM_TOTAL_REPS),
                    df_ngram_summary_schema.field(COL_NGRAM_DISTINCT_POSTER_COUNT),
                    df_messages_schema.field(COL_AUTHOR_ID),
                    pa.field(COL_NGRAM_REPS_PER_USER, pa.int32()),
                    df_messages_schema.field(COL_MESSAGE_SURROGATE_ID),
                    df_messages_schema.field(COL_MESSAGE_ID),
                    df_messages_schema.field(COL_MESSAGE_TEXT),
                    df_messages_schema.field(COL_MESSAGE_TIMESTAMP),
                ]
            ),
        ) as writer:
            report_slice_size = max(1, 100_000 // average_cardinality_explosion_factor)
            report_total_processed = 0
            for df_ngram_summary_slice in df_ngram_summary.iter_slices(
                report_slice_size
            ):
                print(
                    f"Writing report "
                    f"{report_total_processed}/{df_ngram_summary.height}",
                    end="\r",
                )
                report_total_processed += df_ngram_summary_slice.height

                df_output = _create_full_report_slice(
                    df_ngram_summary_slice, df_message_ngrams, df_messages
                )

                writer.write_table(df_output.to_arrow())
                report_total_processed += df_ngram_summary_slice.height
                progress.update(report_total_processed / df_ngram_summary.height)
