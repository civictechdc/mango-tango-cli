import types
from pathlib import Path

from app.utils import tokenize_text
from preprocessing.series_semantic import datetime_string, identifier, text_catch_all
from testing import CsvTestData, ParquetTestData, test_primary_analyzer

from .ngrams_base.interface import (
    COL_AUTHOR_ID,
    COL_MESSAGE_ID,
    COL_MESSAGE_TEXT,
    COL_MESSAGE_TIMESTAMP,
    OUTPUT_MESSAGE,
    OUTPUT_MESSAGE_NGRAMS,
    OUTPUT_NGRAM_DEFS,
    PARAM_MAX_N,
    PARAM_MIN_N,
    interface,
)
from .ngrams_base.main import _generate_ngrams_simple, _generate_ngrams_vectorized, main
from .test_data import test_data_dir

TEST_CSV_FILENAME = "ngrams_test_input.csv"
TEST_STRING = "Mango tree is an open source project."

# this is expected output of tokenize()
TEST_TOKENIZED_EXPECTED = [
    "mango",  # it's lower cased
    "tree",
    "is",
    "an",
    "open",
    "source",
    "project.",
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
    """Test the new tokenization engine with polars LazyFrame."""
    import polars as pl

    # Create test data in the format expected by tokenize_text
    test_df = pl.DataFrame({"message_text": [TEST_STRING]}).lazy()

    # Apply tokenization
    result_df = tokenize_text(test_df, "message_text").collect()

    # Get the tokens from the result
    test_tokenized_actual = result_df["tokens"][0].to_list()

    assert isinstance(
        test_tokenized_actual, list
    ), "output of tokenize_text() tokens column is not instance of list"

    assert all(
        [
            expected_str == actual_str
            for expected_str, actual_str in zip(
                TEST_TOKENIZED_EXPECTED, test_tokenized_actual
            )
        ]
    ), "Tokenized strings does not match expected tokens."


def test_ngrams():
    """Test n-gram generation using the new vectorized approach."""
    import polars as pl

    from terminal_tools.progress import RichProgressManager

    # Create test data with tokens
    test_df = pl.DataFrame(
        {"message_surrogate_id": [1], "tokens": [TEST_TOKENIZED_EXPECTED]}
    ).lazy()

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
        # Generate n-grams directly (no progress manager needed for testing)
        ngrams_result = _generate_ngrams_vectorized(
            test_df,
            min_n=test_params["min_gram_len"],
            max_n=test_params["max_ngram_len"],
        ).collect()

        # Check the number of n-grams generated
        actual_count = len(ngrams_result)
        expected_count = test_params["n_expected_ngrams_found"]

        assert (
            actual_count == expected_count
        ), f"Nr. expected tokens mismatch for {test_key}: got {actual_count}, expected {expected_count}"


def test_serialize_ngram():
    """Test that n-grams are properly serialized as space-separated strings."""
    import polars as pl

    from terminal_tools.progress import RichProgressManager

    NGRAM_SERIALIZED_EXPECTED_FIRST = "mango tree is an open"

    # Create test data with tokens
    test_df = pl.DataFrame(
        {"message_surrogate_id": [1], "tokens": [TEST_TOKENIZED_EXPECTED]}
    ).lazy()

    # Generate n-grams with min=5, max=8
    ngrams_result = _generate_ngrams_vectorized(test_df, min_n=5, max_n=8).collect()

    # Get the first n-gram (should be the 5-gram starting with "mango")
    first_ngram = ngrams_result["ngram_text"][0]

    assert NGRAM_SERIALIZED_EXPECTED_FIRST == first_ngram


def test_ngram_analyzer():
    """Test the main analyzer with default parameters."""
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


def test_ngram_analyzer_configurable_parameters():
    """Test the analyzer with different min_n and max_n parameters."""
    # Test with different parameter combinations using parameter-specific expected files
    parameter_combinations = [
        ("min1_max3", {PARAM_MIN_N: 1, PARAM_MAX_N: 3}),
        ("min2_max4", {PARAM_MIN_N: 2, PARAM_MAX_N: 4}),
        ("min4_max6", {PARAM_MIN_N: 4, PARAM_MAX_N: 6}),
    ]

    for param_suffix, params in parameter_combinations:
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
                    filepath=str(
                        Path(
                            test_data_dir,
                            f"{OUTPUT_MESSAGE_NGRAMS}_{param_suffix}.parquet",
                        )
                    )
                ),
                OUTPUT_NGRAM_DEFS: ParquetTestData(
                    filepath=str(
                        Path(
                            test_data_dir, f"{OUTPUT_NGRAM_DEFS}_{param_suffix}.parquet"
                        )
                    )
                ),
                OUTPUT_MESSAGE: ParquetTestData(
                    filepath=str(
                        Path(test_data_dir, f"{OUTPUT_MESSAGE}_{param_suffix}.parquet")
                    )
                ),
            },
            params=params,
        )


def test_ngram_generation_edge_cases():
    """Test n-gram generation with edge cases."""
    import polars as pl

    from terminal_tools.progress import RichProgressManager

    # Test with empty data
    empty_df = pl.DataFrame({"message_surrogate_id": [], "tokens": []}).lazy()

    empty_result = _generate_ngrams_vectorized(empty_df, min_n=1, max_n=3).collect()

    assert len(empty_result) == 0, "Empty input should produce empty output"

    # Test with single token (shorter than min_n)
    single_token_df = pl.DataFrame(
        {"message_surrogate_id": [1], "tokens": [["word"]]}
    ).lazy()

    single_result = _generate_ngrams_vectorized(
        single_token_df, min_n=2, max_n=3
    ).collect()

    assert (
        len(single_result) == 0
    ), "Single token with min_n=2 should produce no n-grams"

    # Test with exactly min_n tokens
    exact_tokens_df = pl.DataFrame(
        {"message_surrogate_id": [1], "tokens": [["word1", "word2"]]}
    ).lazy()

    exact_result = _generate_ngrams_vectorized(
        exact_tokens_df, min_n=2, max_n=3
    ).collect()

    assert (
        len(exact_result) == 1
    ), "Two tokens with min_n=2, max_n=3 should produce one 2-gram"
    assert exact_result["ngram_text"][0] == "word1 word2"
