import asyncio
from traceback import format_exc

from nicegui import ui

from gui.base import GuiPage, GuiSession, gui_routes


class RunAnalysisPage(GuiPage):
    """
    Page that executes the analysis and shows progress.

    After parameter configuration, this page:
    1. Creates an AnalysisContext using project.create_analysis()
    2. Runs the analysis via analysis.run() generator
    3. Shows progress and status updates
    4. Handles errors and cleanup of draft analyses
    5. On success, navigates to AnalysisOptionsPage
    """

    def __init__(self, session: GuiSession):
        super().__init__(
            session=session,
            route=gui_routes.run_analysis,
            title=f"{session.current_project.display_name}: Running Analysis",
            show_back_button=False,  # Prevent navigation during analysis
            show_footer=True,
        )

    def render_content(self) -> None:
        """Render the analysis execution page with progress tracking."""
        # Validate required session data
        if not self.session.selected_analyzer:
            self.notify_warning("No analyzer selected. Redirecting...")
            self.navigate_to(gui_routes.select_analyzer)
            return

        if not self.session.column_mapping:
            self.notify_warning("Column mapping not configured. Redirecting...")
            self.navigate_to(gui_routes.configure_analysis)
            return

        if self.session.analysis_params is None:
            self.notify_warning("Parameters not configured. Redirecting...")
            self.navigate_to(gui_routes.configure_analysis_parameters)
            return

        analyzer = self.session.selected_analyzer
        project = self.session.current_project

        # Create the analysis context
        try:
            analysis = project.create_analysis(
                analyzer.id,
                self.session.column_mapping,
                self.session.analysis_params,
            )
        except Exception as e:
            self.notify_error(f"Failed to create analysis: {str(e)}")
            print(f"Analysis creation error:\n{format_exc()}")
            self.navigate_to(gui_routes.configure_analysis_parameters)
            return

        # Calculate total steps for progress tracking
        secondary_analyzers = (
            self.session.app.context.suite.find_toposorted_secondary_analyzers(analyzer)
        )
        total_steps = 1 + len(secondary_analyzers)  # primary + secondaries

        # State tracking for cancellation
        cancel_requested = False

        def request_cancel():
            """Handle cancel button click."""
            nonlocal cancel_requested
            cancel_requested = True
            cancel_btn.text = "Canceling..."
            cancel_btn.disable()

        # Main content area
        with (
            ui.column()
            .classes("items-center justify-center gap-6")
            .style("width: 50%; max-width: 800px; margin: 0 auto; height: 80vh;")
        ):
            # Progress bar (value from 0.0 to 1.0)
            progress_bar = ui.linear_progress(value=0).classes("w-full")

            # Create checkboxes for each analysis step (read-only, stacked vertically)
            step_checkboxes = []
            with ui.column().classes("w-full gap-1"):
                # Primary analyzer checkbox
                primary_checkbox = ui.checkbox(analyzer.name, value=False).props(
                    "disable"
                )
                step_checkboxes.append(primary_checkbox)

                # Secondary analyzer checkboxes
                for secondary in secondary_analyzers:
                    checkbox = ui.checkbox(secondary.name, value=False).props("disable")
                    step_checkboxes.append(checkbox)

            # Log container (plain, no card wrapper)
            log_container = ui.column().classes("w-full gap-1")

            # Buttons container
            buttons_container = ui.row().classes("gap-4")
            with buttons_container:
                # Cancel button
                cancel_btn = ui.button(
                    "Cancel Analysis",
                    icon="stop",
                    color="secondary",
                    on_click=request_cancel,
                ).props("outline")

                # Return button for errors (initially hidden)
                return_btn = ui.button(
                    "Return to Parameters",
                    icon="arrow_back",
                    color="secondary",
                    on_click=lambda: self.navigate_to(
                        gui_routes.configure_analysis_parameters
                    ),
                )

                # Success button (initially hidden)
                success_btn = ui.button(
                    "Continue",
                    icon="arrow_forward",
                    color="primary",
                    on_click=lambda: self.navigate_to(gui_routes.analysis_options),
                )
                success_btn.disable()

        # Run analysis asynchronously
        async def run_analysis_task():
            nonlocal cancel_requested
            current_step = 0

            try:
                for event in analysis.run():
                    # Check for cancellation
                    if cancel_requested:
                        with log_container:
                            ui.label("Analysis canceled by user").classes(
                                "text-warning text-sm"
                            )
                        raise KeyboardInterrupt("User canceled analysis")

                    if event.event == "start":
                        current_step += 1

                        # Update progress bar value (0 to 1)
                        progress_bar.value = current_step / total_steps

                    elif event.event == "finish":
                        # Check the corresponding checkbox
                        if current_step > 0 and current_step <= len(step_checkboxes):
                            step_checkboxes[current_step - 1].value = True

                    # Allow UI to update
                    await asyncio.sleep(0.01)

                # Store completed analysis in session
                self.session.current_analysis = analysis

                # Update buttons
                success_btn.enable()
                cancel_btn.disable()

                self.notify_success("Analysis completed!")

            except KeyboardInterrupt:
                # User canceled
                self.notify_warning("Analysis was canceled")

                # Update buttons
                cancel_btn.disable()
                return_btn.set_visibility(True)

            except Exception as e:
                # Error occurred
                self.notify_error(f"Analysis error: {str(e)}")

                with log_container:
                    ui.label(f"Error: {str(e)}").classes(
                        "text-negative font-bold text-sm"
                    )

                print(f"Analysis error:\n{format_exc()}")

                # Update buttons
                cancel_btn.disable()
                return_btn.set_visibility(True)

            finally:
                # Cleanup: delete draft analysis if not completed
                if analysis.is_draft:
                    analysis.delete()

        # Start the analysis task after a short delay to allow UI to render
        ui.timer(0.1, run_analysis_task, once=True)
