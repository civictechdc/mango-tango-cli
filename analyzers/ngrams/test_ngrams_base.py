import types
from pathlib import Path

import polars as pl
import pytest

from preprocessing.series_semantic import datetime_string, identifier, text_catch_all
from services.tokenizer.basic import TokenizerConfig, tokenize_text
from services.tokenizer.core.types import CaseHandling
from testing import CsvTestData, ParquetTestData, test_primary_analyzer

from .ngrams_base.interface import (
    COL_AUTHOR_ID,
    COL_MESSAGE_ID,
    COL_MESSAGE_SURROGATE_ID,
    COL_MESSAGE_TEXT,
    COL_MESSAGE_TIMESTAMP,
    OUTPUT_MESSAGE,
    OUTPUT_MESSAGE_NGRAMS,
    OUTPUT_NGRAM_DEFS,
    interface,
)
from .ngrams_base.main import (
    _create_ngram_definitions,
    _extract_ngrams_from_messages,
    _preprocess_messages,
    main,
    ngrams,
    serialize_ngram,
)
from .test_data import test_data_dir

TEST_CSV_FILENAME = "ngrams_test_input.csv"
TEST_STRING = "Mango tree is an open source project."

# this is expected output of tokenize_text() with new tokenizer service
TEST_TOKENIZED_EXPECTED = [
    "mango",  # it's lower cased
    "tree",
    "is",
    "an",
    "open",
    "source",
    "project",  # punctuation is now separated - better for n-gram analysis
]

NGRAMS_EXPECTED_min1_max3 = [
    ["mango"],
    ["mango", "tree"],
    ["mango", "tree", "is"],
    ["tree"],
    ["tree", "is"],
    ["tree", "is", "an"],
    ["is"],
    ["is", "an"],
    ["is", "an", "open"],
    ["an"],
    ["an", "open"],
    ["an", "open", "source"],
    ["open"],
    ["open", "source"],
    ["open", "source", "project"],
    ["source"],
    ["source", "project"],
    ["project"],
]

NGRAMS_EXPECTED_min5_max7 = [
    ["mango", "tree", "is", "an", "open"],
    ["mango", "tree", "is", "an", "open", "source"],
    ["mango", "tree", "is", "an", "open", "source", "project"],
    ["tree", "is", "an", "open", "source"],
    ["tree", "is", "an", "open", "source", "project"],
    ["is", "an", "open", "source", "project"],
]

# if max ngram len is not found, it just returns all the shortest ngrams
NGRAMS_EXPECTED_min5_max8 = [
    ["mango", "tree", "is", "an", "open"],
    ["mango", "tree", "is", "an", "open", "source"],
    ["mango", "tree", "is", "an", "open", "source", "project"],
    ["tree", "is", "an", "open", "source"],
    ["tree", "is", "an", "open", "source", "project"],
    ["is", "an", "open", "source", "project"],
]


def test_tokenize():
    # Configure tokenizer for clean word extraction (no social media entities)
    config = TokenizerConfig(
        case_handling=CaseHandling.LOWERCASE,
        normalize_unicode=True,
        extract_hashtags=False,
        extract_mentions=False,
        include_urls=False,
        min_token_length=1,
    )
    test_tokenized_actual = tokenize_text(TEST_STRING, config)

    assert isinstance(
        test_tokenized_actual, list
    ), "output of tokenize_text() is not an instance of list"

    assert (
        test_tokenized_actual == TEST_TOKENIZED_EXPECTED
    ), "Tokenized strings do not match expected tokens."

    pass


def test_ngrams():
    # Configure tokenizer for clean word extraction (no social media entities)
    config = TokenizerConfig(
        case_handling=CaseHandling.LOWERCASE,
        normalize_unicode=True,
        extract_hashtags=False,
        extract_mentions=False,
        include_urls=False,
        min_token_length=1,
    )
    test_string_tokenized = tokenize_text(TEST_STRING, config)

    test_combinations = {
        "min1_max3": {
            "min_gram_len": 1,
            "max_ngram_len": 3,
            "n_expected_ngrams_found": 18,
        },
        "min5_max7": {
            "min_gram_len": 5,
            "max_ngram_len": 7,
            "n_expected_ngrams_found": 6,
        },
        "min5_max8": {
            "min_gram_len": 5,
            "max_ngram_len": 8,
            "n_expected_ngrams_found": 6,
        },
    }

    for test_key, test_params in test_combinations.items():
        ngrams_actual = ngrams(
            test_string_tokenized,
            min=test_params["min_gram_len"],
            max=test_params["max_ngram_len"],
        )

        assert isinstance(ngrams_actual, types.GeneratorType)
        assert (
            len(list(ngrams_actual)) == test_params["n_expected_ngrams_found"]
        ), f"Nr. expected tokens mismatch for {test_key}"


