from datetime import datetime
from traceback import format_exc
from typing import Optional

from nicegui import ui

from app import AnalysisContext
from components.select_analysis import analysis_label, present_timestamp
from gui.base import GuiPage, GuiSession, gui_routes
from gui.components import ToggleButtonGroup
from gui.import_options import ImportOptionsDialog


# wrapper function to create a page with two buttons
def _two_button_choice_fork_content(
    prompt: str,
    left_button_label: str,
    left_button_on_click: callable,
    left_button_icon: str,
    right_button_label: str,
    right_button_on_click: callable,
    right_button_icon: str,
):

    # Main content area - centered vertically
    with ui.column().classes("items-center justify-center").style(
        "height: 80vh; width: 100%"
    ):
        # Prompt label
        ui.label(prompt).classes("q-mb-lg").style("font-size: 1.05rem")

        # Action buttons row
        with ui.row().classes("gap-4"):
            ui.button(
                left_button_label,
                on_click=left_button_on_click,
                icon=left_button_icon,
                color="primary",
            )

            ui.button(
                right_button_label,
                on_click=right_button_on_click,
                icon=right_button_icon,
                color="primary",
            )


class StartPage(GuiPage):
    """
    Main/home page of the application.

    Displays welcome message and primary navigation buttons for
    creating a new project or viewing existing projects.
    """

    def __init__(self, session: GuiSession):
        super().__init__(
            session=session,
            route="/",
            title="CIB Mango Tree",
            show_back_button=False,  # Home page - no back navigation
            show_footer=True,
        )

    def render_content(self) -> None:
        """Render main page content with action buttons."""
        # Main content area - centered vertically
        with ui.column().classes("items-center justify-center").style(
            "height: 80vh; width: 100%"
        ):
            # Prompt label
            ui.label("Let's get started! What do you want to do?").classes(
                "q-mb-lg"
            ).style("font-size: 1.05rem")

            # Action buttons row
            with ui.row().classes("gap-4"):
                ui.button(
                    "New Project",
                    on_click=lambda: self.navigate_to(gui_routes.new_project),
                    icon="add",
                    color="primary",
                )

                ui.button(
                    "Show Existing Projects",
                    on_click=lambda: self.navigate_to(gui_routes.select_project),
                    icon="folder",
                    color="primary",
                )


class SelectProjectPage(GuiPage):
    """
    Projects list page showing existing projects.

    Allows users to select an existing project to work with.
    """

    def __init__(self, session: GuiSession):
        super().__init__(
            session=session,
            route="/select_project",
            title="CIB Mango Tree",
            show_back_button=True,
            back_route="/",
            show_footer=True,
        )

    def render_content(self) -> None:
        """Render projects list with selection interface."""
        # Projects list - centered
        with ui.row().classes("items-center center-justify").style(
            "max-width: 600px; margin: 0 auto;"
        ):
            # Get projects from app via session
            projects = self.session.app.list_projects()

            if not projects:
                # No projects found - show message
                with ui.column().classes("items-center q-mt-lg"):
                    ui.label("No existing projects found.").classes("text-grey")
                    ui.label("Create a new project to get started.").classes(
                        "text-grey"
                    )
            else:
                # Create dropdown with project names
                project_options = {
                    project.display_name: project for project in projects
                }

                with ui.column().classes("items-center justify-center gap-6").style(
                    "width: 100%; max-width: 600px; margin: 0 auto; height: 80vh;"
                ):
                    selected_project = (
                        ui.select(
                            label="Select a project",
                            options=list(project_options.keys()),
                            with_input=True,
                        )
                        .classes("q-mt-md")
                        .style("width: 100%; max-width: 400px")
                    )

                    def on_project_selected():
                        """Handle project selection and navigate to analyzer page."""
                        if selected_project.value:
                            # Store selected project in session
                            self.session.current_project = project_options[
                                selected_project.value
                            ]
                            self.notify_success(
                                f"Selected project: {self.session.current_project.display_name}"
                            )
                            self.navigate_to(gui_routes.select_analyzer_fork)

                    async def open_manage_projects():
                        """Open the Manage Projects dialog."""
                        from gui.projects import ManageProjectsDialog

                        dialog = ManageProjectsDialog(session=self.session)
                        result = await dialog

                        # If a project_id exists, show notification and refresh
                        # result -> (is_deleted, project_name, project_id)
                        if result[0]:
                            self.notify_success(
                                f"Successfully deleted project: {result[1]} (ID: {result[2]})"
                            )

                    with ui.row().classes("items-center center-justify"):

                        ui.button(
                            "Manage Projects",
                            on_click=open_manage_projects,
                            icon="settings",
                            color="secondary",
                        ).props("outline").classes("q-mt-md")

                        ui.button(
                            "Open Project",
                            on_click=on_project_selected,
                            icon="arrow_forward",
                            color="primary",
                        ).classes("q-mt-md")


