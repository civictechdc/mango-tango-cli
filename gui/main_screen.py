"""
Main GUI screen with title and project selection.
"""

from nicegui import ui

from app import App

# Mango Tree brand color
MANGO_DARK_GREEN = "#609949"
MANGO_ORANGE = "#f3921e"
ACCENT = "white"


def gui_main(app: App):
    """
    Launch the NiceGUI interface with a minimal single screen.

    Args:
        app: The initialized App instance with storage and suite
    """

    @ui.page("/")
    def main_page():

        # Register custom colors FIRST, before any UI elements
        ui.colors(primary=MANGO_DARK_GREEN, secondary=MANGO_ORANGE, accent=ACCENT)

        # Header
        with ui.header(elevated=True):
            ui.label("CIB Mango Tree")

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

                def on_new_project():
                    ui.notify("New Project clicked", color="secondary", type="info")
                    # TODO: Implement new project workflow

                ui.button(
                    "New Project",
                    on_click=on_new_project,
                    icon="add",
                    color="primary",
                )

                ui.button(
                    "Show Existing Projects",
                    on_click=lambda: ui.navigate.to("/projects"),
                    icon="folder",
                    color="primary",
                )

        with ui.footer():
            ui.label("A Civic Tech DC Project")

    @ui.page("/projects")
    def projects_page():
        """Sub-page showing list of existing projects."""

        # Register custom colors FIRST, before any UI elements
        ui.colors(primary=MANGO_DARK_GREEN, secondary=MANGO_ORANGE, accent=ACCENT)

        # Header
        with ui.header(elevated=True):
            ui.button(
                icon="arrow_back", color="accent", on_click=lambda: ui.navigate.to("/")
            ).props("flat")

        # Projects list - centered
        with ui.row().classes("items-center center-justify").style(
            "max-width: 600px; margin: 0 auto;"
        ):

            # Get projects from app
            projects = app.list_projects()

            if not projects:
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
                        if selected_project.value:
                            project = project_options[selected_project.value]
                            ui.notify(
                                f"Selected project: {project.display_name}",
                                type="positive",
                                color="secondary",
                            )
                            # TODO: Navigate to project detail page

                    ui.button(
                        "Open Project",
                        on_click=on_project_selected,
                        icon="arrow_forward",
                        color="primary",
                    ).classes("q-mt-md")

    # Launch in native mode
    ui.run(
        native=True,
        window_size=(800, 600),
        title="CIB Mango Tree",
        favicon="🥭",
        reload=False,
    )
