import os

from preprocessing.series_semantic import identifier
from testing import CsvConfig, CsvTestData, test_primary_analyzer

from .example_base.interface import interface
from .example_base.main import main
from .test_data import test_data_dir


# This example shows you how to test a primary analyzer.
# It runs on pytest.
def test_example_base():

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
            os.path.join(test_data_dir, "input.csv"),
            # Specifying the column semantics are optional, and are optional for
            # each column. It's useful in CsvTestData, ExcelTestData, and
            # JsonTestData if you have data that need to be interpreted into
            # types not directly supported by the file format like timestamp.
            semantics={"message_id": identifier},
            # This is optional; it lets you specify how the CSV file is read.
            # Every field in this is optional, too. These are the defaults.
            csv_config=CsvConfig(
                has_header=True,
                quote_char='"',
                encoding="utf8",
                separator=",",
            ),
        ),
        # This is optional if your analyzer doesn't take parameters.
        # You're responsible for making sure the analyzer you're testing
        # get the parameters it needs.
        params={"fudge_factor": 10},
        # These outputs are the expected outputs of the analyzer.
        # You don't need to specify all the outputs, only the ones you want to test.
        # The output IDs must match the IDs in the interface schema.
        # You must provide at least one output (otherwise you're not really testing anything!)
        outputs={
            "character_count": CsvTestData(os.path.join(test_data_dir, "output.csv"))
        },
    )