class NewProjectPage(GuiPage):

    def __init__(self, session: GuiSession):
        super().__init__(
            session=session,
            route="/new_project",
            title="New Project",
            show_back_button=True,
            back_route="/",
            show_footer=True,
        )

    def render_content(self) -> None:

        # Main content - centered vertically and horizontally
        with ui.column().classes("items-center justify-center gap-6").style(
            "width: 100%; max-width: 600px; margin: 0 auto; height: 80vh;"
        ):
            # Store the input widget locally (not in session)
            new_project_name_input = ui.input(
                label="New Project Name",
                placeholder="e.g. Twitter-2018-dataset",
            )

            def _on_next():
                # Capture the input value when user clicks Next
                project_name = new_project_name_input.value

                # Validate the string value
                if not project_name or not project_name.strip():
                    self.notify_warning("Please enter a project name")
                    return

                # Store validated value in session
                self.session.new_project_name = project_name
                self.navigate_to(gui_routes.import_dataset)

            ui.button(
                text="Next: Select Dataset",
                icon="arrow_forward",
                on_click=_on_next,
                color="primary",
            )


class ImportDatasetPage(GuiPage):
    """
    Dataset import page for selecting a file.

    Allows users to:
    1. Browse for CSV/Excel files
    2. View file information
    3. Proceed to data preview
    """

    def __init__(self, session: GuiSession):
        super().__init__(
            session=session,
            route=gui_routes.import_dataset,
            title="Import Dataset",
            show_back_button=True,
            back_route=gui_routes.new_project,
            show_footer=True,
        )

    def render_content(self) -> None:
        """Render file selection interface."""
        import os
        from datetime import datetime

        from gui.base import format_file_size
        from gui.file_picker import LocalFilePicker

        # Page state - store selected file path locally
        selected_file_path = None

        # Main content - centered vertically and horizontally
        with ui.column().classes("items-center justify-center gap-6").style(
            "width: 100%; max-width: 800px; margin: 0 auto; height: 80vh;"
        ):
            ui.label("Choose a dataset file.").classes("text-lg")

            # File info card (initially hidden)
            file_info_card = ui.card().style("display: none;")
            with file_info_card:
                file_name_label = ui.label().classes("text-sm")
                file_path_label = ui.label().classes("text-sm")
                file_size_label = ui.label().classes("text-sm")
                file_modified_label = ui.label().classes("text-sm")

                with ui.row().classes("w-full justify-end gap-2 mt-4"):
                    change_file_btn = ui.button(
                        "Pick a different file",
                        icon="edit",
                        color="secondary",
                        on_click=lambda: None,
                    ).props("outline")
                    preview_btn = ui.button(
                        "Next: Preview Data", icon="arrow_forward", color="primary"
                    )

            # Browse button
            async def browse_for_file():
                nonlocal selected_file_path

                picker = LocalFilePicker(
                    state=self.session.app.file_selector_state,
                    file_extensions=[".csv", ".xlsx"],
                )
                result = await picker

                if result:
                    selected_file_path = result

                    # Show file info
                    file_stats = os.stat(result)
                    file_size = format_file_size(file_stats.st_size)
                    file_modified = datetime.fromtimestamp(
                        file_stats.st_mtime
                    ).strftime("%Y-%m-%d %H:%M:%S")

                    file_name_label.text = f"Dataset file: {os.path.basename(result)}"
                    file_path_label.text = f"Location: {result}"
                    file_size_label.text = f"Size: {file_size}"
                    file_modified_label.text = f"Modified: {file_modified}"

                    file_info_card.style("display: block;")
                    browse_btn.set_visibility(False)

                    self.notify_success("File selected successfully")

            def navigate_to_preview():
                """Navigate to preview page with selected file path."""
                if not selected_file_path:
                    self.notify_warning("No file selected")
                    return

                # Store file path in session
                self.session.selected_file_path = selected_file_path
                self.navigate_to("/preview_dataset")

            browse_btn = ui.button(
                "Browse files",
                icon="folder_open",
                on_click=browse_for_file,
                color="primary",
            )

            # Wire up buttons
            preview_btn.on("click", navigate_to_preview)

            change_file_btn.on(
                "click",
                lambda: (
                    file_info_card.style("display: none;"),
                    browse_btn.set_visibility(True),
                ),
            )


