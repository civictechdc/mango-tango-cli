from itertools import accumulate

import polars as pl

from analyzer_interface.context import PrimaryAnalyzerContext
from terminal_tools import ProgressReporter

from .interface import (
    COL_AUTHOR_ID,
    COL_POST,
    COL_TIME,
    OUTPUT_COL_COUNT,
    OUTPUT_COL_GINI,
    OUTPUT_COL_HASHTAGS,
    OUTPUT_COL_TIMESPAN,
    OUTPUT_COL_USERS,
    OUTPUT_GINI,
    PARAM_TIME_WINDOW,
)

SMOOTH_WINDOW_SIZE = 3


def gini(x: pl.Series) -> float:
    """
    Parameters
    ----------
    x : pl.Series
        polars Series containing values for which to compute the Gini coefficient

    Returns
    -------
    float
        Gini coefficient (between 0.0 and 1.0)
    """
    sorted_x = x.value_counts().sort(by="count", descending=False)[:, 1].to_list()

    n = len(sorted_x)
    cumx = list(accumulate(sorted_x))

    return (n + 1 - 2 * sum(cumx) / cumx[-1]) / n


def hashtag_analysis(data_frame: pl.DataFrame, every="1h") -> pl.DataFrame:
    if not isinstance(data_frame.schema[COL_TIME], pl.Datetime):
        data_frame = data_frame.with_columns(
            pl.col(COL_TIME).str.to_datetime().alias(COL_TIME)
        )

    # define the expressions
    has_hashtag_symbols = (
        pl.col(COL_POST).str.contains("#").any()
    )  # find posts containing hasthag symbols
    extract_hashtags = pl.col(COL_POST).str.extract_all(
        r"(#\S+)"
    )  # fetch all hashtags based on `#` symbol

    with ProgressReporter("Gathering hashtags..."):
        # if hashtag symbol is detected, extract with regex
        if data_frame.select(has_hashtag_symbols).item():
            df_input = data_frame.with_columns(extract_hashtags).filter(
                pl.col(COL_POST) != []
            )

        else:  # otherwise, we assume str: "['hashtag1', 'hashtag2', ...]"
            raise ValueError(
                f"The data in {COL_POST} column appear to have no hashtags."
            )

    # select columns and sort by time in ascending order
    # (expected by .group_by_dynamic below)
    df_input = df_input.select(pl.col([COL_AUTHOR_ID, COL_TIME, COL_POST])).sort(
        pl.col(COL_TIME)
    )

    with ProgressReporter("Counting hashtags..."):
        # compute gini per timewindow
        df_out = (
            df_input.explode(pl.col(COL_POST))
            .group_by_dynamic(
                pl.col(COL_TIME), every=every, period=every, start_by="datapoint"
            )
            .agg(
                pl.col(COL_AUTHOR_ID).alias(OUTPUT_COL_USERS),
                pl.col(COL_POST).alias(OUTPUT_COL_HASHTAGS),
                pl.col(COL_POST).count().alias(OUTPUT_COL_COUNT),
                pl.col(COL_POST)
                .map_batches(gini, returns_scalar=True, return_dtype=pl.Float64)
                .alias(OUTPUT_COL_GINI),
            )
            .with_columns(
                pl.col(OUTPUT_COL_GINI)
                .rolling_mean(window_size=SMOOTH_WINDOW_SIZE, center=True)
                .alias(OUTPUT_COL_GINI + "_smooth")
            )
            .rename({COL_TIME: OUTPUT_COL_TIMESPAN})
        )

    # convert datetime back to string
    df_out = df_out.with_columns(
        pl.col(OUTPUT_COL_TIMESPAN).dt.to_string("%Y-%m-%d %H:%M:%S")
    )

    return df_out


def main(context: PrimaryAnalyzerContext):
    input_reader = context.input()
    df_input = input_reader.preprocess(pl.read_parquet(input_reader.parquet_path))

    time_window_param = context.params.get(PARAM_TIME_WINDOW)

    # window hard-coded to 1hr for now
    df_out = hashtag_analysis(
        data_frame=df_input,
        every=time_window_param.to_polars_truncate_spec(),  # returns '12h', '5d' etc.
    )

    df_out.write_parquet(context.output(OUTPUT_GINI).parquet_path)
