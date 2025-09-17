from functools import lru_cache

import plotly.graph_objects as go
import polars as pl
from dateutil import parser as dateutil_parser
from shiny import reactive, render, ui
from shinywidgets import output_widget, render_widget

from ..hashtags.interface import COL_AUTHOR_ID, COL_POST, COL_TIME
from .analysis import secondary_analyzer
from .plots import (
    MANGO_DARK_GREEN,
    _plot_hashtags_placeholder_fig,
    _plot_users_placeholder_fig,
    plot_bar_plotly,
    plot_gini_plotly,
    plot_users_plotly,
)

LOGO_URL = "https://raw.githubusercontent.com/CIB-Mango-Tree/CIB-Mango-Tree-Website/main/assets/images/mango-text.PNG"

# https://icons.getbootstrap.com/icons/question-circle-fill/
question_circle_fill = ui.HTML(
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-question-circle-fill mb-1" viewBox="0 0 16 16"><path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.496 6.033h.825c.138 0 .248-.113.266-.25.09-.656.54-1.134 1.342-1.134.686 0 1.314.343 1.314 1.168 0 .635-.374.927-.965 1.371-.673.489-1.206 1.06-1.168 1.987l.003.217a.25.25 0 0 0 .25.246h.811a.25.25 0 0 0 .25-.25v-.105c0-.718.273-.927 1.01-1.486.609-.463 1.244-.977 1.244-2.056 0-1.511-1.276-2.241-2.673-2.241-1.267 0-2.655.59-2.75 2.286a.237.237 0 0 0 .241.247zm2.325 6.443c.61 0 1.029-.394 1.029-.927 0-.552-.42-.94-1.029-.94-.584 0-1.009.388-1.009.94 0 .533.425.927 1.01.927z"/></svg>'
)

df_global = None
context_global = None
df_raw = None
TZ_UTC = "UTC"  # normalizing to UTC, before stripping


def set_df_global_state(df_input, df_output):
    global df_global, df_raw
    df_global = df_output
    df_raw = df_input.with_columns(
        pl.col(COL_TIME)
        .dt.convert_time_zone(TZ_UTC)  # normalize to UTC
        .dt.replace_time_zone(None)  # strip to tz naive format
    )  # Will be loaded from context when needed


@lru_cache(maxsize=32)
def get_raw_data_subset(time_start, time_end, user_id, hashtag):
    """Get subset of raw input data for a timewindow, user and a hashtag"""

    return df_raw.filter(
        pl.col(COL_AUTHOR_ID) == user_id,
        pl.col(COL_TIME).is_between(lower_bound=time_start, upper_bound=time_end),
        pl.col(COL_POST).str.contains(hashtag),
    )


def select_users(secondary_output, selected_hashtag):
    users_df = (
        secondary_output.filter(pl.col("hashtags") == selected_hashtag)["users_all"]
        .explode()
        .value_counts(sort=True)
    )

    return users_df


page_dependencies = ui.tags.head(
    ui.tags.style(".card-header { color:white; background:#f3921e !important; }"),
    ui.tags.link(
        rel="stylesheet", href="https://fonts.googleapis.com/css?family=Roboto"
    ),
    ui.tags.style("body { font-family: 'Roboto', sans-serif; }"),
)

# main panel showing the line plot
analysis_panel = ui.card(
    ui.card_header(
        "Full time window analysis ",
        ui.tooltip(
            ui.tags.span(
                question_circle_fill,
                style="cursor: help; font-size: 14px;",
            ),
            "This analysis shows the gini coefficient over the entire dataset. Select specific timepoints below to explore narrow time windows.",
            placement="top",
        ),
    ),
    ui.input_checkbox("smooth_checkbox", "Show smoothed line", value=False),
    output_widget("line_plot", height="300px"),
)

