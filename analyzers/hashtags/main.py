from collections import Counter
from itertools import accumulate

import polars as pl

from analyzer_interface.context import PrimaryAnalyzerContext

from .interface import (
    COL_AUTHOR_ID,
    COL_HASHTAGS,
    COL_TIME,
    OUTPUT_COL_COUNT,
    OUTPUT_COL_GINI,
    OUTPUT_COL_HASHTAGS,
    OUTPUT_GINI,
)

# let's look at the hashtags column
COLS_ALL = [COL_AUTHOR_ID, COL_TIME, COL_HASHTAGS]

NULL_CHAR = "[]"  # this is taken as the null character for hashtags


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
    sorted_x = (
        x.value_counts()
        .sort(by="count", descending=False)[:, 1].to_list()
    )

    n = len(sorted_x)
    cumx = list(accumulate(sorted_x))

    return (n + 1 - 2 * sum(cumx) / cumx[-1]) / n


def hashtag_analysis(data_frame:pl.DataFrame, every="1h") -> pl.DataFrame:

    # define the expressions
    has_hashtag_symbol = pl.col(COL_HASHTAGS).str.contains("#").any()
    extract_hashtags = pl.col(COL_HASHTAGS).str.extract_all(r'(#\S+)')
    extract_hashtags_by_split = (
        pl.col(COL_HASHTAGS)
        .str.strip_chars("[]")
        .str.replace_all("'", "")
        .str.replace_all(" ", "")
        .str.split(",")
        )

    # if hashtag symbol is detected, extract with regex
    if data_frame.select(has_hashtag_symbol).item():
        df_input = (
            data_frame
            .with_columns(extract_hashtags)
            .filter(pl.col(COL_HASHTAGS) != [])
        )
    else: # otherwise, we assume str: "['hashtag1', 'hashtag2', ...]"
        df_input = (
            data_frame
            .filter(pl.col(COL_HASHTAGS) != '[]')
            .with_columns(extract_hashtags_by_split)
        )

    # select columns and sort
    df_input = (
        df_input
        .select(pl.col(COLS_ALL))
        .sort(pl.col(COL_TIME))
    )

    df_out = (
        df_input
        .explode(pl.col(COL_HASHTAGS))
        .with_columns(
            window_start = pl.col(COL_TIME).dt.truncate(every)
        )
        .group_by("window_start").agg(
            users = pl.col(COL_AUTHOR_ID),
            hashtags = pl.col(COL_HASHTAGS),
            count = pl.col(COL_HASHTAGS).count(),
            gini = pl.col(COL_HASHTAGS)
            .map_batches(
                gini, returns_scalar=True
            )
        )
    )

    return df_out

def main(context: PrimaryAnalyzerContext):

    input_reader = context.input()
    df_input = input_reader.preprocess(pl.read_parquet(input_reader.parquet_path))

    df_agg = hashtag_analysis(
        data_frame=df_input,
    )

    df_agg.write_parquet(context.output(OUTPUT_GINI).parquet_path)
