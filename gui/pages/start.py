from nicegui import ui

from gui.base import GuiPage, GuiSession, gui_routes


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
        with (
            ui.column()
            .classes("items-center justify-center")
            .style("height: 80vh; width: 100%")
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
