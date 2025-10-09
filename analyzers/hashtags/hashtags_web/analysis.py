import polars as pl

from ..hashtags_base.interface import OUTPUT_COL_HASHTAGS, OUTPUT_COL_USERS


def secondary_analyzer(primary_output, timewindow):
    dataframe_single_timewindow = primary_output.filter(
        pl.col("timewindow_start") == timewindow
    )

    secondary_output = (
        dataframe_single_timewindow.explode(
            [OUTPUT_COL_HASHTAGS, OUTPUT_COL_USERS]
        )  # make eash hashtag and user a separate row
        .with_columns(
            n_hashtags=pl.col(OUTPUT_COL_HASHTAGS).len()
        )  # column with number of hashtags
        .group_by(
            pl.col(OUTPUT_COL_HASHTAGS)
        )  # for each hashtag, compute the folllowing
        .agg(
            users_all=pl.col(OUTPUT_COL_USERS),
            users_unique=pl.col(OUTPUT_COL_USERS).unique(),
            hashtag_perc=(
                pl.col(OUTPUT_COL_HASHTAGS).count() / pl.col("n_hashtags").first()
            )
            * 100,
        )
        .sort(by="hashtag_perc", descending=True)
        .with_columns(
            pl.col("hashtag_perc").round(2),
        )
    )

    return secondary_output