class SelectAnalyzerForkPage(GuiPage):
    """A forking page with two buttons for either advancing to start a new analysis or selecting an old one"""

    def __init__(self, session: GuiSession):
        super().__init__(
            session=session,
            route=gui_routes.select_analyzer_fork,
            title=f"{session.current_project.display_name}",
            show_back_button=True,
            back_route=gui_routes.select_project,
            show_footer=True,
        )

    def render_content(self):

        _two_button_choice_fork_content(
            prompt="What do you want to do next?",
            left_button_label="Start a New Test",
            left_button_icon="computer",
            left_button_on_click=lambda: self.navigate_to(gui_routes.select_analyzer),
            right_button_label="Review a Previous Test",
            right_button_on_click=lambda: self.navigate_to(
                gui_routes.select_previous_analyzer
            ),
            right_button_icon="refresh",
        )


class SelectNewAnalyzerPage(GuiPage):
    """
    Page for selecting a new analyzer to run.
    """

    def __init__(self, session: GuiSession):
        super().__init__(
            session=session,
            route=gui_routes.select_analyzer,
            title=f"{session.current_project.display_name}: Select New Analyzer",
            show_back_button=True,
            back_route=gui_routes.select_analyzer_fork,
            show_footer=True,
        )

    def render_content(self) -> None:
        """Render new analyzer selection interface."""
        # Show success message if project was just created
        if self.session.new_project_name:
            self.notify_success(f"Created project: {self.session.new_project_name}!")
            # Clear the name after showing notification
            self.session.new_project_name = None

        # Ensure a project is selected
        if not self.session.current_project:
            self.notify_warning("No project selected. Redirecting...")
            self.navigate_to("/select_project")
            return

        # Main content - centered
        with ui.column().classes("items-center justify-center gap-6").style(
            "width: 100%; max-width: 800px; margin: 0 auto; height: 80vh;"
        ):
            ui.label("Start a New Analysis").classes("text-lg")

            # Get primary analyzers from suite
            analyzers = self.session.app.context.suite.primary_anlyzers

            if not analyzers:
                ui.label("No analyzers available").classes("text-grey")
            else:
                # Create radio options from analyzers
                analyzer_options = {
                    analyzer.name: analyzer.short_description for analyzer in analyzers
                }

                # Create toggle button group for analyzer selection
                button_group = ToggleButtonGroup()
                with ui.row().classes("items-center justify-center gap-4"):

                    # add a button for each analyzer
                    for analyzer_name in analyzer_options.keys():
                        button_group.add_button(analyzer_name)

                with ui.card().classes("w-full no-shadow"):

                    DEFAULT_TEXT = (
                        "No analyzer selected. Click button above to select it."
                    )

                    ui.label().bind_text_from(
                        target_object=button_group,
                        target_name="selected_text",
                        backward=lambda text: analyzer_options.get(text, DEFAULT_TEXT),
                    ).classes("text-center w-full")

                with ui.row().classes("w-full justify-end mt-6"):

                    def _on_proceed():
                        """Handle proceed button click."""
                        # Get current selection
                        new_selection = button_group.get_selected_text()

                        # Validation: none selected
                        if not new_selection:
                            self.notify_warning("Please select an analyzer")
                            return

                        # Find the analyzer interface by name
                        selected_analyzer = next(
                            (a for a in analyzers if a.name == new_selection), None
                        )

                        if not selected_analyzer:
                            self.notify_error("Could not find selected analyzer")
                            return

                        # Store selected analyzer interface and name in session
                        self.session.selected_analyzer = selected_analyzer
                        self.session.selected_analyzer_name = new_selection

                        self.navigate_to("/configure_analysis")

                    ui.button(
                        "Configure Analysis",
                        icon="arrow_forward",
                        color="primary",
                        on_click=_on_proceed,
                    )


