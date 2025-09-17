import polars as pl
from dash import html
from shiny.ui import layout_columns, nav_panel

from analyzer_interface.context import (
    FactoryOutputContext,
    ShinyContext,
    WebPresenterContext,
)
from app.project_context import _get_columns_with_semantic
from app.shiny import page_dependencies

from ..hashtags.interface import COL_TIME, OUTPUT_GINI
from .app import (
    analysis_panel,
    hashtag_plot_panel,
    server,
    set_df_global_state,
    tweet_explorer,
    users_plot_panel,
)


def load_and_transform_input_data(
    web_context: WebPresenterContext, column_names: list[str]
) -> pl.DataFrame:
    """Load input dataset and apply analysis preprocessing to specified columns"""
    project_id = web_context.base.analysis.project_id
    df_raw = web_context.store.load_project_input(project_id)

    # Get semantic info for all columns
    columns_with_semantic = _get_columns_with_semantic(df_raw)
    semantic_dict = {col.name: col for col in columns_with_semantic}

    # Apply transformations to selected columns
    transformed_columns = {}
    for col_name in column_names:
        if col_name in semantic_dict:
            # Apply semantic transformation
            transformed_columns[col_name] = semantic_dict[
                col_name
            ].apply_semantic_transform()
        else:
            # Keep original if no semantic transformation
            transformed_columns[col_name] = df_raw[col_name]

    return df_raw.with_columns(
        [transformed_columns[col_name].alias(col_name) for col_name in column_names]
    )


def factory(
    web_context: WebPresenterContext,
) -> FactoryOutputContext:
    # Load the primary output associated with this project
    df_hashtags = pl.read_parquet(web_context.base.table(OUTPUT_GINI).parquet_path)

    # Get user-selected column names
    orig2inputschema = {
        v: k for k, v in web_context.base.analysis.column_mapping.items()
    }
    orig_schema_names = [v for v in orig2inputschema.keys()]

    # Load and apply semantic transformations to
    # input data frame
    df_raw = load_and_transform_input_data(
        web_context=web_context, column_names=orig_schema_names
    )

    # Rename columns to follow input schema names and select
    column_mapping = web_context.base.analysis.column_mapping
    df_raw = df_raw.select(
        [
            pl.col(orig_col).alias(schema_col)
            for schema_col, orig_col in column_mapping.items()
        ]
    ).sort(pl.col(COL_TIME))

    set_df_global_state(
        df_input=df_raw,
        df_output=df_hashtags,
    )

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
                analysis_panel,
                layout_columns(
                    hashtag_plot_panel,
                    users_plot_panel,
                ),
                tweet_explorer,
            ),
        )
    )
