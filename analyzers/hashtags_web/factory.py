import polars as pl

from analyzer_interface.context import WebPresenterContext

from ..hashtags.interface import OUTPUT_GINI


def factory(context: WebPresenterContext):
    # Load hashtag analysis data from the base analyzer
    df_hashtags = pl.read_parquet(context.base.table(OUTPUT_GINI).parquet_path)

    # Create and configure the Shiny app with CLI data
    from .app import create_app

    shiny_app = create_app(df_hashtags, context)

    # For now, mount the Shiny app via iframe in Dash
    # This preserves the existing CLI integration
    from dash import html

    app = context.dash_app

    app.layout = html.Div(
        [
            html.H1("Hashtag Analysis Dashboard"),
            html.Iframe(
                src=f"http://localhost:8051",  # Shiny app will run on port 8051
                style={"width": "100%", "height": "800px", "border": "none"},
            ),
        ]
    )

    # Start the Shiny app server
    import threading

    from shiny import run_app

    def run_shiny():
        run_app(shiny_app, host="127.0.0.1", port=8051, launch_browser=False)

    shiny_thread = threading.Thread(target=run_shiny, daemon=True)
    shiny_thread.start()

    return None
