import plotly.express as px
import polars as pl
from dash.dcc import Graph
from dash.html import H2, Div, P
from analyzer_interface.context import WebPresenterContext
from ..temporal.interface import (
    OUTPUT_COL_POST_COUNT,
    OUTPUT_COL_TIME_INTERVAL_END,
    OUTPUT_COL_TIME_INTERVAL_START,
    OUTPUT_TABLE_INTERVAL_COUNT,
)
from ..utils.pop import pop_unnecessary_fields

def factory(context: WebPresenterContext):
    df_interval_count = pl.read_parquet(
        context.base.table(OUTPUT_TABLE_INTERVAL_COUNT).parquet_path
    )

    fig = px.bar(
        x=(
            df_interval_count[OUTPUT_COL_TIME_INTERVAL_START].dt.strftime("%H:%M")
            + "-"
            + df_interval_count[OUTPUT_COL_TIME_INTERVAL_END].dt.strftime("%H:%M")
        ),
        y=df_interval_count[OUTPUT_COL_POST_COUNT],
        orientation="v",
        title=f"Post Count by Time of Day",
        labels={"x": "Time Interval", "y": "Post Count"},
    )

    context.dash_app.layout = Div(
        [
            H2("Time Frequency Analysis"),
            P("The bars indicate the number of posts in each time interval."),
            Graph(id="bar-plot", figure=fig),
        ]
    )

def api_factory(context: WebPresenterContext):
    presenter_model = context.web_presenter.model_dump()
    data_frame = pl.read_parquet(context.base.table(OUTPUT_TABLE_INTERVAL_COUNT).parquet_path)
    presenter_model["figure_type"] = "bar"
    presenter_model["x"] = f"{data_frame[OUTPUT_COL_TIME_INTERVAL_START].dt.strftime("%H:%M")} - {data_frame[OUTPUT_COL_TIME_INTERVAL_END].dt.strftime("%H:%M")}"
    presenter_model["y"] = data_frame[OUTPUT_COL_POST_COUNT]
    presenter_model["axis"] = {
        "x": {
            "label": "Time Interval"
        },
        "y": {
            "label": "Post Count"
        }
    }
    presenter_model["explanation"] = {
        "title": "Time Frequency Analysis",
        "description": "The bars indicate the number of posts in each time interval."
    }

    return pop_unnecessary_fields(presenter_model)