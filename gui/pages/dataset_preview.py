from io import BytesIO
from traceback import format_exc
from typing import cast

from nicegui import ui

from gui.base import GuiPage, GuiSession, gui_routes
from gui.import_options import ImportOptionsDialog
from importing import importers


class PreviewDatasetPage(GuiPage):
    """
    Data preview page showing a sample of the imported dataset.

    Allows users to:
    1. View first 5 rows of data with column info
    2. Adjust import options (delimiter, encoding, etc.)
    3. Confirm and create project with imported data
    """

    def __init__(self, session: GuiSession):
        super().__init__(
            session=session,
            route=gui_routes.preview_dataset,
            title="Data Preview",
            show_back_button=True,
            back_route=gui_routes.import_dataset,
            show_footer=True,
        )

    def _selected_file_does_not_exists(self) -> bool:
        return (
            not self.session.selected_file_content_type
            or not self.session.selected_file
            or not self.session.selected_file_name
        )

    def render_content(self) -> None:
        # Validate file is selected
        if self._selected_file_does_not_exists():
            self.notify_warning("No file selected. Redirecting...")
            self.navigate_to(gui_routes.import_dataset)
            return

        # Auto-detect importer
        importer = None
        for imp in importers:
            if imp.suggest(cast(str, self.session.selected_file_content_type)):
                importer = imp
                break

        if not importer:
            self.notify_error("Could not detect file format")
            self.navigate_to(gui_routes.import_dataset)
            return

        # Initialize import session and load preview
        try:
            import_session = importer.init_session(
                cast(BytesIO, self.session.selected_file)
            )
            if not import_session:
                raise ValueError("Failed to initialize import session")

            # Store session for later use
            self.session.import_session = import_session

            N_ROWS_FOR_PREVIEW = 5
            import_preview = import_session.load_preview(n_records=N_ROWS_FOR_PREVIEW)

            # Container for dynamic preview updates
            data_preview_container = None

            # Retry callback for import options dialog
            async def handle_retry(updated_session):
                """Handle retry from import options dialog."""
                if data_preview_container is None:
                    return

                nonlocal import_preview

                try:
                    # Update session in GuiSession
                    self.session.import_session = updated_session

                    # Reload preview with new settings
                    import_preview = updated_session.load_preview(
                        n_records=N_ROWS_FOR_PREVIEW
                    )

                    # Clear and rebuild data preview
                    data_preview_container.clear()
                    with data_preview_container:
                        self._make_preview_grid(import_preview)

                    self.notify_success("Preview updated successfully!")

                except Exception as e:
                    self.notify_error(f"Error: {str(e)}")
                    print(f"Retry import error:\n{format_exc()}")

            # Open import options dialog
            async def open_import_options():
                if (
                    self.session.import_session is None
                    or self._selected_file_does_not_exists()
                ):
                    return

                dialog = ImportOptionsDialog(
                    import_session=self.session.import_session,
                    selected_file=cast(BytesIO, self.session.selected_file),
                    on_retry=handle_retry,
                )
                await dialog

            # Import and create project
            async def import_data_create_project():
                try:
                    # Create project using session data
                    project = self.session.app.create_project(
                        name=(
                            self.session.new_project_name
                            if self.session.new_project_name is not None
                            else ""
                        ),
                        importer_session=self.session.import_session,
                    )

                    # Store project in session
                    self.session.current_project = project

                    # Navigate to analyzer selection
                    self.navigate_to(gui_routes.select_analyzer)

                except Exception as e:
                    self.notify_error(f"Error creating project: {str(e)}")
                    print(f"Project creation error:\n{format_exc()}")

            # Main content area - centered
            with (
                ui.column()
                .classes("items-center justify-center gap-6")
                .style(
                    "width: 100%; max-width: 1200px; margin: 0 auto; padding: 2rem; min-height: 70vh;"
                )
            ):
                # Data Preview (with container for dynamic updates)
                data_preview_container = ui.column().classes("w-full")
                with data_preview_container:
                    self._make_preview_grid(import_preview)

                # Bottom Actions
                with ui.row().classes("w-full justify-center gap-2 mt-4"):
                    ui.button(
                        "Change Import Options",
                        icon="settings",
                        color="secondary",
                        on_click=open_import_options,
                    ).props("outline")

                    ui.button(
                        "Import and Create Project",
                        icon="upload",
                        color="primary",
                        on_click=import_data_create_project,
                    )

        except Exception as e:
            self.notify_error(f"Error loading preview: {str(e)}")
            print(f"Preview error:\n{format_exc()}")
            self.navigate_to(gui_routes.import_dataset)
            return

    def _make_preview_grid(self, data_frame):
        """
        Render preview data grid with column information.

        Args:
            data_frame: Polars DataFrame containing preview data
        """
        ui.label("Data Preview (first 5 rows)").classes("text-lg")

        # Count empty columns
        n_empty = sum((c[0] == 0 for c in data_frame.count().iter_columns()))
        ui.label(
            f"Nr. detected columns: {len(data_frame.columns)} ({n_empty} empty)"
        ).classes("text-sm")

        # Display data grid
        ui.aggrid.from_polars(
            data_frame, theme="quartz", auto_size_columns=False
        ).classes("w-full h-64")
