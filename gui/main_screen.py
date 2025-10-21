"""
Main GUI screen with title and project selection.
"""

import os
from datetime import datetime
from traceback import format_exc

from nicegui import ui

from app import App
from gui.file_picker import LocalFilePicker
from importing import importers

# Mango Tree brand color
MANGO_DARK_GREEN = "#609949"
MANGO_ORANGE = "#f3921e"
ACCENT = "white"

# Module-level state for native mode (single user)
_selected_file_path = None


def _set_colors():
    return ui.colors(primary=MANGO_DARK_GREEN, secondary=MANGO_ORANGE, accent=ACCENT)


def present_separator(value: str) -> str:
    """Format separator/quote character for display."""
    mapping = {
        "\t": "Tab",
        " ": "Space",
        ",": ", (Comma)",
        ";": "; (Semicolon)",
        "'": "' (Single quote)",
        '"': '" (Double quote)',
        "|": "| (Pipe)",
    }
    return mapping.get(value, value)


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

                    ui.navigate.to("/new_project")

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

    @ui.page("/new_project")
    def new_project():

        # Register custom colors FIRST, before any UI elements
        ui.colors(primary=MANGO_DARK_GREEN, secondary=MANGO_ORANGE, accent=ACCENT)

        # Header
        with ui.header(elevated=True):
            ui.button(
                icon="home", color="accent", on_click=lambda: ui.navigate.to("/")
            ).props("flat")

        with ui.column().classes("items-center center-justify").style(
            "width: 100%; height: 100%"
        ):
            with ui.row(align_items="center"):
                ui.input(
                    label="New Project Name",
                    placeholder="e.g. Twitter-2018-dataset",
                )

            with ui.row(align_items="center"):
                ui.button(
                    text="Next: Select Dataset",
                    icon="arrow_forward",
                    on_click=lambda: ui.navigate.to("/dataset_importing"),
                )

    @ui.page("/dataset_importing")
    def dataset_importing():

        ui.colors(primary=MANGO_DARK_GREEN, secondary=MANGO_ORANGE, accent=ACCENT)

        # Page state
        selected_file_path = None

        with ui.header(elevated=True):
            ui.button(
                text="New Project",
                icon="arrow_back",
                color="accent",
                on_click=lambda: ui.navigate.to("/new_project"),
            ).props("flat")

        with ui.column().classes("items-center justify-center gap-4").style(
            "width: 100%; max-width: 1000px; margin: 0 auto; padding: 2rem;"
        ):
            ui.label("Choose a dataset file.").classes("text-lg")

            # File info card (initially hidden)
            file_info_card = ui.card().classes("w-full").style("display: none;")
            with file_info_card:
                file_name_label = ui.label().classes("text-sm")
                file_path_label = ui.label().classes("text-sm")
                file_size_label = ui.label().classes("text-sm")
                file_modified_label = ui.label().classes("text-sm")

                with ui.row().classes("w-full justify-end gap-2 mt-4"):
                    change_file_btn = ui.button(
                        "Pick a different file", icon="edit", on_click=lambda: None
                    ).props("outline")
                    preview_btn = ui.button(
                        "Next: Preview Data", icon="arrow_forward", color="primary"
                    )

            # Browse button
            async def browse_for_file():
                nonlocal selected_file_path

                picker = LocalFilePicker(
                    state=app.file_selector_state,
                    file_extensions=[".csv", ".xlsx"],
                )
                result = await picker

                if result:
                    selected_file_path = result

                    # Show file info
                    file_stats = os.stat(result)
                    file_size = _format_file_size(file_stats.st_size)
                    file_modified = datetime.fromtimestamp(
                        file_stats.st_mtime
                    ).strftime("%Y-%m-%d %H:%M:%S")

                    file_name_label.text = f"Dataset file: {os.path.basename(result)}"
                    file_path_label.text = f"Location: {result}"
                    file_size_label.text = f"Size: {file_size}"
                    file_modified_label.text = f"Modified: {file_modified}"

                    file_info_card.style("display: block;")
                    browse_btn.set_visibility(False)

                    ui.notify(
                        message="File selected successfully",
                        color="secondary",
                        type="positive",
                    )

            def navigate_to_preview():
                """Navigate to preview page with selected file path."""
                global _selected_file_path

                if not selected_file_path:
                    ui.notify("No file selected", type="warning")
                    return

                # Store file path in module-level variable (native mode, single user)
                _selected_file_path = selected_file_path
                ui.navigate.to("/data_preview")

            def _format_file_size(size_bytes: int) -> str:
                """Format file size in human-readable format."""
                for unit in ["B", "KB", "MB", "GB", "TB"]:
                    if size_bytes < 1024.0:
                        return f"{size_bytes:.1f} {unit}"
                    size_bytes /= 1024.0
                return f"{size_bytes:.1f} PB"

            browse_btn = ui.button(
                "Browse files",
                icon="folder_open",
                on_click=browse_for_file,
                color="primary",
            ).classes("text-lg")

            # Wire up buttons
            preview_btn.on("click", navigate_to_preview)

            change_file_btn.on(
                "click",
                lambda: (
                    file_info_card.style("display: none;"),
                    browse_btn.set_visibility(True),
                ),
            )

    @ui.page("/data_preview")
    def data_preview_page():
        global _selected_file_path

        ui.colors(primary=MANGO_DARK_GREEN, secondary=MANGO_ORANGE, accent=ACCENT)

        # Retrieve file path from module-level variable
        selected_file_path = _selected_file_path

        if not selected_file_path:
            ui.notify("No file selected. Redirecting...", type="warning")
            ui.navigate.to("/dataset_importing")
            return

        with ui.header(elevated=True):
            ui.button(
                icon="arrow_back",
                color="accent",
                on_click=lambda: ui.navigate.to("/dataset_importing"),
            ).props("flat")
            ui.label("Data Preview")

        # Auto-detect importer
        importer = None
        for imp in importers:
            if imp.suggest(selected_file_path):
                importer = imp
                break

        if not importer:
            ui.notify("Could not detect file format", type="negative")
            ui.navigate.to("/dataset_importing")
            return

        # Initialize import session and load preview
        try:
            import_session = importer.init_session(selected_file_path)
            if not import_session:
                raise ValueError("Failed to initialize import session")

            import_preview = import_session.load_preview(10)

            # Declare containers for dynamic updates
            columns_container = None
            data_preview_container = None

            # Main content area
            with ui.column().classes("items-center justify-start gap-4").style(
                "width: 100%; max-width: 1200px; margin: 0 auto; padding: 2rem;"
            ):

                # Section 1: Import Configuration
                with ui.card().classes("w-full"):
                    ui.label("Import Settings").classes("text-h6 mb-3")
                    ui.label(f"Format: {importer.name}").classes(
                        "text-sm font-bold mb-2"
                    )

                    # Display configuration based on importer type
                    from importing.csv import CsvImportSession
                    from importing.excel import ExcelImportSession

                    if isinstance(import_session, CsvImportSession):
                        # Row 1: Column Separator
                        with ui.row().classes("w-full items-center gap-4 mb-3"):
                            ui.label("Column separator:").classes(
                                "text-sm font-bold"
                            ).style("min-width: 150px")
                            separator_toggle = ui.toggle(
                                {
                                    ",": "Comma (,)",
                                    ";": "Semicolon (;)",
                                    "|": "Pipe (|)",
                                    "\t": "Tab",
                                },
                                value=import_session.separator,
                            )

                        # Row 2: Quote Character
                        with ui.row().classes("w-full items-center gap-4 mb-3"):
                            ui.label("Quote character:").classes(
                                "text-sm font-bold"
                            ).style("min-width: 150px")
                            quote_toggle = ui.toggle(
                                {
                                    '"': 'Double quote (")',
                                    "'": "Single quote (')",
                                },
                                value=import_session.quote_char,
                            )

                        # Row 3: Has Header
                        with ui.row().classes("w-full items-center gap-4 mb-3"):
                            ui.label("Has header:").classes("text-sm font-bold").style(
                                "min-width: 150px"
                            )
                            header_toggle = ui.toggle(
                                {True: "Yes", False: "No"},
                                value=import_session.has_header,
                            )

                        # Row 4: Skip Rows (numeric input with validation)
                        with ui.row().classes("w-full items-center gap-4 mb-3"):
                            ui.label("Skip rows:").classes("text-sm font-bold").style(
                                "min-width: 150px"
                            )
                            skip_rows_input = ui.number(
                                label="",
                                value=import_session.skip_rows,
                                min=0,
                                max=100,
                                step=1,
                                precision=0,
                                validation={
                                    "Must be a non-negative integer": lambda v: v >= 0,
                                    "Cannot skip more than 100 rows": lambda v: v
                                    <= 100,
                                },
                            ).classes("w-32")

                        # Retry Import Button
                        async def retry_import():
                            """Retry import with updated configuration from UI controls."""
                            nonlocal import_session, import_preview, columns_container, data_preview_container

                            # Get current control values
                            new_separator = separator_toggle.value
                            new_quote_char = quote_toggle.value
                            new_has_header = header_toggle.value
                            new_skip_rows = int(skip_rows_input.value)

                            # Validate skip_rows
                            if new_skip_rows < 0 or new_skip_rows > 100:
                                ui.notify("Invalid skip rows value", type="negative")
                                return

                            # Create new import session with updated config
                            import_session = CsvImportSession(
                                input_file=selected_file_path,
                                separator=new_separator,
                                quote_char=new_quote_char,
                                has_header=new_has_header,
                                skip_rows=new_skip_rows,
                            )

                            try:
                                # Reload preview with new settings
                                ui.notify("Reloading preview...", type="info")
                                import_preview = import_session.load_preview(10)

                                # Clear and rebuild Sections 2 & 3
                                columns_container.clear()
                                data_preview_container.clear()

                                # Rebuild Section 2: Columns
                                with columns_container:
                                    ui.label(
                                        f"Detected Columns ({len(import_preview.columns)} total)"
                                    ).classes("text-h6 mb-3")

                                    columns = import_preview.columns
                                    with ui.grid(columns=3).classes("w-full gap-2"):
                                        for i, col in enumerate(columns, 1):
                                            ui.label(f"{i}. {col}").classes("text-sm")

                                # Rebuild Section 3: Data Preview
                                with data_preview_container:
                                    ui.label("Data Sample (first 10 rows)").classes(
                                        "text-h6 mb-3"
                                    )

                                    # Convert DataFrame for aggrid
                                    preview_dict = import_preview.to_dict(
                                        as_series=False
                                    )
                                    column_defs = [
                                        {"field": col, "sortable": True, "filter": True}
                                        for col in import_preview.columns
                                    ]
                                    row_data = [
                                        {
                                            col: preview_dict[col][i]
                                            for col in import_preview.columns
                                        }
                                        for i in range(len(import_preview))
                                    ]

                                    ui.aggrid(
                                        {"columnDefs": column_defs, "rowData": row_data}
                                    ).classes("w-full h-96")

                                ui.notify(
                                    "Preview updated successfully!", type="positive"
                                )

                            except Exception as e:
                                ui.notify(f"Error: {str(e)}", type="negative")
                                print(f"Retry import error:\n{format_exc()}")

                        with ui.row().classes("w-full justify-end mt-4"):
                            ui.button(
                                "Retry Import",
                                icon="refresh",
                                on_click=retry_import,
                                color="secondary",
                            ).props("outline")

                    elif isinstance(import_session, ExcelImportSession):
                        ui.label(
                            f"• Sheet name: {import_session.selected_sheet}"
                        ).classes("text-sm")

                # Section 2: Detected Columns (with container for dynamic updates)
                with ui.card().classes("w-full"):
                    columns_container = ui.column().classes("w-full")
                    with columns_container:
                        ui.label(
                            f"Detected Columns ({len(import_preview.columns)} total)"
                        ).classes("text-h6 mb-3")

                        # Display as numbered list in columns for better space usage
                        columns = import_preview.columns
                        with ui.grid(columns=3).classes("w-full gap-2"):
                            for i, col in enumerate(columns, 1):
                                ui.label(f"{i}. {col}").classes("text-sm")

                # Section 3: Data Preview (with container for dynamic updates)
                with ui.card().classes("w-full"):
                    data_preview_container = ui.column().classes("w-full")
                    with data_preview_container:
                        ui.label("Data Sample (first 10 rows)").classes("text-h6 mb-3")

                        # Convert polars DataFrame to dict for aggrid
                        preview_dict = import_preview.to_dict(as_series=False)

                        # Create column definitions
                        column_defs = [
                            {"field": col, "sortable": True, "filter": True}
                            for col in import_preview.columns
                        ]

                        # Create row data
                        row_data = [
                            {
                                col: preview_dict[col][i]
                                for col in import_preview.columns
                            }
                            for i in range(len(import_preview))
                        ]

                        ui.aggrid(
                            {"columnDefs": column_defs, "rowData": row_data}
                        ).classes("w-full h-96")

                # Bottom Actions
                with ui.row().classes("w-full justify-end gap-2 mt-4"):
                    ui.button(
                        "Change Import Options",
                        icon="settings",
                        on_click=lambda: ui.notify(
                            "Coming soon: Change import options", type="info"
                        ),
                    ).props("outline")

                    ui.button(
                        "Import Dataset",
                        icon="upload",
                        color="primary",
                        on_click=lambda: ui.notify(
                            "Coming soon: Import dataset", type="info"
                        ),
                    )

        except Exception as e:
            ui.notify(f"Error loading preview: {str(e)}", type="negative")
            print(f"Preview error:\n{format_exc()}")
            ui.navigate.to("/dataset_importing")
            return

    # Launch in native mode
    ui.run(
        native=True,
        window_size=(800, 600),
        title="CIB Mango Tree",
        favicon="🥭",
        reload=False,
    )
