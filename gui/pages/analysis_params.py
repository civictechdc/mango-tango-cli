from tempfile import TemporaryDirectory

from nicegui import ui

from context import InputColumnProvider, PrimaryAnalyzerDefaultParametersContext
from gui.base import GuiPage, GuiSession, gui_routes
from gui.components import AnalysisParamsCard


class ConfigureAnalaysisParams(GuiPage):
    def __init__(self, session: GuiSession):
        super().__init__(
            session=session,
            route=gui_routes.configure_analysis_parameters,
            title=f"{session.current_project.display_name}: Configure Parameters",
            show_back_button=True,
            back_route=gui_routes.configure_analysis,
            show_footer=True,
        )

    def render_content(self):
        # Validate required session data
        if not self.session.selected_analyzer:
            self.notify_warning("No analyzer selected. Redirecting...")
            self.navigate_to(gui_routes.select_analyzer)
            return

        if not self.session.column_mapping:
            self.notify_warning("Column mapping not configured. Redirecting...")
            self.navigate_to(gui_routes.configure_analysis)
            return

        analyzer = self.session.selected_analyzer
        project = self.session.current_project
        column_mapping = self.session.column_mapping

        # If analyzer has no parameters, skip to next step
        if not analyzer.params:
            self.notify_success("This analyzer has no configurable parameters.")
            self.session.analysis_params = {}
            # TODO: Navigate to next step (run analysis or review page)
            self.notify_success("Ready to run analysis!")
            return

        # Compute default parameter values using backend logic
        with TemporaryDirectory() as temp_dir:
            default_parameters_context = PrimaryAnalyzerDefaultParametersContext(
                analyzer=analyzer,
                store=self.session.app.context.storage,
                temp_dir=temp_dir,
                input_columns={
                    analyzer_column_name: InputColumnProvider(
                        user_column_name=user_column_name,
                        semantic=project.column_dict[user_column_name].semantic,
                    )
                    for analyzer_column_name, user_column_name in column_mapping.items()
                },
            )

            analyzer_decl = self.session.app.context.suite.get_primary_analyzer(
                analyzer.id
            )
            if not analyzer_decl:
                self.notify_error(f"Analyzer `{analyzer.id}` not found")
                self.navigate_to(gui_routes.select_analyzer)
                return

            # Combine static defaults with data-dependent defaults
            param_values = {
                **{
                    param_spec.id: static_param_default_value
                    for param_spec in analyzer_decl.params
                    if (static_param_default_value := param_spec.default) is not None
                },
                # Data-dependent defaults can override static defaults
                **analyzer_decl.default_params(default_parameters_context),
            }
            # Remove None values
            param_values = {
                param_id: param_value
                for param_id, param_value in param_values.items()
                if param_value is not None
            }

        # Main content area
        with (
            ui.column()
            .classes("items-center justify-start gap-6")
            .style("width: 100%; max-width: 1200px; margin: 0 auto; padding: 2rem;")
        ):
            ui.label(f"Configure {analyzer.name} Parameters").classes("text-xl")

            # Create parameter configuration card
            params_card = AnalysisParamsCard(
                params=analyzer.params, default_values=param_values
            )

            # Action button
            with ui.row().classes("w-full justify-end mt-6"):

                def _on_proceed():
                    """Retrieve parameter values and proceed."""
                    final_params = params_card.get_param_values()

                    # Store parameters in session
                    self.session.analysis_params = final_params

                    # TODO: Navigate to next step (run analysis or review page)
                    self.notify_success("Coming soon!")

                ui.button(
                    "Proceed to Run Analysis",
                    icon="arrow_forward",
                    color="primary",
                    on_click=_on_proceed,
                )
