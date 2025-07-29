import polars as pl
from dash import html
from shiny.ui import nav_panel

from analyzer_interface.context import (
    FactoryOutputContext,
    ShinyContext,
    WebPresenterContext,
)
from app.shiny import page_dependencies

from ..ngram_stats.interface import OUTPUT_NGRAM_FULL, OUTPUT_NGRAM_STATS
from ..ngram_stats.interface import interface as ngram_stats
from .app import _get_app_layout, _set_global_state_vars, server

data_stats = None
data_full = None


def factory(web_context: WebPresenterContext):
    # get secondary output data (for plot)
    df_stats = pl.read_parquet(
        web_context.dependency(ngram_stats).table(OUTPUT_NGRAM_STATS).parquet_path
    )

    # get the full report data (for Data viewer)
    df_full = pl.read_parquet(
        web_context.dependency(ngram_stats).table(OUTPUT_NGRAM_FULL).parquet_path
    )

    # find the different ngram categories in the data
    ngram_choices = df_stats.select(pl.col("n").unique().sort()).to_series().to_list()

    ngram_choices_dict = {i: f"{i}-grams" for i in ngram_choices}

    # make sure this column is categorical (to work for plotly)
    df_stats = df_stats.with_columns(pl.col("n").cast(pl.String))

    # make sure the app has access to these varables
    _set_global_state_vars(df_stats=df_stats, df_full=df_full)

    app_layout = _get_app_layout(ngram_choices_dict=ngram_choices_dict)

    web_context.dash_app.layout = html.Div(
        [
            html.H1("Hashtag Analysis Dashboard"),
            html.Iframe(
                src="http://localhost:8050/shiny",  # Shiny app will run on port 8051
                style={"width": "100%", "height": "800px", "border": "none"},
            ),
        ]
    )

    return FactoryOutputContext(
        shiny=ShinyContext(
            server_handler=server,
            panel=nav_panel(
                "Dashboard",
                page_dependencies,
                app_layout,
            ),
        )
    )
