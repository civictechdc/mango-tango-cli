import types
from pathlib import Path

from preprocessing.series_semantic import datetime_string, identifier, text_catch_all
from services.tokenizer.basic import TokenizerConfig, tokenize_text
from services.tokenizer.core.types import CaseHandling
from testing import CsvTestData, ParquetTestData, test_primary_analyzer

from .ngrams_base.interface import (
    COL_AUTHOR_ID,
    COL_MESSAGE_ID,
    COL_MESSAGE_TEXT,
    COL_MESSAGE_TIMESTAMP,
    OUTPUT_MESSAGE,
    OUTPUT_MESSAGE_NGRAMS,
    OUTPUT_NGRAM_DEFS,
    interface,
)
from .ngrams_base.main import main, ngrams, serialize_ngram
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
