from functools import lru_cache

import numpy as np
import polars as pl
from shiny import reactive, render, ui
from shinywidgets import output_widget, render_widget

from ..hashtags.interface import COL_AUTHOR_ID, COL_POST, COL_TIME
from .analysis import secondary_analyzer
from .plots import plot_bar_plotly, plot_gini_plotly, plot_users_plotly

MANGO_ORANGE2 = "#f3921e"
LOGO_URL = "https://raw.githubusercontent.com/CIB-Mango-Tree/CIB-Mango-Tree-Website/main/assets/images/mango-text.PNG"

# https://icons.getbootstrap.com/icons/question-circle-fill/
question_circle_fill = ui.HTML(
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-question-circle-fill mb-1" viewBox="0 0 16 16"><path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.496 6.033h.825c.138 0 .248-.113.266-.25.09-.656.54-1.134 1.342-1.134.686 0 1.314.343 1.314 1.168 0 .635-.374.927-.965 1.371-.673.489-1.206 1.06-1.168 1.987l.003.217a.25.25 0 0 0 .25.246h.811a.25.25 0 0 0 .25-.25v-.105c0-.718.273-.927 1.01-1.486.609-.463 1.244-.977 1.244-2.056 0-1.511-1.276-2.241-2.673-2.241-1.267 0-2.655.59-2.75 2.286a.237.237 0 0 0 .241.247zm2.325 6.443c.61 0 1.029-.394 1.029-.927 0-.552-.42-.94-1.029-.94-.584 0-1.009.388-1.009.94 0 .533.425.927 1.01.927z"/></svg>'
)

df_global = None
context_global = None
df_raw = None


def set_df_global_state(df_input, df_output):
    global df_global, df_raw
    df_global = df_output
    df_raw = df_input  # Will be loaded from context when needed


@lru_cache(maxsize=32)
def get_raw_data_subset(time_start, time_end, user_id, hashtag):
    """Get subset of raw input data for a timewindow, user and a hashtag"""

    return df_raw.filter(
        pl.col(COL_AUTHOR_ID) == user_id,
        pl.col(COL_TIME).is_between(lower_bound=time_start, upper_bound=time_end),
        pl.col(COL_POST).str.contains(hashtag),
    )


# Global variables for CLI integration


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
analysis_panel = ui.accordion(
    ui.accordion_panel(
        "",
        [
            ui.card(
                ui.card_header(
                    "Full time scale analysis ",
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
        ],
    )
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
            "Select a date to display the hashtags that users posted most frequently in the time period starting with that date.",
            placement="top",
        ),
    ),
    ui.input_selectize(
        id="date_picker",
        label="Show hashtags for time period starting on:",
        choices=[],  # Will be populated by reactive effect
        selected=None,
        width="100%",
    ),
    output_widget("bar_plot", height="1500px"),
    max_height="500px",
    full_screen=True,
)

# panel to show hashtag count per user distribution
users_plot_panel = ui.card(
    ui.card_header(
        "Hashtag usage by users ",
        ui.tooltip(
            ui.tags.span(
                question_circle_fill,
                style="cursor: help; font-size: 14px;",
            ),
            "Select a user account to show the number of times it used a specific hashtag.",
            placement="top",
        ),
    ),
    ui.input_selectize(
        id="hashtag_picker",
        label="Show users for hashtag:",
        choices=[],
        width="100%",
    ),
    output_widget("user_plot", height="800px"),
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
            "Inspect the posts containing the hashtag for the specific user in the selected time period.",
            placement="top",
        ),
    ),
    ui.input_selectize(
        id="user_picker",
        label="Show tweets for user:",
        choices=[],
        width="100%",
    ),
    ui.output_text(id="tweets_title"),
    ui.output_data_frame("tweets"),
)

analysis_panel_elements = [
    page_dependencies,
    analysis_panel,
    ui.layout_columns(
        hashtag_plot_panel,
        users_plot_panel,
    ),
    tweet_explorer,
]


