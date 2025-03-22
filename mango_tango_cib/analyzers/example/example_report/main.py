import polars as pl

from mango_tango_cib.analyzer_interface.context import SecondaryAnalyzerContext


def main(context: SecondaryAnalyzerContext):
    df_character_count = pl.read_parquet(
        # This `character_count` is the output ID from the primary analyzer.
        context.base.table("character_count").parquet_path
    )

    df_export = df_character_count.with_columns(
        # `is_long` is a new column that we are adding to the output.
        pl.col("character_count")
        .gt(100)
        .alias("is_long")
    )

    # Save the output to a parquet file. The output ID comes from the secondary
    # analyzer's interface.
    df_export.write_parquet(context.output("example_report").parquet_path)
