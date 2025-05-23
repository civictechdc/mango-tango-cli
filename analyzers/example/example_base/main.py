import polars as pl

from analyzer_interface.context import PrimaryAnalyzerContext
from terminal_tools import ProgressReporter


def main(context: PrimaryAnalyzerContext):
    # To read the user's input data the way the user intended, you have to do
    # two things:
    # - Read the input file, which is a parquet file. The InputReader interface
    #   gives you the path to the file. You can use whichever library
    #   to do this. Here we use polars.
    #
    # - Preprocess the input data. This transforms the user's imported data
    #   to the format that your analyzer expects by performing the column
    #   mapping and data type conversion (like converting a string column
    #   that represents a datetime into a timestamp column).
    #   YOU MUST DO THIS before you can start your analysis, otherwise you won't
    #   get the columns or the types that you need.
    input_reader = context.input()
    df_input = input_reader.preprocess(pl.read_parquet(input_reader.parquet_path))

    # The analysis parameters are provided in a dictionary. This is how you
    # access them. The dictionary key must match the parameter ID in the interface.
    fudge_factor_param = context.params.get("fudge_factor")

    # You don't actually need to do this as the app will make sure all
    # parameters are of the right type. But it's a good idea anyway.
    # It also lets python narrow the type for you.
    assert isinstance(fudge_factor_param, int), "Fudge factor must be an integer"

    # Now you can start your analysis. The following code is just a minimal example.
    #
    # The use of the ProgressReporter is optional. It helps breaking a
    # longer analysis down into sections.
    with ProgressReporter("Counting characters") as progress:
        df_count = df_input.select(
            pl.col("message_id"),
            # The input and output columns are as you define in the interface.
            pl.col("message_text")
            .str.len_chars()
            .add(fudge_factor_param)
            .alias("character_count"),
        )

        # If you decide to process the data in small batches
        # you can update the progress bar with the fraction of the
        # current batch. Again, this is optional. Here we just use
        # 1.0 to indicate 100% completion.
        #
        # You can still use the ProgressReporter without updating the progress
        # value, in which case the progress bar will just show a spinner and
        # the message.
        progress.update(1.0)

    # The analyzer is expected to write the output to a parquet file for
    # every output that is defined. Make sure that the output ID and the
    # columns match the interface.
    df_count.write_parquet(context.output("character_count").parquet_path)