# panel to show hashtag distributions
hashtag_plot_panel = ui.card(
    ui.card_header(
        "Most frequently used hashtags ",
        ui.tooltip(
            ui.tags.span(
                question_circle_fill,
                style="cursor: help; font-size: 14px;",
            ),
            "Displayed are the hashtags that users posted most frequently in the time window starting with selected date.",
            placement="top",
        ),
    ),
    ui.output_text(id="hashtag_card_info"),
    output_widget("hashtag_bar_plot", height="1500px"),
    max_height="500px",
    full_screen=True,
)

# panel to show hashtag count per user distribution
users_plot_panel = ui.card(
    ui.card_header(
        "Hashtag usage by accounts ",
        ui.tooltip(
            ui.tags.span(
                question_circle_fill,
                style="cursor: help; font-size: 14px;",
            ),
            "Select a hashtag to show the number of times it was used by specific accounts.",
            placement="top",
        ),
    ),
    ui.input_selectize(
        id="hashtag_picker",
        label="Show accounts that used hashtag:",
        choices=[],
        width="100%",
    ),
    output_widget("user_bar_plot", height="800px"),
    max_height="500px",
    full_screen=True,
)

tweet_explorer = ui.card(
    ui.card_header(
        "Tweet Explorer ",
        ui.tooltip(
            ui.tags.span(
                question_circle_fill,
                style="cursor: help; font-size: 14px;",
            ),
            "Inspect the posts containing the hashtag for the specific user in the selected time window.",
            placement="top",
        ),
    ),
    ui.input_selectize(
        id="user_picker",
        label="Show posts for account:",
        choices=[],
        width="100%",
    ),
    ui.output_text(id="tweets_title"),
    ui.output_data_frame("tweets"),
)


