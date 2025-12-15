import polars as pl

from analyzer_interface.context import PrimaryAnalyzerContext
from services.tokenizer.basic import TokenizerConfig, tokenize_text
from services.tokenizer.core.types import CaseHandling
from terminal_tools import ProgressReporter

from .interface import (
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
    PARAM_MAX_N,
    PARAM_MIN_N,
)


def _preprocess_messages(df_input: pl.DataFrame) -> pl.DataFrame:
    """
    Add surrogate IDs and filter invalid messages.

    Args:
        df_input: Raw input dataframe with message data

    Returns:
        Preprocessed dataframe with:
        - message_surrogate_id column added (1-indexed)
        - null/empty message_text filtered out
        - null/empty author_id filtered out
    """
    df_input = df_input.with_columns(
        (pl.int_range(pl.len()) + 1).alias(COL_MESSAGE_SURROGATE_ID)
    )
    df_input = df_input.filter(
        pl.col(COL_MESSAGE_TEXT).is_not_null()
        & (pl.col(COL_MESSAGE_TEXT) != "")
        & pl.col(COL_AUTHOR_ID).is_not_null()
        & (pl.col(COL_AUTHOR_ID) != "")
    )
    return df_input


def _extract_ngrams_from_messages(
    df_input: pl.DataFrame,
    min_n: int,
    max_n: int,
    tokenizer_config: TokenizerConfig,
    progress_callback=None,
) -> tuple[pl.DataFrame, dict[str, int]]:
    """
    Extract n-grams from messages with within-message deduplication.

    Args:
        df_input: Preprocessed dataframe with messages
        min_n: Minimum n-gram length
        max_n: Maximum n-gram length
        tokenizer_config: Configuration for text tokenization
        progress_callback: Optional callback for progress reporting

    Returns:
        Tuple of (df_message_ngrams, ngrams_by_id) where:
        - df_message_ngrams: DataFrame with columns [message_surrogate_id, ngram_id]
        - ngrams_by_id: Dict mapping serialized n-gram strings to n-gram IDs
    """

    def get_ngram_rows(ngrams_by_id: dict[str, int]):
        num_rows = df_input.height
        current_row = 0

        for row in df_input.iter_rows(named=True):
            tokens = tokenize_text(row[COL_MESSAGE_TEXT], tokenizer_config)

            # this will track within message repetitions
            seen_ngrams_in_message = set()

            for ngram in ngrams(tokens, min_n, max_n):
                serialized_ngram = serialize_ngram(ngram)

                # skip repetitions of already detected ngrams
                if serialized_ngram in seen_ngrams_in_message:
                    continue
                seen_ngrams_in_message.add(serialized_ngram)

                # generate ngram ids (by counting)
                if serialized_ngram not in ngrams_by_id:
                    ngrams_by_id[serialized_ngram] = len(ngrams_by_id)
                ngram_id = ngrams_by_id[serialized_ngram]

                yield {
                    COL_MESSAGE_SURROGATE_ID: row[COL_MESSAGE_SURROGATE_ID],
                    COL_NGRAM_ID: ngram_id,
                }
            current_row = current_row + 1
            if current_row % 100 == 0 and progress_callback:
                progress_callback(current_row / num_rows)

    ngrams_by_id: dict[str, int] = {}
    df_ngram_instances = pl.DataFrame(get_ngram_rows(ngrams_by_id))

    return df_ngram_instances, ngrams_by_id


def _create_ngram_definitions(ngrams_by_id: dict[str, int]) -> pl.DataFrame:
    """
    Create n-gram definitions table with IDs, words, and lengths.

    Args:
        ngrams_by_id: Dict mapping serialized n-gram strings to n-gram IDs

    Returns:
        DataFrame with columns [ngram_id, ngram_words, ngram_length]
    """
    return pl.DataFrame(
        {
            COL_NGRAM_ID: list(ngrams_by_id.values()),
            COL_NGRAM_WORDS: list(ngrams_by_id.keys()),
        }
    ).with_columns(
        [pl.col(COL_NGRAM_WORDS).str.split(" ").list.len().alias(COL_NGRAM_LENGTH)]
    )


def main(context: PrimaryAnalyzerContext):
    # Get parameters with defaults
    parameters = context.params
    min_n = parameters.get(PARAM_MIN_N, 3)
    max_n = parameters.get(PARAM_MAX_N, 5)

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
        df_input = _preprocess_messages(df_input)

    with ProgressReporter("Detecting n-grams") as progress:
        df_ngram_instances, ngrams_by_id = _extract_ngrams_from_messages(
            df_input, min_n, max_n, tokenizer_config, progress.update
        )

    with ProgressReporter("Fetching n-gram statistics"):
        (
            pl.DataFrame(df_ngram_instances)
            .sort(by=[COL_MESSAGE_SURROGATE_ID, COL_NGRAM_ID])
            .write_parquet(context.output(OUTPUT_MESSAGE_NGRAMS).parquet_path)
        )

    with ProgressReporter("Outputting n-gram definitions"):
        df_ngram_defs = _create_ngram_definitions(ngrams_by_id)
        df_ngram_defs.write_parquet(context.output(OUTPUT_NGRAM_DEFS).parquet_path)

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
