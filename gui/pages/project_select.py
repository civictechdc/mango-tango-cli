from nicegui import ui

from gui.base import GuiPage, GuiSession, gui_routes


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
        with (
            ui.row()
            .classes("items-center center-justify")
            .style("max-width: 600px; margin: 0 auto;")
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

                with (
                    ui.column()
                    .classes("items-center justify-center gap-6")
                    .style(
                        "width: 100%; max-width: 600px; margin: 0 auto; height: 80vh;"
                    )
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
                        if isinstance(result, tuple) and result[0]:
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
