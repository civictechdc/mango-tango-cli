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


def gini(x):
    """
    Parameters
    ----------
    x : list[str]
        List of values for which to compute the Gini coefficient

    Returns
    -------
    float
        Gini coefficient
    """
    x_counts = Counter(x).values()

    sorted_x = sorted(x_counts)
    n = len(sorted_x)
    cumx = list(accumulate(sorted_x))

    return (n + 1 - 2 * sum(cumx) / cumx[-1]) / n


def hashtag_analysis(data_frame:pl.DataFrame, every="1h") -> pl.DataFrame:

    has_hashtag_symbol = pl.col(COL_HASHTAGS).str.contains("#").any()
    extract_hashtags = pl.col(COL_HASHTAGS).str.extract_all(r'(#\S+)')
    extract_hashtags_by_split = (
        pl.col(COL_HASHTAGS)
        .str.strip_chars("[]")
        .str.replace_all("'", "")
        .str.replace_all(" ", "")
        .str.split(",")
        )

    # assign None to messages with no hashtags
    if data_frame.select(has_hashtag_symbol).item():
        df_input = (
            data_frame
            .with_columns(extract_hashtags)
            .filter(pl.col(COL_HASHTAGS) != [])
        )
    else:
        df_input = (
            data_frame
            .filter(pl.col(COL_HASHTAGS) == '[]')
            .with_columns(extract_hashtags_by_split)
        )

    # select columns
    df_input = df_input.select(pl.col(COLS_ALL))

    breakpoint()

    df_agg = (
        df_input.drop_nulls(pl.col(COL_HASHTAGS))
        .select(
            pl.col(COL_TIME),
            pl.col(COL_HASHTAGS),
        )
        .sort(COL_TIME)
        .group_by_dynamic(COL_TIME, every=every)  # this could be a parameter
        .agg(
            pl.col(COL_HASHTAGS).explode().alias(OUTPUT_COL_HASHTAGS),
            pl.col(COL_HASHTAGS).explode().count().alias(OUTPUT_COL_COUNT),
            pl.col(COL_HASHTAGS)
            .explode()
            .map_elements(
                lambda x: gini(x.to_list()),
                return_dtype=pl.Float32,
                returns_scalar=True,
            )
            .alias(OUTPUT_COL_GINI),
        )
    )

    return df_agg

def main(context: PrimaryAnalyzerContext):

    input_reader = context.input()
    df_input = input_reader.preprocess(pl.read_parquet(input_reader.parquet_path))

    df_agg = hashtag_analysis(
        data_frame=df_input,
    )

    df_agg.write_parquet(context.output(OUTPUT_GINI).parquet_path)
