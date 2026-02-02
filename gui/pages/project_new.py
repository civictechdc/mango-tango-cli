from nicegui import ui
from gui.base import GuiPage, GuiSession, gui_routes


class NewProjectPage(GuiPage):
    def __init__(self, session: GuiSession):
        super().__init__(
            session=session,
            route="/new_project",
            title="New Project",
            show_back_button=True,
            back_route="/",
            show_footer=True,
            on_page_exit=lambda: session.reset_project_workflow(),
        )

    def render_content(self) -> None:
        # Main content - centered vertically and horizontally
        with (
            ui.column()
            .classes("items-center justify-center gap-6")
            .style("width: 100%; max-width: 600px; margin: 0 auto; height: 80vh;")
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
