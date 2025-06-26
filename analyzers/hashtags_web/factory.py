import polars as pl
from dash import html

from analyzer_interface.context import WebPresenterContext

from ..hashtags.interface import COL_AUTHOR_ID, COL_POST, COL_TIME, OUTPUT_GINI


def factory(
    web_context: WebPresenterContext,
):
    # Load the primary output associated with this project
    df_hashtags = pl.read_parquet(web_context.base.table(OUTPUT_GINI).parquet_path)

    # load the raw input data used for this project
    project_id = web_context.base.analysis.project_id
    df_raw = web_context.store.load_project_input(project_id)

    # flip mapping to point from raw data to analyzer input schema
    column_mapping_inv = {
        v: k for k, v in web_context.base.analysis.column_mapping.items()
    }
    df_raw = df_raw.rename(mapping=column_mapping_inv)

    if not isinstance(df_raw.schema[COL_TIME], pl.Datetime):
        df_raw = df_raw.with_columns(pl.col(COL_TIME).str.to_datetime().alias(COL_TIME))

    df_raw = df_raw.select(pl.col([COL_AUTHOR_ID, COL_TIME, COL_POST])).sort(
        pl.col(COL_TIME)
    )

    web_context.dash_app.layout = html.Div(
        [
            html.H1("Hashtag Analysis Dashboard"),
            html.Iframe(
                src="http://localhost:8050/shiny",  # Shiny app will run on port 8051
                style={"width": "100%", "height": "800px", "border": "none"},
            ),
        ]
    )

    return dict(raw_dataframe=df_raw, hashtags_dataframe=df_hashtags)
