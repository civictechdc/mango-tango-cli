from typing import Any, Optional, Union

import plotly.express as px
import plotly.graph_objects as go
import polars as pl
from dash import Input as DashInput
from dash import Output
from dash.dcc import Graph
from dash.dcc import Input as DccInput
from dash.dcc import RadioItems
from dash.html import H2, Datalist, Div, Em, Label, Option, P

from analyzer_interface.context import WebPresenterContext

from ..ngram_stats.interface import (
    COL_AUTHOR_ID,
    COL_MESSAGE_SURROGATE_ID,
    COL_MESSAGE_TEXT,
    COL_MESSAGE_TIMESTAMP,
    COL_NGRAM_DISTINCT_POSTER_COUNT,
    COL_NGRAM_ID,
    COL_NGRAM_LENGTH,
    COL_NGRAM_REPS_PER_USER,
    COL_NGRAM_TOTAL_REPS,
    COL_NGRAM_WORDS,
    OUTPUT_NGRAM_FULL,
    OUTPUT_NGRAM_STATS,
)
from ..ngram_stats.interface import interface as ngram_stats
from ..utils.matcher import create_word_matcher
from ..utils.pop import pop_unnecessary_fields


def factory(context: WebPresenterContext):
    df = pl.read_parquet(
        context.dependency(ngram_stats).table(OUTPUT_NGRAM_STATS).parquet_path
    )
    all_grams = sorted(set(df[COL_NGRAM_WORDS].str.split(" ").explode()))
    explanation_total = "N-grams to the right are repeated by more users. N-grams higher up are repeated more times overall."
    explanation_amplification = "N-grams to the right are repeated by more users. N-grams higher up are repeated more times on average per user."

    @context.dash_app.callback(
        [Output("scatter-plot", "figure"), Output("explanation", "children")],
        [DashInput("grams-list-input", "value"), DashInput("y-axis", "value")],
    )
    def update_figure(filter_text: Optional[str], y_axis: str):
        y_label = (
            "Total Repetition"
            if y_axis == "total_repetition"
            else "Amplification Factor"
        )
        y_legend_label = (
            "Avg Repetitions Per User"
            if y_axis == "amplification_factor"
            else "Total Repetition (All Users)"
        )
        explanation = (
            explanation_total
            if y_axis == "total_repetition"
            else explanation_amplification
        )

        matcher = create_word_matcher(filter_text or "", pl.col(COL_NGRAM_WORDS))
        plotted_df = df.filter(matcher) if matcher is not None else df
        if plotted_df.height == 0:
            fig = go.Figure()
            fig.update_layout(
                xaxis_title="User Count",
                yaxis_title=y_label,
                annotations=[
                    {
                        "text": "No matching n-grams found",
                        "x": 0.5,
                        "y": 0.5,
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                    }
                ],
            )
            return fig, explanation

        x_value = plotted_df[COL_NGRAM_DISTINCT_POSTER_COUNT]
        y_value = (
            plotted_df[COL_NGRAM_TOTAL_REPS]
            if y_axis == "total_repetition"
            else plotted_df[COL_NGRAM_TOTAL_REPS]
            / plotted_df[COL_NGRAM_DISTINCT_POSTER_COUNT]
        )

        fig = px.scatter(
            x=x_value,
            y=y_value,
            labels={"x": "User Count", "y": y_label},
            log_y=True,
            log_x=True,
        )

        fig.update_traces(
            hovertemplate='<b>"%{customdata}"</b><br>'
            + "User Count: %{x}<br>"
            + y_legend_label
            + ": %{y}<br>"
            + "<extra></extra>",
            customdata=plotted_df[COL_NGRAM_WORDS],
        )

        return fig, explanation

    fig = update_figure(None, "total_repetition")

    context.dash_app.layout = Div(
        style={"display": "flex", "flex-direction": "column", "height": "100%"},
        children=[
            Div(
                [
                    H2("N-gram repetition statistics"),
                    P(
                        [
                            "Show on Y-axis: ",
                            RadioItems(
                                id="y-axis",
                                options=[
                                    {
                                        "label": "Total Repetition",
                                        "value": "total_repetition",
                                    },
                                    {
                                        "label": "Amplification Factor",
                                        "value": "amplification_factor",
                                    },
                                ],
                                value="total_repetition",
                                inline=True,
                                style={"display": "inline-block"},
                            ),
                        ]
                    ),
                    P(Em(id="explanation", children=explanation_total)),
                    P(
                        [
                            Label(
                                "Search for n-grams containing: ",
                                htmlFor="grams-list-input",
                            ),
                            Datalist(
                                id="grams-list",
                                children=[Option(value=gram) for gram in all_grams],
                            ),
                            DccInput(
                                id="grams-list-input", type="text", list="grams-list"
                            ),
                        ]
                    ),
                ]
            ),
            Graph(
                id="scatter-plot",
                figure=fig,
                style={"height": "300px", "flex-grow": "1"},
            ),
        ],
    )