ABOUT_TEXT = ui.markdown(
    f"""

<img src="{LOGO_URL}" alt="logo" style="width:200px;"/>

CIB Mango Tree, a collaborative and open-source project to develop software that tests for coordinated inauthentic behavior (CIB) in datasets of online activity.

[mangotree.org](https://mangotree.org)

A project of [Civic Tech DC](https://www.civictechdc.org/), our mission is to share methods to uncover how disruptive actors seek to hack our legitimate online discourse regarding health, politics, and society. The CIB Mango Tree presents the most simple tests for CIB first – the low-hanging fruit. These tests are easy to run and interpret. They will reveal signs of unsophisticated CIB. As you move up the Mango Tree, tests become harder and will scavenge for higher-hanging fruit.

"""
)
app_layout = ui.page_navbar(
    ui.nav_panel(
        "Dashboard",
        analysis_panel_elements,
    ),
    ui.nav_panel(
        "About",
        ui.card(
            ui.card_header("About the Mango Tree project"),
            ABOUT_TEXT,
            ui.card_footer("PolyForm Noncommercial License 1.0.0"),
        ),
    ),
    title="Hashtag analysis dashboard",
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

    @lru_cache(maxsize=100)
    def get_selected_datetime_cached(selected_formatted):
        """Convert selected formatted date back to datetime with caching"""
        df = get_df()
        # Find the datetime that matches the formatted string
        for dt in df["timewindow_start"].to_list():
            if dt.strftime("%B %d, %Y") == selected_formatted:
                return dt
        return df["timewindow_start"].to_list()[0]  # fallback

    def get_selected_datetime():
        return get_selected_datetime_cached(input.date_picker())

    @reactive.calc
    def selected_date():
        df = get_df()
        x_selected = df.with_columns(
            sel=pl.col("timewindow_start") == input.date_picker()
        ).select(pl.col("sel"))

        return np.where(x_selected)[0].item()

    @reactive.calc
    def secondary_analysis():
        timewindow = get_selected_datetime()
        df = get_df()
        df_out2 = secondary_analyzer(df, timewindow)
        return df_out2

    @reactive.effect
    def update_hashtag_choices():
        hashtags = secondary_analysis()["hashtags"].to_list()
        ui.update_selectize(
            "hashtag_picker",
            choices=hashtags,
            selected=hashtags[0] if hashtags else None,
            session=session,
        )

    @reactive.effect
    def update_user_choices():
        df_users = select_users(
            secondary_analysis(), selected_hashtag=input.hashtag_picker()
        ).sort("count", descending=True)

        users = df_users["users_all"].to_list()

        ui.update_selectize(
            "user_picker",
            choices=users,
            selected=users[0] if users else None,
            session=session,
        )

    @render_widget
    def line_plot():
        selected_date = get_selected_datetime()
        smooth_enabled = input.smooth_checkbox()
        df = get_df()
        return plot_gini_plotly(df=df, x_selected=selected_date, smooth=smooth_enabled)

    @render_widget
    def bar_plot():
        selected_date = get_selected_datetime()
        return plot_bar_plotly(
            data_frame=secondary_analysis(),
            selected_date=selected_date,
            show_title=False,
        )

    @render_widget
    def user_plot():
        selected_hashtag = input.hashtag_picker()
        if selected_hashtag:
            users_data = select_users(secondary_analysis(), selected_hashtag)
            return plot_users_plotly(users_data)
        else:
            # Return empty plot if no hashtag selected
            import plotly.graph_objects as go

            fig = go.Figure()
            fig.add_annotation(
                x=0.5,
                y=0.5,
                text="Select a hashtag to see user distribution",
                showarrow=False,
                font=dict(size=16),
                xref="paper",
                yref="paper",
            )
            fig.update_layout(
                template="plotly_white",
                xaxis=dict(range=[0, 1]),
                yaxis=dict(range=[0, 1]),
                height=400,
            )
            return fig

    @render.text
    def tweets_title():
        timewindow = get_selected_datetime()
        time_step = get_time_step()
        if time_step:
            timewindow_end = timewindow + time_step
            format_code = "%B %d, %Y"
            dates_formatted = f"{timewindow.strftime(format_code)} - {timewindow_end.strftime(format_code)}"
            return "Showing posts in time window: " + dates_formatted
        return "Time window information not available"

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

        return render.DataGrid(df_posts, width="100%", filters=True)
