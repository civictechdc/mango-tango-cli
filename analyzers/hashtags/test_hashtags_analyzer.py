import os

import numpy as np
import polars as pl

from preprocessing.series_semantic import datetime_string, identifier, text_catch_all
from testing import CsvTestData, JsonTestData, test_primary_analyzer

from .interface import COL_AUTHOR_ID, COL_POST, COL_TIME, OUTPUT_GINI, interface
from .main import gini, main
from .test_data import test_data_dir

HASHTAGS = [
    "sunset",
    "nature",
    "food",
    "travel",
    "happy",
    "friends",
    "love",
    "family",
    "music",
    "art",
    "photography",
    "fun",
    "smile",
    "weekend",
    "coffee",
    "book",
    "reading",
    "running",
    "fitness",
    "health",
    "cat",
    "dog",
    "bird",
    "fish",
    "lizard",
]


def test_gini():
    test_cases = [
        # a single hashtags is detected
        {
            "data": ["same"] * 1000,
            "expected": 0.0,
            "description": "One single hashtag (no inequality possible)",
        },
        {
            "data": HASHTAGS,
            "expected": 0.0,
            "description": "Perfect equality (all unique)",
        },
        {
            "data": HASHTAGS * 5,
            "expected": 0.0,
            "description": "Perfect equality (all appear 5 times)",
        },
        {
            "data": ["trending"] * 9999 + HASHTAGS,
            "expected": 0.95,  # It goes towards 1
            "description": "Extreme inequality (9999 vs 1 occurrences)",
        },
    ]

    # caculcate gini and compare
    for test_case in test_cases:
        data_series = pl.Series(test_case["data"])

        # Calculate actual Gini coefficient
        actual = gini(data_series)

        assert np.allclose(
            [actual], [test_case["expected"]], rtol=1e-2, atol=1e-2
        ), f"Failed test case: {test_case['description']}"


# This example shows you how to test a primary analyzer.
# It runs on pytest.
def test_hashtag_analyzer():
    # You use this test function.
    test_primary_analyzer(
        interface,  # You provide the interface ...
        main,  # ... and the analyzer's entry point.
        # There are also JsonTestData, ExcelTestData.
        # You can also programmatically create a polars DataFrame
        # and use PolarsTestData.
        # The column names for the input and output data must match the
        # interface schema.
        input=CsvTestData(
            os.path.join(test_data_dir, "hashtag_test_input.csv"),
            # Specifying the column semantics are optional, and are optional for
            # each column. It's useful in CsvTestData, ExcelTestData, and
            # JsonTestData if you have data that need to be interpreted into
            # types not directly supported by the file format like timestamp.
            semantics={
                COL_AUTHOR_ID: identifier,
                COL_TIME: datetime_string,
                COL_POST: text_catch_all,
            },
        ),
        # These outputs are the expected outputs of the analyzer.
        # You don't need to specify all the outputs, only the ones you want to test.
        # The output IDs must match the IDs in the interface schema.
        # You must provide at least one output (otherwise you're not really testing anything!)
        outputs={
            OUTPUT_GINI: JsonTestData(
                os.path.join(test_data_dir, "hashtag_test_output.json")
            )
        },
    )
