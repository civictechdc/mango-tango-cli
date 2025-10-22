import polars as pl

from analyzer_interface.context import PrimaryAnalyzerContext
from services.tokenizer.basic import TokenizerConfig, tokenize_text
from services.tokenizer.core.types import CaseHandling
from terminal_tools import ProgressReporter

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


def main(context: PrimaryAnalyzerContext):
    # Get parameters with defaults
    parameters = context.params
    min_n_param = parameters.get(PARAM_MIN_N, 3)
    max_n_param = parameters.get(PARAM_MAX_N, 5)
    assert isinstance(min_n_param, int), "min_n parameter must be an integer"
    assert isinstance(max_n_param, int), "max_n parameter must be an integer"
    min_n = min_n_param
    max_n = max_n_param

    # Configure tokenizer for social media text processing
    tokenizer_config = TokenizerConfig(
        case_handling=CaseHandling.LOWERCASE,
        normalize_unicode=True,
        extract_hashtags=True,
        extract_mentions=True,
        include_urls=True,
        min_token_length=1,
    )

    input_reader = context.input()
    df_input = input_reader.preprocess(pl.read_parquet(input_reader.parquet_path))
    with ProgressReporter("Preprocessing messages"):
        df_input = df_input.with_columns(
            (pl.int_range(pl.len()) + 1).alias(COL_MESSAGE_SURROGATE_ID)
        )
        df_input = df_input.filter(
            pl.col(COL_MESSAGE_TEXT).is_not_null()
            & (pl.col(COL_MESSAGE_TEXT) != "")
            & pl.col(COL_AUTHOR_ID).is_not_null()
            & (pl.col(COL_AUTHOR_ID) != "")
        )

    with ProgressReporter("Detecting n-grams") as progress:

        def get_ngram_rows(ngrams_by_id: dict[str, int]):
            nonlocal progress
            num_rows = df_input.height
            current_row = 0
            for row in df_input.iter_rows(named=True):
                tokens = tokenize_text(row[COL_MESSAGE_TEXT], tokenizer_config)

                # Deduplicate n-grams within this message
                # This ensures that if "go go" appears twice in "go go go now",
                # we yield one row with count=2, not two separate rows.
                # This semantically represents: "This n-gram appears N times in this message"
                message_ngrams = {}  # {ngram_id: count}

                for ngram in ngrams(tokens, min_n, max_n):
                    serialized_ngram = serialize_ngram(ngram)
                    if serialized_ngram not in ngrams_by_id:
                        ngrams_by_id[serialized_ngram] = len(ngrams_by_id)
                    ngram_id = ngrams_by_id[serialized_ngram]

                    # Count occurrences of this n-gram within this message
                    message_ngrams[ngram_id] = message_ngrams.get(ngram_id, 0) + 1

                # Yield one row per unique n-gram in this message (with count)
                for ngram_id, count in message_ngrams.items():
                    yield {
                        COL_MESSAGE_SURROGATE_ID: row[COL_MESSAGE_SURROGATE_ID],
                        COL_NGRAM_ID: ngram_id,
                        COL_MESSAGE_NGRAM_COUNT: count,
                    }

                current_row = current_row + 1
                if current_row % 100 == 0:
                    progress.update(current_row / num_rows)

        ngrams_by_id: dict[str, int] = {}
        df_ngram_instances = list(get_ngram_rows(ngrams_by_id))

    # N-gram deduplication is now done in-loop in get_ngram_rows(),
    # so we don't need to group and aggregate here.
    with ProgressReporter("Writing per-message n-gram data"):
        # Handle empty case by providing explicit schema
        if df_ngram_instances:
            (
                pl.DataFrame(df_ngram_instances)
                .sort(by=[COL_MESSAGE_SURROGATE_ID, COL_NGRAM_ID])
                .write_parquet(context.output(OUTPUT_MESSAGE_NGRAMS).parquet_path)
            )
        else:
            # Create empty DataFrame with correct schema
            pl.DataFrame(
                {
                    COL_MESSAGE_SURROGATE_ID: [],
                    COL_NGRAM_ID: [],
                    COL_MESSAGE_NGRAM_COUNT: [],
                },
                schema={
                    COL_MESSAGE_SURROGATE_ID: pl.Int64,
                    COL_NGRAM_ID: pl.Int64,
                    COL_MESSAGE_NGRAM_COUNT: pl.Int64,
                },
            ).write_parquet(context.output(OUTPUT_MESSAGE_NGRAMS).parquet_path)

    with ProgressReporter("Outputting n-gram definitions"):
        # Handle empty case by providing explicit schema
        if ngrams_by_id:
            (
                pl.DataFrame(
                    {
                        COL_NGRAM_ID: list(ngrams_by_id.values()),
                        COL_NGRAM_WORDS: list(ngrams_by_id.keys()),
                    }
                )
                .with_columns(
                    [
                        pl.col(COL_NGRAM_WORDS)
                        .str.split(" ")
                        .list.len()
                        .alias(COL_NGRAM_LENGTH)
                    ]
                )
                .write_parquet(context.output(OUTPUT_NGRAM_DEFS).parquet_path)
            )
        else:
            # Create empty DataFrame with correct schema
            pl.DataFrame(
                {
                    COL_NGRAM_ID: [],
                    COL_NGRAM_WORDS: [],
                    COL_NGRAM_LENGTH: [],
                },
                schema={
                    COL_NGRAM_ID: pl.Int64,
                    COL_NGRAM_WORDS: pl.String,
                    COL_NGRAM_LENGTH: pl.Int64,
                },
            ).write_parquet(context.output(OUTPUT_NGRAM_DEFS).parquet_path)

    with ProgressReporter("Outputting messages"):
        (
            df_input.select(
                [
                    COL_MESSAGE_SURROGATE_ID,
                    COL_MESSAGE_ID,
                    COL_MESSAGE_TEXT,
                    COL_AUTHOR_ID,
                    COL_MESSAGE_TIMESTAMP,
                ]
            ).write_parquet(context.output(OUTPUT_MESSAGE).parquet_path)
        )


def ngrams(tokens: list[str], min: int, max: int):
    """Generate n-grams from list of tokens."""
    for i in range(len(tokens) - min + 1):
        for n in range(min, max + 1):
            if i + n > len(tokens):
                break
            yield tokens[i : i + n]


def serialize_ngram(ngram: list[str]) -> str:
    """Generates a string that uniquely represents an ngram"""
    return " ".join(ngram)