def api_factory(context: WebPresenterContext, options: Optional[dict[str, Any]] = None):
    filter_value = (
        options["matcher"]
        if (
            not options is None
            and "matcher" in options
            and not options["matcher"] is None
        )
        else ""
    )
    data_frame_full = pl.read_parquet(
        context.dependency(ngram_stats).table(OUTPUT_NGRAM_FULL).parquet_path
    )
    data_frame_stats = pl.read_parquet(
        context.dependency(ngram_stats).table(OUTPUT_NGRAM_STATS).parquet_path
    )
    matcher_full = create_word_matcher(filter_value, pl.col(COL_NGRAM_WORDS))
    matcher_stats = create_word_matcher(filter_value, pl.col(COL_NGRAM_WORDS))
    plotted_df_full = (
        data_frame_full.filter(matcher_full)
        if not matcher_full is None
        else data_frame_full
    )
    plotted_df_stats = (
        data_frame_stats.filter(matcher_stats)
        if not matcher_stats is None
        else data_frame_stats
    )
    presenter_model_stats = context.web_presenter.model_dump()
    presenter_model_full = context.web_presenter.model_dump()
    explanations = {
        "total_repetition": "N-grams to the right are repeated by more users. N-grams higher up are repeated more times overall.",
        "amplification_factor": "N-grams to the right are repeated by more users. N-grams higher up are repeated more times on average per user.",
    }
    axes = {
        "x": {"label": "Total Repetition", "value": "total_repetition"},
        "y": {"label": "Amplification Factor", "value": "amplification_factor"},
    }
    presenter_model_full["figure_type"] = "scatter"
    presenter_model_full["explanation"] = explanations
    presenter_model_full["axis"] = axes
    presenter_model_full["ids"] = plotted_df_full[COL_NGRAM_ID].to_list()
    presenter_model_full["timestamps"] = plotted_df_full[
        COL_MESSAGE_TIMESTAMP
    ].to_list()
    presenter_model_full["ngrams"] = plotted_df_full[COL_NGRAM_WORDS].to_list()
    presenter_model_full["ngram_length"] = plotted_df_full[COL_NGRAM_LENGTH].to_list()
    presenter_model_full["messages"] = plotted_df_full[COL_MESSAGE_TEXT].to_list()
    presenter_model_full["users"] = plotted_df_full[COL_AUTHOR_ID].to_list()
    presenter_model_full["user_reps"] = plotted_df_full[
        COL_NGRAM_REPS_PER_USER
    ].to_list()
    presenter_model_full["upns"] = plotted_df_full[COL_MESSAGE_SURROGATE_ID].to_list()
    presenter_model_full["poster_counts"] = plotted_df_full[
        COL_NGRAM_DISTINCT_POSTER_COUNT
    ].to_list()
    presenter_model_full["x"] = plotted_df_full[
        COL_NGRAM_DISTINCT_POSTER_COUNT
    ].to_list()
    presenter_model_full["y"] = {
        "total_repetition": plotted_df_full[COL_NGRAM_TOTAL_REPS].to_list(),
        "amplification_factor": (
            plotted_df_full[COL_NGRAM_TOTAL_REPS]
            / plotted_df_full[COL_NGRAM_DISTINCT_POSTER_COUNT]
        ).to_list(),
    }
    presenter_model_stats["figure_type"] = "scatter"
    presenter_model_stats["explanation"] = explanations
    presenter_model_stats["axis"] = axes
    presenter_model_stats["ngrams"] = plotted_df_stats[COL_NGRAM_WORDS].to_list()
    presenter_model_stats["x"] = plotted_df_stats[
        COL_NGRAM_DISTINCT_POSTER_COUNT
    ].to_list()
    presenter_model_stats["y"] = {
        "total_repetition": plotted_df_stats[COL_NGRAM_TOTAL_REPS].to_list(),
        "amplification_factor": (
            plotted_df_stats[COL_NGRAM_TOTAL_REPS]
            / plotted_df_stats[COL_NGRAM_DISTINCT_POSTER_COUNT]
        ).to_list(),
    }

    return {
        "default_output": OUTPUT_NGRAM_STATS,
        OUTPUT_NGRAM_STATS: pop_unnecessary_fields(presenter_model_stats),
        OUTPUT_NGRAM_FULL: pop_unnecessary_fields(presenter_model_full),
    }
