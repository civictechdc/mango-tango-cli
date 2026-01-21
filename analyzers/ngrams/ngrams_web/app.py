import plotly.express as px
import plotly.graph_objects as go
import polars as pl
from shiny import reactive, render, ui
from shinywidgets import output_widget, render_widget

from ..ngrams_base.interface import (
    COL_AUTHOR_ID,
    COL_MESSAGE_TEXT,
    COL_MESSAGE_TIMESTAMP,
    COL_NGRAM_ID,
    COL_NGRAM_LENGTH,
)
from ..ngrams_stats.interface import (
    COL_NGRAM_DISTINCT_POSTER_COUNT,
    COL_NGRAM_TOTAL_REPS,
    COL_NGRAM_WORDS,
)

MANGO_DARK_GREEN = "#609949"
CLICKED_COLOR = "red"
data_stats = None  # secondary output
data_full = None  # primary output
ngram_choices_dict = {}


def _set_global_state_vars(df_stats: pl.DataFrame, df_full: pl.DataFrame):
    global data_stats, data_full

    data_stats = df_stats
    data_full = df_full


def plot_scatter(data):
    import numpy as np

    # Add jitter to x-axis to separate overlapping points
    # Since we're using log scale, we need to be careful with the jitter amount
    rng = np.random.default_rng(seed=42)  # For reproducible jitter

    # Create jitter as a small multiplier (5% of the log value)
    jitter_factor = 0.05
    data = data.with_columns(
        (
            pl.col(COL_NGRAM_TOTAL_REPS)
            * (1 + rng.uniform(-jitter_factor, jitter_factor, len(data)))
        ).alias("total_reps_jittered")
    )

    n_gram_categories = data.select(pl.col("n").unique().sort()).to_series()

    fig = px.scatter(
        data_frame=data,
        x="distinct_posters",
        y="total_reps_jittered",
        log_y=True,
        log_x=True,
        custom_data=[COL_NGRAM_WORDS, COL_NGRAM_ID, COL_NGRAM_TOTAL_REPS],
        color="n",
        category_orders={"n": n_gram_categories},
    )

    fig.update_traces(
        marker=dict(size=11, opacity=0.7, line=dict(width=0.5, color="white")),
        hovertemplate="<br>".join(
            [
                "<b>Ngram:</b> %{customdata[0]}",
                "<b>Frequency:</b> %{customdata[2]}",
                "<b>Nr. unique posters:</b> %{x}",
            ]
        ),
    )

    # Customize the plot
    fig.update_layout(
        title_text="Repeated phrases and accounts",
        yaxis_title="N-gram frequency",
        xaxis_title="Nr. unique posters",
        hovermode="closest",
        legend=dict(title="N-gram length"),
        template="plotly_white",
    )

    return fig


# helper to clear markers from figure widget
def _remove_markers(figure_widget: go.FigureWidget) -> go.FigureWidget:
    traces_to_remove = []
    for i, existing_trace in enumerate(figure_widget.data):
        try:
            if (
                hasattr(existing_trace, "marker")
                and hasattr(existing_trace.marker, "color")
                and str(existing_trace.marker.color) == CLICKED_COLOR
            ):
                traces_to_remove.append(i)
        except Exception:
            continue

    # Remove old markers in reverse order
    for i in reversed(traces_to_remove):
        try:
            figure_widget.data = figure_widget.data[:i] + figure_widget.data[i + 1 :]
        except Exception:
            continue

    return figure_widget


def _get_app_layout(ngram_choices_dict: dict):

    app_layout = [
        ui.card(
            ui.card_header("N-gram statistics"),
            ui.layout_sidebar(
                ui.sidebar(
                    ui.input_text(
                        id="ngram_content_search",
                        label="Search N-gram Content:",
                        placeholder="Enter keywords to search",
                    ),
                    ui.input_selectize(
                        id="ngram_length_selector",
                        label="Included N-grams:",
                        choices=ngram_choices_dict,
                        selected=list(ngram_choices_dict.keys()),
                        multiple=True,
                    ),
                    ui.div(
                        ui.input_action_button(
                            id="reset_button",
                            label="Clear selection",
                            fill=False,
                        ),
                        style="margin-top: 25px;",  # Align with labeled inputs
                    ),
                ),
                output_widget("scatter_plot", height="400px"),
            ),
        ),
        ui.card(
            ui.card_header("Data viewer"),
            ui.output_text(id="data_info"),
            ui.output_data_frame("data_viewer"),
        ),
    ]

    return app_layout