def server(input, output, session):
    @reactive.calc
    def get_df():
        """Get primary data from global context and fix datetime format"""
        df = df_global
        # Convert timewindow_start from string to datetime
        if df is not None and "timewindow_start" in df.columns:
            df = df.with_columns(
                pl.col("timewindow_start").str.to_datetime("%Y-%m-%d %H:%M:%S")
            )
        return df

    @reactive.calc
    def get_time_step():
        """Calculate time step from data"""
        df = get_df()
        if len(df) > 1:
            return df["timewindow_start"][1] - df["timewindow_start"][0]
        return None

    def _get_timewindow_info_text():
        """Format selected timewindow into a short info text for feedback"""
        click_data = clicked_data.get()

        if click_data and hasattr(click_data, "xs") and len(click_data.xs) > 0:
            timewindow = get_selected_datetime()
            time_step = get_time_step()
            timewindow_end = timewindow + time_step
            format_code = "%B %d, %Y"
            dates_formatted = f"{timewindow.strftime(format_code)} - {timewindow_end.strftime(format_code)}"
            return "Time window: " + dates_formatted
        else:
            return "Time window not available (select first)"

    @reactive.effect
    def populate_date_choices():
        """Populate date picker choices when data is loaded"""
        df = get_df()
        choices = [dt.strftime("%B %d, %Y") for dt in df["timewindow_start"].to_list()]
        ui.update_selectize(
            "date_picker",
            choices=choices,
            selected=df["timewindow_start"].to_list()[0].strftime("%B %d, %Y"),
            session=session,
        )

    def get_midpoint_datetime():
        """Default - middle of dataset instead of first point"""
        df = get_df()
        middle_index = len(df) // 2
        return df["timewindow_start"][middle_index]

    # this will store line plot values when clicked
    clicked_data = reactive.value(None)

    def get_selected_datetime():
        """Get datetime from plot click, converting string to datetime"""
        click_data = clicked_data.get()
        if click_data and hasattr(click_data, "xs") and len(click_data.xs) > 0:
            clicked_value = click_data.xs[0]

            # If it's a string, parse it to datetime
            if isinstance(clicked_value, str):
                return dateutil_parser.parse(clicked_value)
            else:
                return clicked_value  # Already datetime
        else:
            return get_midpoint_datetime()

    @reactive.calc
    def secondary_analysis():
        # Only run analysis if user has clicked on line plot
        click_data = clicked_data()
        if not (click_data and hasattr(click_data, "xs") and len(click_data.xs) > 0):
            return None

        timewindow = get_selected_datetime()
        df = get_df()
        df_out2 = secondary_analyzer(df, timewindow)
        return df_out2

    @reactive.effect
    def update_hashtag_choices():
        analysis_result = secondary_analysis()
        if analysis_result is None:
            hashtags = []
        else:
            hashtags = analysis_result["hashtags"].to_list()

        ui.update_selectize(
            "hashtag_picker",
            choices=hashtags,
            selected=hashtags[0] if hashtags else None,
            session=session,
        )

    @reactive.effect
    def update_user_choices():
        analysis_result = secondary_analysis()
        selected_hashtag = input.hashtag_picker()

        if analysis_result is None or not selected_hashtag:
            users = []
        else:
            df_users = select_users(
                analysis_result, selected_hashtag=selected_hashtag
            ).sort("count", descending=True)
            users = df_users["users_all"].to_list()

        ui.update_selectize(
            "user_picker",
            choices=users,
            selected=users[0] if users else None,
            session=session,
        )

    # whenever line plot is clicked, update `click_reactive`
    def on_point_click(trace, points, state):
        clicked_data.set(points)

        # Get the parent figure widget from the trace
        fig_widget = trace.parent

        # Remove existing red marker traces
        traces_to_remove = []
        for i, existing_trace in enumerate(fig_widget.data):
            if (
                hasattr(existing_trace, "marker")
                and hasattr(existing_trace.marker, "color")
                and existing_trace.marker.color == MANGO_DARK_GREEN
            ):
                traces_to_remove.append(i)

        # Remove old red markers in reverse order
        for i in reversed(traces_to_remove):
            fig_widget.data = fig_widget.data[:i] + fig_widget.data[i + 1 :]

        # Add new red marker at clicked point
        fig_widget.add_scatter(
            x=[points.xs[0]],
            y=[points.ys[0]],
            mode="markers",
            marker=dict(size=8, color=MANGO_DARK_GREEN),
            hoverinfo="skip",  # Disable hover for this marker
            showlegend=False,
        )

    @render_widget
    def line_plot():
        smooth_enabled = input.smooth_checkbox()

        df = get_df()

        fig = plot_gini_plotly(df=df, smooth=smooth_enabled)

        fig_widget = go.FigureWidget(fig.data, fig.layout)
        fig_widget.data[0].on_click(on_point_click)

        return fig_widget

    @render_widget
    def hashtag_bar_plot():
        analysis_result = secondary_analysis()

        if analysis_result is not None:
            selected_date = get_selected_datetime()
            return plot_bar_plotly(
                data_frame=analysis_result,
                selected_date=selected_date,
                show_title=False,
            )
        else:
            # Return placeholder plot if no data clicked
            return _plot_hashtags_placeholder_fig()

    @render.text
    def hashtag_card_info():
        return _get_timewindow_info_text()

    @render_widget
    def user_bar_plot():
        analysis_result = secondary_analysis()
        selected_hashtag = input.hashtag_picker()

        if analysis_result is not None and selected_hashtag:
            users_data = select_users(analysis_result, selected_hashtag)
            return plot_users_plotly(users_data)
        else:
            # Return empty plot if no hashtag selected
            return _plot_users_placeholder_fig()

    @render.text
    def tweets_title():
        return _get_timewindow_info_text()

    @render.data_frame
    def tweets():
        timewindow = get_selected_datetime()
        time_step = get_time_step()

        if time_step:
            df_posts = get_raw_data_subset(
                time_start=timewindow,
                time_end=timewindow + time_step,
                user_id=input.user_picker(),
                hashtag=input.hashtag_picker(),
            )
        else:
            # Return empty dataframe if no time step available
            return pl.DataFrame({COL_TIME: [], COL_POST: []})

        # format strings
        df_posts = df_posts.with_columns(
            pl.col(COL_TIME).dt.strftime("%B %d, %Y %I:%M %p")
        )

        df_posts = df_posts.rename({"time": "Post date and time", "text": "Text"})

        df_posts = df_posts.drop(pl.col(COL_AUTHOR_ID))

        return render.DataGrid(df_posts, width="100%")