class SelectPreviousAnalyzerPage(GuiPage):
    """
    Page for selecting a previous analysis to review.
    """

    grid: Optional[ui.aggrid] = None

    def __init__(self, session: GuiSession):
        super().__init__(
            session=session,
            route=gui_routes.select_previous_analyzer,
            title=f"{session.current_project.display_name}: Select Previous Analysis",
            show_back_button=True,
            back_route=gui_routes.select_analyzer_fork,
            show_footer=True,
        )

    def render_content(self) -> None:
        """Render previous analysis selection interface."""
        # Ensure a project is selected
        if not self.session.current_project:
            self.notify_warning("No project selected. Redirecting...")
            self.navigate_to("/select_project")
            return

        # Main content - centered
        with ui.column().classes("items-center justify-center gap-6").style(
            "width: 100%; max-width: 800px; margin: 0 auto; height: 80vh;"
        ):
            ui.label("Review a Previous Analysis").classes("text-lg")

            # Populate list of existing analyses
            now = datetime.now()
            analysis_list = sorted(
                [
                    (
                        analysis_label(analysis, now),
                        analysis,
                    )
                    for analysis in self.session.current_project.list_analyses()
                ],
                key=lambda option: option[0],
            )

            if analysis_list:
                self._render_previous_analyses_grid(entries=analysis_list)
            else:
                ui.label("No previous tests have been found.").classes("text-grey")

            async def _on_proceed():
                """Handle proceed button click."""
                # Get selected previous analysis if grid exists
                selected_name = None
                if analysis_list:
                    selected_rows = await self.grid.get_selected_rows()
                    if selected_rows:
                        selected_name = selected_rows[0]["name"]

                # Validation: none selected
                if not selected_name:
                    self.notify_warning("Please select a previous analysis")
                    return

                # Find the analysis object by display_name
                selected_analysis = next(
                    (a for _, a in analysis_list if a.display_name == selected_name),
                    None,
                )

                # Store selected analysis in session
                # if selected_analysis:
                #    self.session.current_analysis = selected_analysis
                #    self.navigate_to("/show_output_options")

            ui.button(
                "Proceed",
                icon="arrow_forward",
                color="primary",
                on_click=_on_proceed,
            )

    def _render_previous_analyses_grid(
        self, entries: list[tuple[str, AnalysisContext]]
    ):
        """Render grid of previous analyses."""
        now = datetime.now()

        data = {
            "columnDefs": [
                {"headerName": "Analyzer Name", "field": "name"},
                {"headerName": "Date Created", "field": "date"},
            ],
            "rowData": [
                {
                    "name": analysis_context.display_name,
                    "date": (
                        present_timestamp(analysis_context.create_time, now)
                        if analysis_context.create_time
                        else "Unknown"
                    ),
                }
                for label, analysis_context in entries
            ],
            "rowSelection": {"mode": "singleRow"},
        }

        self.grid = ui.aggrid(
            data,
            theme="quartz",
        ).classes("w-full h-64")


