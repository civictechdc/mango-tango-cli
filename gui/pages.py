from nicegui import ui

from gui.base import GuiPage, GuiSession


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
                    on_click=lambda: self.navigate_to("/projects"),
                    icon="folder",
                    color="primary",
                )


class ProjectsPage(GuiPage):
    """
    Projects list page showing existing projects.

    Allows users to select an existing project to work with.
    """

    def __init__(self, session: GuiSession):
        super().__init__(
            session=session,
            route="/projects",
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
