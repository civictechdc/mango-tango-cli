from json import loads

import plotly.express as px
import polars as pl
from dash.dcc import Graph
from dash.html import Div

from analyzer_interface.context import WebPresenterContext

from ...utils.pop import pop_unnecessary_fields


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

    fudge_factor_param = context.base_params.get("fudge_factor")
    app.layout = Div(
        [
            Div(f"Fudge factor: {fudge_factor_param}"),
            Div("You naughty data scientist") if fudge_factor_param else None,
            Graph(
                figure=fig,
                style={"height": "100%", "flex-grow": "1"},
            ),
        ]
    )


def api_factory(context: WebPresenterContext):
    presenter_model = context.web_presenter.model_dump()
    data_frame = pl.read_parquet(context.base.table("character_count").parquet_path)
    presenter_model["figure_type"] = "histogram"
    presenter_model["x"] = data_frame["character_count"].to_list()
    presenter_model["axis"] = {
        "x": {"label": "Message Character Count", "value": "message_character_count"},
        "y": {"label": "Number of Messages", "value": "number_of_messages"},
    }

    return pop_unnecessary_fields(presenter_model)