def server(input, output, sessions):

    def _format_data_for_display(df: pl.DataFrame) -> pl.DataFrame:
        """Format dataframe for display with column selection and renaming"""
        SEL_COLUMNS = [
            COL_AUTHOR_ID,
            COL_NGRAM_WORDS,
            COL_MESSAGE_TEXT,
            COL_MESSAGE_TIMESTAMP,
        ]
        COL_RENAME = ["Unique user ID", "N-gram content", "Post content", "Timestamp"]
        old2new = {k: v for k, v in zip(SEL_COLUMNS, COL_RENAME)}

        if df.is_empty():
            return df.select(SEL_COLUMNS).head(0).rename(old2new).with_row_count(
                name="#", offset=1
            )

        return (
            df.with_columns(
                pl.col(COL_MESSAGE_TIMESTAMP).dt.strftime("%B %d, %Y %I:%M %p")
            )
            .select(SEL_COLUMNS)
            .rename(old2new)
            .with_row_count(name="#", offset=1)
        )

    @reactive.calc
    def get_search_filtered_stats():
        """Get n-gram statistics filtered by search term and n-gram length only.

        Note: Click filtering is NOT applied here to avoid re-rendering the scatter plot.
        Click filtering is applied downstream in get_filtered_full_data().
        """

        global data_stats

        # Start with full stats data
        data_out = data_stats

        # Get filter inputs (excluding clicks)
        ngram_search_term = (input.ngram_content_search() or "").strip()
        ngram_lengths = (
            input.ngram_length_selector()
        )  # tuple[str] e.g. ('3', '5') or empty tuple

        # Apply filters in order: search → length

        # 1. Filter by search term (if provided)
        if ngram_search_term:
            # Match the search term as whole word(s)
            regex_pattern = f"\\b{ngram_search_term}\\b"
            data_out = data_out.filter(
                pl.col(COL_NGRAM_WORDS).str.contains(pattern=regex_pattern),
            )

        # 2. Filter by n-gram length (if any selected)
        # If ngram_lengths is empty (user deselected all), return empty dataframe
        if not ngram_lengths:
            return data_out.head(0)

        data_out = data_out.filter(pl.col(COL_NGRAM_LENGTH).is_in(ngram_lengths))

        return data_out

    # Store the figure widget reference
    current_figure_widget = reactive.value(None)

    @reactive.effect
    def handle_reset_button():
        # if reset button is clicked
        # disable it and clear traces
        if input.reset_button():
            # Reset the click data
            click_data.set(None)
            # Reset the scatter plot by removing any red markers
            fig_widget = current_figure_widget()
            if fig_widget is not None:
                try:
                    # Remove red marker traces
                    fig_widget = _remove_markers(figure_widget=fig_widget)
                except Exception:
                    pass

    def get_top_n_stats(df: pl.DataFrame = None, n: int = 100) -> pl.DataFrame:
        """Format and return top N n-gram statistics.

        Args:
            df: Optional dataframe to format. If None, uses global data_stats.
            n: Number of top n-grams to return (default 100)

        Returns:
            Formatted dataframe with sorted and renamed columns
        """
        if df is None:
            global data_stats
            df = data_stats

        data_top_n = (
            df.select(
                [
                    COL_NGRAM_WORDS,
                    COL_NGRAM_TOTAL_REPS,
                    COL_NGRAM_DISTINCT_POSTER_COUNT,
                    COL_NGRAM_LENGTH,
                ]
            )
            .sort(
                pl.col(COL_NGRAM_TOTAL_REPS),
                pl.col(COL_NGRAM_DISTINCT_POSTER_COUNT),
                pl.col(COL_NGRAM_LENGTH),
                descending=[True, True, False],
            )
            .rename(
                {
                    COL_NGRAM_WORDS: "N-gram content",
                    COL_NGRAM_TOTAL_REPS: "Nr. total repetitions",
                    COL_NGRAM_DISTINCT_POSTER_COUNT: "Nr. unique posters",
                    COL_NGRAM_LENGTH: "N-gram length",
                }
            )
            .head(n)
        )
        return data_top_n

    click_data = reactive.value(None)

    def on_point_click(trace, points, state):
        if not hasattr(points, "point_inds") or not points.point_inds:
            return

        # Extract ngram_id from customdata
        point_idx = points.point_inds[0]

        try:
            # Access customdata from the trace
            customdata = trace.customdata
            if customdata is not None and len(customdata) > point_idx:
                ngram_id = customdata[point_idx][
                    1
                ]  # ngram_id is second item in customdata
                click_data.set({COL_NGRAM_ID: ngram_id, "points": points})
            else:
                click_data.set(points)
        except Exception:
            click_data.set(points)

        fig_widget = trace.parent

        # Clear markers from previous clicks
        fig_widget = _remove_markers(figure_widget=fig_widget)

        # Add new green marker at clicked point
        fig_widget.add_scatter(
            x=[points.xs[0]],
            y=[points.ys[0]],
            mode="markers",
            marker=dict(size=15, color=CLICKED_COLOR),
            hoverinfo="skip",
            showlegend=False,
        )

    @render_widget
    def scatter_plot():

        df = get_search_filtered_stats()

        fig = plot_scatter(data=df)

        # Create FigureWidget directly from the figure
        fig_widget = go.FigureWidget(fig)

        # Store reference to figure widget for reset functionality
        current_figure_widget.set(fig_widget)

        # Attach click handler to all traces (one for each color group)
        for trace in fig_widget.data:
            trace.on_click(on_point_click)

        return fig_widget

    @reactive.calc
    def get_filtered_full_data():
        """Get filtered data respecting search, ngram size selection, and clicks.

        This applies all three filter types:
        1. Search term (via get_search_filtered_stats)
        2. N-gram length (via get_search_filtered_stats)
        3. Click selection (applied here)
        """
        global data_full

        # Start with search and length filtered stats
        stats_filtered = get_search_filtered_stats()

        # Apply click filter if a point was clicked
        clicked = click_data()
        if clicked and isinstance(clicked, dict) and COL_NGRAM_ID in clicked:
            ngram_id = clicked[COL_NGRAM_ID]
            stats_filtered = stats_filtered.filter(pl.col(COL_NGRAM_ID) == ngram_id)

        # If stats are empty, return empty formatted dataframe
        if stats_filtered.is_empty():
            return _format_data_for_display(data_full.head(0))

        # Get unique ngram IDs and lengths from filtered stats
        ngram_ids = stats_filtered.select(pl.col(COL_NGRAM_ID).unique()).to_series()
        ngram_lengths = (
            stats_filtered.select(pl.col(COL_NGRAM_LENGTH).unique()).cast(pl.Int8)
        ).to_series()

        # Filter the full dataframe with individual posts
        data_filtered = data_full.filter(
            pl.col(COL_NGRAM_ID).is_in(ngram_ids),
            pl.col(COL_NGRAM_LENGTH).is_in(ngram_lengths),
        )

        return _format_data_for_display(data_filtered)

    @render.text
    def data_info() -> str:
        """Display context-aware information about the current data view"""

        # Check if a point was clicked
        clicked = click_data()
        has_click = clicked and isinstance(clicked, dict) and COL_NGRAM_ID in clicked

        # Check if there's a search term
        content_search = (input.ngram_content_search() or "").strip()
        has_search = bool(content_search)

        # Get filtered data
        filtered_data = get_filtered_full_data()

        if has_click:
            # Show specific ngram info
            if not filtered_data.is_empty():
                total_reps = len(filtered_data)
                ngram_string = filtered_data["N-gram content"][0]
                return f"N-gram: '{ngram_string}' — {total_reps:,} total repetitions"
            else:
                return "Selected n-gram not found in current filters. Try adjusting your search or n-gram length selection."

        if has_search:
            # Show search results summary
            search_stats = get_search_filtered_stats()

            if search_stats.is_empty():
                return f"No results found for '{content_search}'. Try adjusting your search or n-gram length selection."

            total_ngrams = len(search_stats)
            if not filtered_data.is_empty():
                total_records = len(filtered_data)
                return f"Search results for '{content_search}': {total_ngrams:,} unique n-grams (showing top 100) with {total_records:,} total occurrences"
            else:
                return f"Search results for '{content_search}': {total_ngrams:,} unique n-grams"

        # Default: show summary message
        return "Showing summary (top 100 n-grams by frequency). Click a data point on the scatter plot to view all occurrences."

    reset_click_count = reactive.value(0)

    @render.data_frame
    def data_viewer():
        """Display appropriate data based on user interactions.

        Three scenarios:
        1. No filters: Show top 100 n-grams (stats summary)
        2. Search/length filter only: Show top 100 filtered n-grams (stats summary)
        3. Click on n-gram: Show all individual posts for that n-gram (full data)
        """
        # Check if user clicked on a specific n-gram
        clicked = click_data()
        has_click = clicked and isinstance(clicked, dict) and COL_NGRAM_ID in clicked

        # Check if user has search term
        content_search = (input.ngram_content_search() or "").strip()
        has_search = bool(content_search)

        # if a new click is detected, show summary
        if input.reset_button.get() > reset_click_count.get():

            reset_click_count.set(input.reset_button.get())

            return render.DataGrid(get_top_n_stats(n=100), width="100%")

        if has_click:
            # Show individual posts for clicked n-gram
            data_for_display = get_filtered_full_data()
            return render.DataGrid(data_for_display, width="100%")

        # No click: show n-gram statistics (top 100)
        if has_search:
            # Show filtered n-gram stats (search + length filters)
            stats_filtered = get_search_filtered_stats()
            if stats_filtered.is_empty():
                # Return empty with proper column structure
                return render.DataGrid(get_top_n_stats().head(0), width="100%")

            # Format and return top 100 filtered stats
            data_for_display = get_top_n_stats(df=stats_filtered, n=100)
            return render.DataGrid(data_for_display, width="100%")

        # Default: show top 100 n-grams by frequency
        return render.DataGrid(get_top_n_stats(n=100), width="100%")
