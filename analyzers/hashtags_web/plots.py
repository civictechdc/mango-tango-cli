import plotly.graph_objects as go
import polars as pl

FS = 16
MANGO_DARK_GREEN = "#609949"
MANGO_DARK_ORANGE = "#f3921e"
LIGHT_BLUE = "#acd7e5"


def plot_gini_plotly(df: pl.DataFrame, smooth: bool = False):
    """Create a plotly line plot with white theme"""

    y = df.select(pl.col("gini")).to_numpy().flatten()
    x = df.select(pl.col("timewindow_start")).to_numpy().flatten()

    fig = go.Figure()

    # Add main line
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="lines",
            name="Gini coefficient",
            hovertemplate="<b>Gini:</b> %{y:.3f}<extra></extra>",
            line=dict(color="black", width=1.5),
        )
    )

    # Add smooth line if requested
    if smooth:
        y2 = df.select(pl.col("gini_smooth")).to_numpy().flatten()
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y2,
                mode="lines",
                name="Smoothed",
                hovertemplate="<b>Gini (Smoothed):</b> %{y:.3f}<extra></extra>",
                line=dict(color="orange", width=2),
            )
        )

    # Update layout with white theme
    fig.update_layout(
        template="plotly_white",
        title="Concentration of hashtags over time",
        xaxis_title="Time window (start date)",
        yaxis_title="Hashtag Concentration<br>(Gini coefficient)",
        hovermode="x unified",
        showlegend=False,
        height=300,
        margin=dict(l=50, r=50, t=50, b=50),
    )

    return fig


def plot_bar_plotly(data_frame, selected_date=None, show_title=True):
    """Create an interactive plotly bar plot"""

    if len(data_frame) == 0:
        fig = go.Figure()
        fig.add_annotation(
            x=0.5,
            y=0.5,
            text="No data for selected date",
            showarrow=False,
            font=dict(size=16),
            xref="paper",
            yref="paper",
        )
        fig.update_layout(
            template="plotly_white",
            xaxis=dict(range=[0, 1]),
            yaxis=dict(range=[0, 1]),
            # height=400
        )
        return fig

    # Use all data, no threshold filtering
    df_sorted = data_frame.sort("hashtag_perc", descending=False)

    # Get data (lowest to highest for plotly to display highest at top)
    hashtags = df_sorted["hashtags"].to_list()
    percentages = df_sorted["hashtag_perc"].to_list()

    # Create horizontal bar chart with fixed bar width
    fig = go.Figure(
        go.Bar(
            x=percentages,
            y=hashtags,
            orientation="h",
            marker_color=MANGO_DARK_GREEN,
            hovertemplate="<b>%{y}</b><br>%{x:.1f}% of all hashtags<extra></extra>",
            width=0.8,  # Fixed bar width
            text=hashtags,  # Add text labels on bars
            textposition="outside",
            textfont=dict(color="black", size=12),
        )
    )

    # Format title with date (optional)
    if show_title:
        if selected_date:
            formatted_date = selected_date.strftime("%B %d, %Y")
            title = f"Most frequent hashtags - {formatted_date}"
        else:
            title = "Most frequent hashtags"
    else:
        title = None

    # Use fixed height and let container handle scrolling
    # Calculate dynamic height based on number of hashtags (fixed spacing per bar)
    bar_height = 30  # Fixed height per bar
    dynamic_height = len(hashtags) * bar_height + 100  # +100 for margins

    # Update layout
    fig.update_layout(
        template="plotly_white",
        title=title,
        xaxis_title="% all hashtags in the selected time window",
        yaxis_title="",
        height=dynamic_height,
        margin=dict(l=0, r=50, t=10, b=50),
        showlegend=False,
    )

    # Update axes
    fig.update_xaxes(
        range=[0, max(percentages) * 1.5], side="top"
    )  # Extra space for text, x-axis on top
    fig.update_yaxes(
        categoryorder="array", categoryarray=hashtags, showticklabels=False
    )

    return fig


def _plot_hashtags_placeholder_fig():
    """Create a an empty placeholder figure for hashtags barplot"""
    fig = go.Figure()

    fig.add_annotation(
        x=0.5,
        y=0.5,
        text="Select a time window on line plot above<br>hashtags in that time window",
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


def plot_users_plotly(users_data):
    """Create an interactive plotly bar plot for user distribution"""

    if len(users_data) == 0:
        fig = go.Figure()
        fig.add_annotation(
            x=0.5,
            y=0.5,
            text="No users found for this hashtag",
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

    # Sort by count (ascending for plotly display with highest at top)
    df_sorted = users_data.sort("count", descending=False)

    # Get data
    users = df_sorted["users_all"].to_list()
    counts = df_sorted["count"].to_list()

    # Create horizontal bar chart with fixed bar width
    fig = go.Figure(
        go.Bar(
            x=counts,
            y=users,
            orientation="h",
            marker_color=MANGO_DARK_GREEN,
            hovertemplate="<b>%{y}</b><br>%{x} posts<extra></extra>",
            width=0.8,  # Fixed bar width
            text=users,  # Add text labels on bars
            textposition="outside",
            textfont=dict(color="black", size=12),
        )
    )

    # Calculate dynamic height based on number of users
    bar_height = 30  # Fixed height per bar
    dynamic_height = len(users) * bar_height + 100  # +100 for margins

    # Update layout
    fig.update_layout(
        template="plotly_white",
        title=None,
        xaxis_title="Number of posts",
        yaxis_title="",
        height=dynamic_height,
        margin=dict(l=0, r=50, t=0, b=10),
        showlegend=False,
    )

    # Update axes
    fig.update_xaxes(
        range=[0, max(counts) * 1.5], side="top"
    )  # Extra space for text, x-axis on top
    fig.update_yaxes(categoryorder="array", categoryarray=users, showticklabels=False)

    return fig


def _plot_users_placeholder_fig():
    fig = go.Figure()

    fig.add_annotation(
        x=0.5,
        y=0.5,
        text="Select a time window and a hashtag<br>to see user distribution",
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
