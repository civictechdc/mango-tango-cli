import os
from datetime import datetime
from nicegui import ui
from gui.base import GuiPage, GuiSession, gui_routes, format_file_size
from gui.file_picker import LocalFilePicker
from gui.components import UploadButton


class ImportDatasetPage(GuiPage):
    """
    Dataset import page for selecting a file.

    Allows users to:
    1. Browse for CSV/Excel files
    2. View file information
    3. Proceed to data preview
    """

    def __init__(self, session: GuiSession):
        super().__init__(
            session=session,
            route=gui_routes.import_dataset,
            title="Import Dataset",
            show_back_button=True,
            back_route=gui_routes.new_project,
            show_footer=True,
        )

    def render_content(self) -> None:
        """Render file selection interface."""
        # Page state - store selected file path locally
        selected_file_path = None

        # Main content - centered vertically and horizontally
        with (
            ui.column()
            .classes("items-center justify-center gap-6")
            .style("width: 100%; max-width: 800px; margin: 0 auto; height: 80vh;")
        ):
            ui.label("Choose a dataset file.").classes("text-lg")

            # File info card (initially hidden)
            file_info_card = ui.card().style("display: none;")
            with file_info_card:
                file_name_label = ui.label().classes("text-sm")
                file_path_label = ui.label().classes("text-sm")
                file_size_label = ui.label().classes("text-sm")
                file_modified_label = ui.label().classes("text-sm")

                with ui.row().classes("w-full justify-end gap-2 mt-4"):
                    change_file_btn = ui.button(
                        "Pick a different file",
                        icon="edit",
                        color="secondary",
                        on_click=lambda: None,
                    ).props("outline")
                    preview_btn = ui.button(
                        "Next: Preview Data", icon="arrow_forward", color="primary"
                    )

            # Browse button
            async def browse_for_file():
                nonlocal selected_file_path

                picker = LocalFilePicker(
                    state=self.session.app.file_selector_state,
                    file_extensions=[".csv", ".xlsx"],
                )
                result = await picker

                if result:
                    selected_file_path = result

                    # Show file info
                    file_stats = os.stat(result)
                    file_size = format_file_size(file_stats.st_size)
                    file_modified = datetime.fromtimestamp(
                        file_stats.st_mtime
                    ).strftime("%Y-%m-%d %H:%M:%S")

                    file_name_label.text = f"Dataset file: {os.path.basename(result)}"
                    file_path_label.text = f"Location: {result}"
                    file_size_label.text = f"Size: {file_size}"
                    file_modified_label.text = f"Modified: {file_modified}"

                    file_info_card.style("display: block;")
                    browse_btn.set_visibility(False)

                    self.notify_success("File selected successfully")

            def navigate_to_preview():
                """Navigate to preview page with selected file path."""
                if not selected_file_path:
                    self.notify_warning("No file selected")
                    return

                # Store file path in session
                self.session.selected_file_path = selected_file_path
                self.navigate_to("/preview_dataset")

            upload_button = UploadButton(
                "Browse Files",
                icon="folder_open",
                on_click=lambda e: print(
                    f"click event from upload button: {e.args if e is not None else 'None'}"
                ),
                on_change=lambda e: print(
                    f"change event from upload button: {e.args if e is not None else 'None'}"
                ),
            )
            """
            browse_btn = ui.button(
                "Browse files",
                icon="folder_open",
                on_click=browse_for_file,
                color="primary",
            )

            # Wire up buttons
            preview_btn.on("click", navigate_to_preview)

            change_file_btn.on(
                "click",
                lambda: (
                    file_info_card.style("display: none;"),
                    browse_btn.set_visibility(True),
                ),
            )
            """
