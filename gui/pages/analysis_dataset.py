import polars as pl
from nicegui import ui

from analyzer_interface import column_automap, get_data_type_compatibility_score
from gui.base import GuiPage, GuiSession, gui_routes


class ConfigureAnalysisDatasetPage(GuiPage):
    def __init__(self, session: GuiSession):
        config_analysis_title: str = "Configure Analysis"
        super().__init__(
            session=session,
            route=gui_routes.configure_analysis_dataset,
            title=(
                f"{session.current_project.display_name}: {config_analysis_title}"
                if session.current_project is not None
                else config_analysis_title
            ),
            show_back_button=True,
            back_route=gui_routes.select_analyzer_fork,
            show_footer=True,
        )

    def render_content(self) -> None:
        # Get analyzer input requirements and user dataset columns
        analyzer = self.session.selected_analyzer
        input_columns = analyzer.input.columns
        user_columns = self.session.current_project.columns
        project = self.session.current_project

        # Generate initial auto-mapping
        draft_column_mapping = column_automap(user_columns, input_columns)

        # Main content area
        with (
            ui.column()
            .classes("items-center justify-start gap-6")
            .style("width: 100%; max-width: 1200px; margin: 0 auto; padding: 2rem;")
        ):
            # Store dropdown widgets for later access
            column_dropdowns = {}

            # Helper function to build preview DataFrame
            def _build_preview_df():
                """Build preview DataFrame with currently mapped columns."""
                # Get current mapping from dropdowns
                current_mapping = {}
                for input_col_name, (dropdown, options) in column_dropdowns.items():
                    if dropdown.value:
                        current_mapping[input_col_name] = options[dropdown.value]

                # determine N_PREVIEW here (in most cases,
                # this will be much larger than 5)
                # but in case of demos, let's handle < 5 cases too
                tmp_col = list(project.column_dict.values())[
                    0
                ]  # fetch the first column length
                N_PREVIEW_ROWS = min(5, tmp_col.data.len())

                # Initialize preview_data with all analyzer columns (empty by default)
                preview_data = {}
                for analyzer_col in analyzer.input.columns:
                    col_name = analyzer_col.human_readable_name_or_fallback()
                    user_col_name = current_mapping.get(analyzer_col.name)

                    if user_col_name and user_col_name in project.column_dict:
                        # Column is mapped - use actual data
                        user_col = project.column_dict[user_col_name]
                        preview_data[col_name] = user_col.head(
                            N_PREVIEW_ROWS
                        ).apply_semantic_transform()
                    else:
                        # Column not mapped - create empty column with 5 null values
                        preview_data[col_name] = [None] * N_PREVIEW_ROWS

                return pl.DataFrame(preview_data)

            # Preview container placeholder (will be created after grid)
            preview_container = None

            def update_preview():
                """Rebuild preview when dropdown changes."""
                if preview_container is not None:
                    preview_container.clear()
                    with preview_container:
                        preview_df = _build_preview_df()
                        preview_title = (
                            "Data Preview (first 5 rows)"
                            if len(preview_df) > 5
                            else "Data Preview (all rows)"
                        )
                        ui.label(preview_title).classes("text-sm text-grey-7")
                        ui.aggrid.from_polars(preview_df, theme="quartz").classes(
                            "w-full h-64"
                        )

            # Create column mapping UI using grid
            with ui.grid(columns=2).classes("gap-2"):
                # create labels for grid header
                ui.label("Required Input Information")  # populates row 1, column 1
                ui.label("Imported Dataset Columns")  # pupolates row 1, column 2

                # this then fills the rows with column information
                for input_col in input_columns:
                    # Left column: Input column info card
                    with ui.row().classes("items-center gap-1"):
                        ui.label(input_col.human_readable_name_or_fallback()).classes(
                            "text-bold text-lg"
                        )
                        if input_col.description:
                            with ui.icon("info").classes("text-grey-6 cursor-pointer"):
                                ui.tooltip(input_col.description)

                    # Right column: Dropdown for column selection
                    # Get compatible user columns
                    compatible_columns = [
                        user_col
                        for user_col in user_columns
                        if get_data_type_compatibility_score(
                            input_col.data_type, user_col.data_type
                        )
                        is not None
                    ]

                    # Create dropdown options
                    dropdown_options = {
                        f"{user_col.name}": user_col.name
                        for user_col in compatible_columns
                    }

                    # Pre-select the auto-mapped column
                    default_value = None
                    if input_col.name in draft_column_mapping:
                        mapped_col_name = draft_column_mapping[input_col.name]
                        default_value = next(
                            (
                                k
                                for k, v in dropdown_options.items()
                                if v == mapped_col_name
                            ),
                            None,
                        )

                    # Create dropdown with on_change handler
                    dropdown = (
                        ui.select(
                            options=list(dropdown_options.keys()),
                            label="Select dataset column",
                            value=default_value,
                            on_change=lambda: update_preview(),
                        )
                        .classes("w-40")
                        .props("use-chips")
                    )

                    # Store reference for later
                    column_dropdowns[input_col.name] = (dropdown, dropdown_options)

            # Preview section (created after grid)
            ui.separator()
            preview_container = ui.column().classes("w-full")

            # Initial preview render
            update_preview()

            # Action button
            with ui.row().classes("w-full justify-end"):

                def _on_proceed():
                    """Build column mapping and proceed."""
                    final_mapping = {}
                    for input_col_name, (dropdown, options) in column_dropdowns.items():
                        if dropdown.value:
                            final_mapping[input_col_name] = options[dropdown.value]

                    # Store mapping in session
                    self.session.column_mapping = final_mapping
                    self.notify_success("Column mapping saved!")

                    # Navigate to parameters configuration page
                    self.navigate_to(gui_routes.configure_analysis_parameters)

                ui.button(
                    "Configure Parameters",
                    icon="arrow_forward",
                    color="primary",
                    on_click=_on_proceed,
                )
