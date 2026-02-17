from nicegui import ui

from gui.base import GuiPage, GuiSession, gui_routes


class RunAnalysisPage(GuiPage):
    """
    Page for running the configured analysis.

    Displays:
    1. Input dataset preview (first 5 rows)
    2. Configured parameters summary
    3. Start Analysis button with progress dialog
    """

    def __init__(self, session: GuiSession):
        super().__init__(
            session=session,
            route=gui_routes.run_analysis,
            title=f"{session.current_project.display_name}: Run Analysis",
            show_back_button=True,
            back_route=gui_routes.configure_analysis_parameters,
            show_footer=True,
        )

    def render_content(self) -> None:
        """Render the run analysis page with preview, params, and start button."""
        # Validate session state
        if not self.session.selected_analyzer:
            self.notify_warning("No analyzer selected. Redirecting...")
            self.navigate_to(gui_routes.select_analyzer)
            return

        if not self.session.column_mapping:
            self.notify_warning("Column mapping not configured. Redirecting...")
            self.navigate_to(gui_routes.configure_analysis)
            return

        if not self.session.analysis_params:
            self.notify_warning("Parameters not configured. Redirecting...")
            self.navigate_to(gui_routes.configure_analysis_parameters)
            return

        analyzer = self.session.selected_analyzer
        project = self.session.current_project
        column_mapping = self.session.column_mapping
        params = self.session.analysis_params

        # Main content area
        with ui.column().classes("items-center justify-start gap-6").style(
            "width: 100%; max-width: 1200px; margin: 0 auto; padding: 2rem;"
        ):
            # Section 1: Dataset Preview
            ui.label("Input Dataset Preview").classes("text-xl font-bold")
            self._render_dataset_preview(project, analyzer, column_mapping)

            ui.separator()

            # Section 2: Parameters Summary
            ui.label("Analysis Parameters").classes("text-xl font-bold")
            self._render_parameters_summary(analyzer, params)

            ui.separator()

            # Section 3: Start Analysis Button
            with ui.row().classes("w-full justify-end mt-6"):
                ui.button(
                    "Start Analysis",
                    icon="play_arrow",
                    color="primary",
                    on_click=lambda: self._run_analysis(),
                ).classes("text-lg")

    def _render_dataset_preview(self, project, analyzer, column_mapping):
        """Render preview of input dataset (first 5 rows)."""
        import polars as pl

        # Get first 5 rows of data with mapped columns
        tmp_col = list(project.column_dict.values())[0]
        N_PREVIEW_ROWS = min(5, tmp_col.data.len())

        preview_data = {}
        for analyzer_col in analyzer.input.columns:
            col_name = analyzer_col.human_readable_name_or_fallback()
            user_col_name = column_mapping.get(analyzer_col.name)

            if user_col_name and user_col_name in project.column_dict:
                user_col = project.column_dict[user_col_name]
                preview_data[col_name] = user_col.head(
                    N_PREVIEW_ROWS
                ).apply_semantic_transform()
            else:
                preview_data[col_name] = [None] * N_PREVIEW_ROWS

        preview_df = pl.DataFrame(preview_data)

        # Display preview
        preview_title = (
            "First 5 rows" if len(preview_df) >= 5 else f"All {len(preview_df)} rows"
        )
        ui.label(preview_title).classes("text-sm text-grey-7")
        ui.aggrid.from_polars(preview_df, theme="quartz").classes("w-full h-64")

    def _render_parameters_summary(self, analyzer, params):
        """Render summary of configured parameters."""
        if not analyzer.params:
            ui.label("This analyzer has no configurable parameters.").classes(
                "text-grey-7"
            )
            return

        with ui.card().classes("w-full"):
            with ui.column().classes("gap-2"):
                for param in analyzer.params:
                    param_value = params.get(param.id)
                    if param_value is not None:
                        with ui.row().classes("items-center gap-2"):
                            ui.label(f"{param.print_name}:").classes(
                                "text-base font-bold"
                            )
                            ui.label(str(param_value)).classes("text-base")

    async def _run_analysis(self):
        """Execute the analysis with progress dialog."""
        from traceback import format_exc

        project = self.session.current_project
        analyzer = self.session.selected_analyzer
        column_mapping = self.session.column_mapping
        params = self.session.analysis_params

        # Create the analysis (persists to storage)
        analysis_context = project.create_analysis(
            primary_analyzer_id=analyzer.id,
            column_mapping=column_mapping,
            param_values=params,
        )

        # Create progress dialog
        with ui.dialog() as progress_dialog, ui.card():
            ui.label("Running Analysis...").classes("text-h6")
            ui.linear_progress().props("indeterminate")
            progress_label = ui.label("Initializing...").classes("text-body2")

        progress_dialog.open()

        try:
            # Run the analysis generator
            for event in analysis_context.run():
                if event.event == "start":
                    if event.analyzer.kind == "primary":
                        progress_label.text = "Starting base analysis for the test..."
                    else:
                        progress_label.text = (
                            f"Running post-analysis: {event.analyzer.name}"
                        )
                elif event.event == "finish":
                    progress_label.text = f"Completed: {event.analyzer.name}"

            # Analysis complete
            progress_dialog.close()
            self.notify_success("Analysis completed successfully!")

        except KeyboardInterrupt:
            progress_dialog.close()
            self.notify_warning("Analysis was canceled")
            # Delete draft analysis
            if analysis_context.is_draft:
                analysis_context.delete()

        except Exception as e:
            progress_dialog.close()
            self.notify_error(f"Analysis failed: {str(e)}")

            # Show traceback option
            with ui.dialog() as error_dialog, ui.card():
                ui.label("Error Details").classes("text-h6")
                ui.label(str(e)).classes("text-body2")

                if await ui.dialog().props("persistent").open():
                    traceback = format_exc()
                    ui.label("Full Traceback:").classes("text-body2 font-bold")
                    ui.label(traceback).classes("text-body2 font-mono")

                ui.button("Close", on_click=error_dialog.close)

            error_dialog.open()

            # Delete draft analysis
            if analysis_context.is_draft:
                analysis_context.delete()