def test_serialize_ngram():
    NGRAM_SERIALIZED_EXPECTED_FIRST = "mango tree is an open"

    # Configure tokenizer for clean word extraction
    config = TokenizerConfig(
        case_handling=CaseHandling.LOWERCASE,
        normalize_unicode=True,
        extract_hashtags=False,
        extract_mentions=False,
        include_urls=False,
        min_token_length=1,
    )
    test_ngrams = list(ngrams(tokenize_text(TEST_STRING, config), min=5, max=8))

    test_ngram_serialized_actual = serialize_ngram(test_ngrams[0])

    assert NGRAM_SERIALIZED_EXPECTED_FIRST == test_ngram_serialized_actual


# Fixtures for unit testing


@pytest.fixture
def df_raw_input():
    """Load raw CSV test input"""
    return pl.read_csv(Path(test_data_dir, TEST_CSV_FILENAME))


@pytest.fixture
def tokenizer_config_fixture():
    """Standard tokenizer config for n-gram analysis"""
    return TokenizerConfig(
        case_handling=CaseHandling.LOWERCASE,
        normalize_unicode=True,
        extract_hashtags=True,
        extract_mentions=True,
        include_urls=True,
        min_token_length=1,
    )


@pytest.fixture
def expected_message_ngrams():
    """Load expected message_ngrams output"""
    return pl.read_parquet(Path(test_data_dir, "message_ngrams.parquet"))


@pytest.fixture
def expected_ngram_defs():
    """Load expected ngram definitions output"""
    return pl.read_parquet(Path(test_data_dir, "ngrams.parquet"))


@pytest.fixture
def expected_messages():
    """Load expected message authors output"""
    return pl.read_parquet(Path(test_data_dir, "message_authors.parquet"))


# Unit tests for extracted functions


def test_preprocess_messages(df_raw_input):
    """Test message preprocessing and filtering"""
    result = _preprocess_messages(df_raw_input)

    # Assert surrogate IDs added and 3 messages were indexed
    assert COL_MESSAGE_SURROGATE_ID in result.columns
    assert result[COL_MESSAGE_SURROGATE_ID].unique().to_list() == [
        1,
        2,
        3,
    ], "Message surrogate ID column not matching expected values"

    # Assert no null/empty messages or authors
    assert result[COL_MESSAGE_TEXT].null_count() == 0
    assert result[COL_AUTHOR_ID].null_count() == 0


def test_extract_ngrams_from_messages(df_raw_input, tokenizer_config_fixture):
    """Test n-gram extraction with within-message deduplication"""
    df_preprocessed = _preprocess_messages(df_raw_input)
    df_message_ngrams, ngrams_by_id = _extract_ngrams_from_messages(
        df_preprocessed, min_n=3, max_n=4, tokenizer_config=tokenizer_config_fixture
    )

    # Check "go go go" appears 3 times (once per message)
    go_ngram_id = ngrams_by_id["go go go"]
    go_count = df_message_ngrams.filter(pl.col("ngram_id") == go_ngram_id).height
    assert go_count == 3, "go go go should appear in all 3 messages"

    # Check "it's very bad" appears 2 times (msg_002, msg_003)
    # Even though msg_003 has it twice, within-message dedup should keep only 1
    bad_ngram_id = ngrams_by_id["it's very bad"]
    bad_count = df_message_ngrams.filter(pl.col("ngram_id") == bad_ngram_id).height
    assert bad_count == 2, "it's very bad should appear in 2 messages (deduplicated)"

    # Check total unique n-grams detected
    assert len(ngrams_by_id) > 2, "Should detect multiple unique n-grams"


def test_create_ngram_definitions():
    """Test n-gram definition table creation"""
    mock_ngrams = {
        "go go go": 0,
        "it's very bad": 1,
        "go it's very": 2,
    }

    result = _create_ngram_definitions(mock_ngrams)

    # Check structure
    assert "ngram_id" in result.columns
    assert "words" in result.columns
    assert "n" in result.columns
    assert result.height == 3

    # Check n-gram lengths calculated correctly
    assert result.filter(pl.col("ngram_id") == 0)["n"][0] == 3
    assert result.filter(pl.col("ngram_id") == 1)["n"][0] == 3


# Integration test
def test_ngram_analyzer():
    test_primary_analyzer(
        interface=interface,
        main=main,
        input=CsvTestData(
            filepath=str(Path(test_data_dir, TEST_CSV_FILENAME)),
            semantics={
                COL_AUTHOR_ID: identifier,
                COL_MESSAGE_ID: identifier,
                COL_MESSAGE_TEXT: text_catch_all,
                COL_MESSAGE_TIMESTAMP: datetime_string,
            },
        ),
        params={"min_n": 3, "max_n": 4},
        outputs={
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
    )
