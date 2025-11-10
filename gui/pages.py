from datetime import datetime

from nicegui import ui

from components.select_analysis import analysis_label
from gui.base import GuiPage, GuiSession
from gui.components import ToggleButtonGroup


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

                with ui.column().classes("items-center").style("width: 100%"):
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

                    ui.button(
                        "Open Project",
                        on_click=on_project_selected,
                        icon="arrow_forward",
                        color="primary",
                    ).classes("q-mt-md")


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
            title="Select Analysis",
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
            self.navigate_to("/projects")
            return

        # Main content - centered
        with ui.column().classes("items-center justify-center gap-6").style(
            "width: 100%; max-width: 800px; margin: 0 auto; height: 80vh;"
        ):
            ui.label("Choose an analysis type").classes("text-lg")

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
                with ui.row().classes("gap-4"):
                    for analyzer_name in analyzer_options.keys():
                        button_group.add_button(analyzer_name)

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
                with ui.card():
                    if analysis_options:
                        previous_analyzer = ui.select(
                            label="Review previous analyses",
                            options=[e[0] for e in analysis_options],
                        )
                    else:
                        ui.label("No previous tests have been found.").classes(
                            "text-base"
                        )

                def on_proceed():
                    """Handle proceed button click."""
                    # Get current selections
                    new_selection = button_group.get_selected_text()
                    prev_selection = (
                        previous_analyzer.value if previous_analyzer else None
                    )

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
                            (
                                a
                                for label, a in analysis_options
                                if label == prev_selection
                            ),
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
                    on_click=on_proceed,
                )
