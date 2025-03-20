import os

from preprocessing.series_semantic import datetime_string, identifier, text_catch_all
from testing import CsvTestData, JsonTestData, test_primary_analyzer

from .interface import COL_AUTHOR_ID, COL_HASHTAGS, COL_TIME, OUTPUT_GINI, interface
from .main import main
from .test_data import test_data_dir

breakpoint()


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
            # semantics={
            #    COL_AUTHOR_ID: identifier,
            #    COL_TIME: datetime_string,
            #    COL_HASHTAGS: text_catch_all},
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
