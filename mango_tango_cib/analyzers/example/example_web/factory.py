import plotly.express as px
import polars as pl
from dash.dcc import Graph
from dash.html import Div

from mango_tango_cib.analyzer_interface.context import WebPresenterContext


def factory(context: WebPresenterContext):
    df = pl.read_parquet(
        # This gives you the path to the primary analyzer's output.
        # The ID is the same as the one you used in the primary analyzer interface.
        context.base.table("character_count").parquet_path
    )

    # For secondary analyzer output, import the secondary analyzer's interface
    # and use an ID from there.
    #
    # Example:
    #
    # from ..example_report import interface as example_report
    #
    # pl.read_parquet(
    #   context.dependency(example_report).table("example_report").parquet_path
    # )

    # This is the Dash app. You can add components to it to build your UI.
    # For a Dash primer, consult the Dash documentation at https://dash.plotly.com/.
    app = context.dash_app

    fig = px.histogram(x=df["character_count"], nbins=50)
    fig.update_layout(
        {
            "xaxis": {
                "title": {"text": "Message Character Count"},
            },
            "yaxis": {
                "title": {"text": "Number of Messages"},
            },
        }
    )

    app.layout = Div(
        [
            Graph(
                figure=fig,
                style={"height": "100%", "flex-grow": "1"},
            )
        ]
    )
