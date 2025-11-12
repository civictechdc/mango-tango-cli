from datetime import datetime
from traceback import format_exc

from nicegui import ui

from components.select_analysis import analysis_label
from gui.base import GuiPage, GuiSession, gui_routes
from gui.components import ToggleButtonGroup
from gui.import_options import ImportOptionsDialog


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
                    on_click=lambda: self.navigate_to("/new_project"),
                    icon="add",
                    color="primary",
                )

                ui.button(
                    "Show Existing Projects",
                    on_click=lambda: self.navigate_to("/select_project"),
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
                            self.navigate_to("/select_analyzer")

                    async def open_manage_projects():
                        """Open the Manage Projects dialog."""
                        from gui.projects import ManageProjectsDialog

                        dialog = ManageProjectsDialog(session=self.session)
                        result = await dialog

                        # If projects were deleted, refresh the page
                        if result:
                            self.notify_success("Projects updated. Refreshing...")
                            ui.navigate.reload()

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


class SelectAnalyzerPage(GuiPage):
    """
    Analyzer selection page for a project.

    Allows users to either:
    1. Select a new analyzer to run
    2. Review a previous analysis
    """

    def __init__(self, session: GuiSession):
        super().__init__(
            session=session,
            route="/select_analyzer",
            title=f"{session.current_project.display_name}: Select Analysis",
            show_back_button=True,
            back_route="/select_project",
            show_footer=True,
        )

    def render_content(self) -> None:
        """Render analyzer selection interface."""
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

            with ui.card().classes("items-center justify-center").style("width: 100%"):
                ui.label("Start a New Analysis").classes("text-lg")

                # Get primary analyzers from suite
                analyzers = self.session.app.context.suite.primary_anlyzers

                if not analyzers:
                    ui.label("No analyzers available").classes("text-grey")
                else:
                    # Create radio options from analyzers
                    analyzer_options = {
                        analyzer.name: analyzer.short_description
                        for analyzer in analyzers
                    }

                    # Create toggle button group for analyzer selection
                    button_group = ToggleButtonGroup()
                    with ui.row().classes("items-center justify-center gap-4"):
                        for analyzer_name in analyzer_options.keys():
                            button_group.add_button(analyzer_name)

            ui.label("OR").classes("text-bold-lg")

            with ui.card().classes("items-center justify-center").style("width: 100%"):
                ui.label("Review a Previous Analysis").classes("text-lg")

                # Populate list of existing analyses
                now = datetime.now()
                analysis_options = sorted(
                    [
                        (
                            analysis_label(analysis, now),
                            analysis,
                        )
                        for analysis in self.session.current_project.list_analyses()
                    ],
                    key=lambda option: option[0],
                )

                previous_analyzer = None

                if analysis_options:
                    previous_analyzer = ui.select(
                        label="Select analysis",
                        options=[e[0] for e in analysis_options],
                    )
                else:
                    ui.label("No previous tests have been found.").classes("text-grey")

            def _on_proceed():
                """Handle proceed button click."""
                # Get current selections
                new_selection = button_group.get_selected_text()
                prev_selection = previous_analyzer.value if previous_analyzer else None

                # Validation: both selected
                if new_selection and prev_selection:
                    self.notify_warning(
                        "Please choose either a new analyzer OR a previous analysis, not both"
                    )
                    return

                # Validation: none selected
                if not new_selection and not prev_selection:
                    self.notify_warning("Please select an analyzer")
                    return

                # Valid selection - proceed
                if new_selection:
                    # Store selected analyzer in session
                    self.session.selected_analyzer = new_selection
                    self.notify_success(f"New analyzer: {new_selection}")
                    # TODO: Navigate to /configure_analysis with new analyzer
                    # self.navigate_to("/configure_analysis")
                else:
                    # Store selected analysis in session
                    # Find the analysis object from the label
                    selected_analysis = next(
                        (a for label, a in analysis_options if label == prev_selection),
                        None,
                    )
                    if selected_analysis:
                        self.session.current_analysis = selected_analysis
                        self.notify_success(f"Previous analysis: {prev_selection}")
                        # TODO: Navigate to /view_analysis with previous results
                        # self.navigate_to("/view_analysis")

            ui.button(
                "Proceed",
                icon="arrow_forward",
                color="primary",
                on_click=_on_proceed,
            )


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
