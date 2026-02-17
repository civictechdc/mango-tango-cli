from nicegui import ui

from gui.base import GuiPage, GuiSession, gui_routes
from gui.components import ToggleButtonGroup


class SelectNewAnalyzerPage(GuiPage):
    """
    Page for selecting a new analyzer to run.
    """

    def __init__(self, session: GuiSession):
        analyzer_select_title: str = "Select New Analyzer"
        super().__init__(
            session=session,
            route=gui_routes.select_analyzer,
            title=(
                f"{session.current_project.display_name}: {analyzer_select_title}"
                if session.current_project is not None
                else analyzer_select_title
            ),
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
        with (
            ui.column()
            .classes("items-center justify-center gap-6")
            .style("width: 100%; max-width: 800px; margin: 0 auto; height: 80vh;")
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

                        self.navigate_to(gui_routes.configure_analysis_dataset)

                    ui.button(
                        "Configure Analysis",
                        icon="arrow_forward",
                        color="primary",
                        on_click=_on_proceed,
                    )