class PreviewDatasetPage(GuiPage):
    """
    Data preview page showing a sample of the imported dataset.

    Allows users to:
    1. View first 5 rows of data with column info
    2. Adjust import options (delimiter, encoding, etc.)
    3. Confirm and create project with imported data
    """

    def __init__(self, session: GuiSession):
        super().__init__(
            session=session,
            route=gui_routes.preview_dataset,
            title="Data Preview",
            show_back_button=True,
            back_route=gui_routes.import_dataset,
            show_footer=True,
        )

    def render_content(self) -> None:
        """Render data preview interface with import options."""
        from importing import importers

        # Validate file is selected
        if not self.session.selected_file_path:
            self.notify_warning("No file selected. Redirecting...")
            self.navigate_to(gui_routes.import_dataset)
            return

        # Auto-detect importer
        importer = None
        for imp in importers:
            if imp.suggest(self.session.selected_file_path):
                importer = imp
                break

        if not importer:
            self.notify_error("Could not detect file format")
            self.navigate_to(gui_routes.import_dataset)
            return

        # Initialize import session and load preview
        try:
            import_session = importer.init_session(self.session.selected_file_path)
            if not import_session:
                raise ValueError("Failed to initialize import session")

            # Store session for later use
            self.session.import_session = import_session

            N_ROWS_FOR_PREVIEW = 5
            import_preview = import_session.load_preview(n_records=N_ROWS_FOR_PREVIEW)

            # Container for dynamic preview updates
            data_preview_container = None

            # Retry callback for import options dialog
            async def handle_retry(updated_session):
                """Handle retry from import options dialog."""
                nonlocal import_preview

                try:
                    # Update session in GuiSession
                    self.session.import_session = updated_session

                    # Reload preview with new settings
                    import_preview = updated_session.load_preview(
                        n_records=N_ROWS_FOR_PREVIEW
                    )

                    # Clear and rebuild data preview
                    data_preview_container.clear()
                    with data_preview_container:
                        self._make_preview_grid(import_preview)

                    self.notify_success("Preview updated successfully!")

                except Exception as e:
                    self.notify_error(f"Error: {str(e)}")
                    print(f"Retry import error:\n{format_exc()}")

            # Open import options dialog
            async def open_import_options():
                dialog = ImportOptionsDialog(
                    import_session=self.session.import_session,
                    selected_file_path=self.session.selected_file_path,
                    on_retry=handle_retry,
                )
                await dialog

            # Import and create project
            async def import_data_create_project():
                try:
                    # Create project using session data
                    project = self.session.app.create_project(
                        name=self.session.new_project_name,
                        importer_session=self.session.import_session,
                    )

                    # Store project in session
                    self.session.current_project = project

                    # Navigate to analyzer selection
                    self.navigate_to(gui_routes.select_analyzer)

                except Exception as e:
                    self.notify_error(f"Error creating project: {str(e)}")
                    print(f"Project creation error:\n{format_exc()}")

            # Main content area - centered
            with ui.column().classes("items-center justify-center gap-6").style(
                "width: 100%; max-width: 1200px; margin: 0 auto; padding: 2rem; min-height: 70vh;"
            ):
                # Data Preview (with container for dynamic updates)
                data_preview_container = ui.column().classes("w-full")
                with data_preview_container:
                    self._make_preview_grid(import_preview)

                # Bottom Actions
                with ui.row().classes("w-full justify-center gap-2 mt-4"):
                    ui.button(
                        "Change Import Options",
                        icon="settings",
                        color="secondary",
                        on_click=open_import_options,
                    ).props("outline")

                    ui.button(
                        "Import and Create Project",
                        icon="upload",
                        color="primary",
                        on_click=import_data_create_project,
                    )

        except Exception as e:
            self.notify_error(f"Error loading preview: {str(e)}")
            print(f"Preview error:\n{format_exc()}")
            self.navigate_to(gui_routes.import_dataset)
            return

    def _make_preview_grid(self, data_frame):
        """
        Render preview data grid with column information.

        Args:
            data_frame: Polars DataFrame containing preview data
        """
        ui.label("Data Preview (first 5 rows)").classes("text-lg")

        # Count empty columns
        n_empty = sum((c[0] == 0 for c in data_frame.count().iter_columns()))
        ui.label(
            f"Nr. detected columns: {len(data_frame.columns)} ({n_empty} empty)"
        ).classes("text-sm")

        # Display data grid
        ui.aggrid.from_polars(
            data_frame, theme="quartz", auto_size_columns=False
        ).classes("w-full h-64")


class ConfigureAnalysis(GuiPage):

    def __init__(self, session: GuiSession):
        super().__init__(
            session=session,
            route="/configure_analysis",
            title=f"{session.current_project.display_name}: Configure Analysis",
            show_back_button=True,
            back_route=gui_routes.select_analyzer_fork,
            show_footer=True,
        )

    def render_content(self) -> None:
        from analyzer_interface import column_automap, get_data_type_compatibility_score

        # Get analyzer input requirements and user dataset columns
        analyzer = self.session.selected_analyzer
        input_columns = analyzer.input.columns
        user_columns = self.session.current_project.columns

        # Generate initial auto-mapping
        draft_column_mapping = column_automap(user_columns, input_columns)

        # Main content area
        with ui.column().classes("items-center justify-start gap-6").style(
            "width: 100%; max-width: 1200px; margin: 0 auto; padding: 2rem;"
        ):

            # Store dropdown widgets for later access
            column_dropdowns = {}

            # Create column mapping UI using grid
            with ui.grid(columns=2).classes("w-full gap-4"):

                ui.label("Input Columns")
                ui.label("Dataset Columns")
                for input_col in input_columns:
                    # Left column: Input column info card
                    with ui.card():
                        ui.label(input_col.human_readable_name_or_fallback()).classes(
                            "text-bold text-lg"
                        )
                        if input_col.description:
                            ui.label(input_col.description).classes(
                                "text-sm text-grey-7"
                            )
                        # ui.label(f"Type: {input_col.data_type}").classes("text-sm")

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
                        f"{user_col.name} [{user_col.data_type}]": user_col.name
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

                    # Create dropdown
                    dropdown = (
                        ui.select(
                            options=list(dropdown_options.keys()),
                            label="Select dataset column",
                            value=default_value,
                        )
                        .classes("w-full")
                        .props("use-chips")
                    )

                    # Store reference for later
                    column_dropdowns[input_col.name] = (dropdown, dropdown_options)

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

                ui.button(
                    "Next",
                    icon="arrow_forward",
                    color="primary",
                    on_click=_on_proceed,
                )
