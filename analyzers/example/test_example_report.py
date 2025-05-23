import os

from testing import CsvTestData, test_secondary_analyzer

from .example_report.interface import interface
from .example_report.main import main
from .test_data import test_data_dir


# This example shows you how to test a secondary analyzer.
# It runs on pytest.
def test_example_report():

    # You use this test function.
    test_secondary_analyzer(
        interface,  # You provide the interface ...
        main,  # ... and the analyzer's entry point.
        # This is optional if your secondar analyzer doesn't need reference
        # to the primary analyzer parameters.
        #
        # You're responsible for making sure the analyzer you're testing
        # get the parameters it needs.
        #
        # In this particular case, the value doesn't matter becuase it isn't used
        # by the `example_report` secondary analyzer, but we have an `assert`
        # statement for the parameter's existence just to make a point.
        primary_params={"fudge_factor": 10},
        # A secondary analyzer requires the primary outputs to be provided.
        # All the outputs required by the secondary analyzer being tested
        # must be provided. But not all the primary outputs need to be provided
        # if they aren't used by the secondary analyzer.
        primary_outputs={
            # Here we provide the test data in csv format.
            # Other formats are also supported.
            #
            # See the primary analyzer test example for more information
            # about CsvTestData and others.
            "character_count": CsvTestData(os.path.join(test_data_dir, "output.csv"))
        },
        # These outputs are the expected outputs of the analyzer.
        # You don't need to specify all the outputs, only the ones you want to test.
        # The output IDs must match the IDs in the interface schema.
        # You must provide at least one output (otherwise you're not really testing anything!)
        expected_outputs={
            "example_report": CsvTestData(
                os.path.join(test_data_dir, "output_report.csv")
            )
        },
    )
