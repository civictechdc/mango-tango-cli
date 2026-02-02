from datetime import datetime
from nicegui import ui
from gui.base import GuiPage, GuiSession, gui_routes
from app.analysis_context import AnalysisContext
from components.select_analysis import analysis_label, present_timestamp


class SelectPreviousAnalyzerPage(GuiPage):
    """
    Page for selecting a previous analysis to review.
    """

    grid: ui.aggrid | None = None

    def __init__(self, session: GuiSession):
        select_previous_title: str = "Select Previous Analysis"
        super().__init__(
            session=session,
            route=gui_routes.select_previous_analyzer,
            title=f"{session.current_project.display_name}: {select_previous_title}"
            if session.current_project is not None
            else select_previous_title,
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
        with (
            ui.column()
            .classes("items-center justify-center gap-6")
            .style("width: 100%; max-width: 800px; margin: 0 auto; height: 80vh;")
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
                    if self.grid is None:
                        return

                    selected_rows = await self.grid.get_selected_rows()
                    if selected_rows:
                        selected_name = selected_rows[0]["name"]

                # Validation: none selected
                if not selected_name:
                    self.notify_warning("Please select a previous analysis")
                    return

                else:
                    self.notify_warning("Coming soon!")

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
