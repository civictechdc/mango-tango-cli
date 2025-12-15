from pathlib import Path

import polars as pl
import pytest

from testing import ParquetTestData, test_secondary_analyzer

from .ngrams_base.interface import (
    OUTPUT_MESSAGE,
    OUTPUT_MESSAGE_NGRAMS,
    OUTPUT_NGRAM_DEFS,
)
from .ngrams_stats.interface import OUTPUT_NGRAM_FULL, OUTPUT_NGRAM_STATS, interface
from .ngrams_stats.main import _compute_ngram_statistics, main
from .test_data import test_data_dir


# Fixtures for unit testing
@pytest.fixture
def df_message_ngrams():
    """Load message_ngrams (output from ngrams_base)"""
    return pl.read_parquet(Path(test_data_dir, "message_ngrams.parquet"))


@pytest.fixture
def df_ngrams():
    """Load n-gram definitions (output from ngrams_base)"""
    return pl.read_parquet(Path(test_data_dir, "ngrams.parquet"))


@pytest.fixture
def df_messages():
    """Load message authors table (output from ngrams_base)"""
    return pl.read_parquet(Path(test_data_dir, "message_authors.parquet"))


# Unit tests for extracted functions
def test_compute_ngram_statistics(df_message_ngrams, df_messages, df_ngrams):
    """Test basic n-gram statistics computation"""
    result = _compute_ngram_statistics(df_message_ngrams, df_messages)

    # Check all n-grams have total_reps > 1
    assert result["total_reps"].min() > 1, "Single-occurrence n-grams not filtered"

    # Check that only 1 occurs 3 times ("go go go")
    assert result["total_reps"].max() == 3, "Max repetitions for 'go go go' is not 3"

    assert result["distinct_posters"].max() == 2, "Wrong number of distinct posters"

    # Verify we have the expected columns
    assert "ngram_id" in result.columns
    assert "total_reps" in result.columns
    assert "distinct_posters" in result.columns

    # Find the ngram_id with max total_reps and verify it's "go go go"
    max_reps_row = result.filter(pl.col("total_reps") == result["total_reps"].max())
    max_ngram_id = max_reps_row[0, "ngram_id"]

    # Look up the ngram string from df_ngrams
    ngram_string = df_ngrams.filter(pl.col("ngram_id") == max_ngram_id)[0, "words"]
    assert ngram_string == "go go go", f"Expected 'go go go' but got '{ngram_string}'"

    # Find "it's very bad" in df_ngrams and verify it's counted exactly twice
    # That is, one repetition within message is ignored
    its_very_bad_row = df_ngrams.filter(pl.col("words") == "it's very bad")
    its_very_bad_id = its_very_bad_row[0, "ngram_id"]

    # Look up its stats in result
    its_very_bad_stats = result.filter(pl.col("ngram_id") == its_very_bad_id)
    assert its_very_bad_stats.height == 1, "'it's very bad' should be in stats"
    assert (
        its_very_bad_stats[0, "total_reps"] == 2
    ), "'it's very bad' should appear exactly 2 times (deduplicated)"


# Integration test
def test_ngram_stats():
    # You use this test function.
    test_secondary_analyzer(
        interface,
        main,
        primary_outputs={
            OUTPUT_MESSAGE_NGRAMS: ParquetTestData(
                filepath=str(Path(test_data_dir, OUTPUT_MESSAGE_NGRAMS + ".parquet"))
            ),
            OUTPUT_NGRAM_DEFS: ParquetTestData(
                filepath=str(Path(test_data_dir, OUTPUT_NGRAM_DEFS + ".parquet"))
            ),
            OUTPUT_MESSAGE: ParquetTestData(
                filepath=str(Path(test_data_dir, OUTPUT_MESSAGE + ".parquet"))
            ),
        },
        expected_outputs={
            OUTPUT_NGRAM_STATS: ParquetTestData(
                str(Path(test_data_dir, OUTPUT_NGRAM_STATS + ".parquet"))
            ),
            OUTPUT_NGRAM_FULL: ParquetTestData(
                str(Path(test_data_dir, OUTPUT_NGRAM_FULL + ".parquet"))
            ),
        },
    )
