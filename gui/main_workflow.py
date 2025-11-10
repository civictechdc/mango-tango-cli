"""
Main GUI screen with title and project selection.
"""

import os
from datetime import datetime
from pathlib import Path
from traceback import format_exc

from nicegui import ui

from app import App
from components.select_analysis import analysis_label
from gui.base import GuiSession
from gui.components import ToggleButtonGroup
from gui.context import GUIContext
from gui.file_picker import LocalFilePicker
from gui.import_options import ImportOptionsDialog
from gui.pages import SelectProjectPage, StartPage
from importing import importers

# Mango Tree brand color
MANGO_DARK_GREEN = "#609949"
MANGO_ORANGE = "#f3921e"
MANGO_ORANGE_LIGHT = "#f9bc30"
ACCENT = "white"

# URLS
GITHUB_URL = "https://github.com/civictechdc/mango-tango-cli"
INSTAGRAM_URL = "https://www.instagram.com/civictechdc/"

# Module-level state for native mode (single user)
_selected_file_path = None
project = None


def _load_svg_icon(icon_name: str) -> str:
    """Load SVG icon from the icons directory."""
    icon_path = Path(__file__).parent / "icons" / f"{icon_name}.svg"
    return icon_path.read_text()


def _set_colors():
    return ui.colors(
        primary=MANGO_DARK_GREEN, secondary=MANGO_ORANGE_LIGHT, accent=ACCENT
    )


def _make_header(
    title: str,
    *,
    back_url: str | None = None,
    back_icon: str = "arrow_back",
    back_text: str | None = None,
) -> None:
    """
    Create a standardized header for GUI pages.

    The header uses a 3-column layout:
    - Left: Back button (if back_url provided)
    - Center: Page title
    - Right: Home button (if not on home page)

    Args:
        title: Page title displayed in center
        back_url: URL to navigate when back button clicked (if None, no back button)
        back_icon: Icon for back button (default: "arrow_back")
        back_text: Optional text label for back button
    """
    with ui.header(elevated=True):
        with ui.row().classes("w-full items-center").style(
            "justify-content: space-between"
        ):
            # Left: Back button (or spacer if none)
            with ui.element("div").classes("flex items-center"):
                if back_url is not None:
                    ui.button(
                        text=back_text,
                        icon=back_icon,
                        color="accent",
                        on_click=lambda: ui.navigate.to(back_url),
                    ).props("flat")

            # Center: Title
            ui.label(title).classes("text-h6")

            # Right: Home button (or spacer if on home page)
            with ui.element("div").classes("flex items-center"):
                # Only show home button if not already on home page
                if back_url is not None:  # If there's a back button, we're not on home
                    ui.button(
                        icon="home",
                        color="accent",
                        on_click=lambda: ui.navigate.to("/"),
                    ).props("flat")


def _make_footer():
    """
    Create a standardized footer for GUI pages.

    Layout:
    - Left: License information
    - Center: Project attribution
    - Right: External links (GitHub, Instagram)
    """
    with ui.footer(elevated=True):
        with ui.row().classes("w-full items-center").style(
            "justify-content: space-between"
        ):
            # Left: License
            with ui.element("div").classes("flex items-center"):
                ui.label("MIT License").classes("text-sm text-bold")

            # Center: Project attribution
            ui.label("A Civic Tech DC Project").classes("text-sm text-bold")

            # Right: External links
            with ui.element("div").classes("flex items-center gap-2"):
                # GitHub button
                github_btn = ui.button(
                    color="accent",
                    on_click=lambda: ui.navigate.to(GITHUB_URL, new_tab=True),
                ).props("flat round")
                with github_btn:
                    # Load and display GitHub SVG icon
                    github_svg = _load_svg_icon("github")
                    ui.html(github_svg).style(
                        "width: 20px; height: 20px; fill: currentColor"
                    )
                    ui.tooltip("Visit our GitHub")

                # Instagram button
                instagram_btn = ui.button(
                    color="accent",
                    on_click=lambda: ui.navigate.to(INSTAGRAM_URL, new_tab=True),
                ).props("flat round")
                with instagram_btn:
                    # Load and display Instagram SVG icon
                    instagram_svg = _load_svg_icon("instagram")
                    ui.html(instagram_svg).style(
                        "width: 20px; height: 20px; fill: currentColor"
                    )
                    ui.tooltip("Follow us on Instagram")


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


# maing GUI entry point
def gui_main(app: App):
    """
    Launch the NiceGUI interface with a minimal single screen.

    Args:
        app: The initialized App instance with storage and suite
    """

    # Initialize GUI session for state management
    gui_context = GUIContext(app=app)
    gui_session = GuiSession(context=gui_context)

    new_project_name = None

    @ui.page("/")
    def start_page():
        """Main/home page using GuiPage abstraction."""
        page = StartPage(session=gui_session)
        page.render()

    @ui.page("/select_project")
    def select_project_page():
        """Sub-page showing list of existing projects using GuiPage abstraction."""
        page = SelectProjectPage(session=gui_session)
        page.render()

    @ui.page("/new_project")
    def new_project():

        # Register custom colors FIRST, before any UI elements
        _set_colors()

        # Header
        _make_header(title="New Project", back_icon="arrow_back", back_url="/")
        _make_footer()

        nonlocal new_project_name

        # Main content - centered vertically and horizontally
        with ui.column().classes("items-center justify-center gap-6").style(
            "width: 100%; max-width: 600px; margin: 0 auto; height: 80vh;"
        ):
            new_project_name_input = ui.input(
                label="New Project Name",
                placeholder="e.g. Twitter-2018-dataset",
            )

            def on_next():
                nonlocal new_project_name
                # Capture the input value when user clicks Next
                new_project_name = new_project_name_input.value

                if not new_project_name or not new_project_name.strip():
                    ui.notify("Please enter a project name", type="warning")
                    return

                ui.navigate.to("/dataset_importing")

            ui.button(
                text="Next: Select Dataset",
                icon="arrow_forward",
                on_click=on_next,
                color="primary",
            )

    @ui.page("/dataset_importing")
    def dataset_importing():

        _set_colors()

        _make_header(
            title="Import Dataset", back_icon="arrow_back", back_url="/new_project"
        )
        _make_footer()

        # Page state
        selected_file_path = None

        # Main content - centered vertically and horizontally
        with ui.column().classes("items-center justify-center gap-6").style(
            "width: 100%; max-width: 800px; margin: 0 auto; height: 80vh;"
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

    @ui.page("/data_preview")
    def data_preview_page():
        global _selected_file_path

        _set_colors()

        _make_header(
            title="Data Preview", back_icon="arrow_back", back_url="/dataset_importing"
        )
        _make_footer()

        def _make_preview_grid(data_frame):
            """Wraps elements of the preview data grid and labels"""
            ui.label("Data Preview (first 5 rows)").classes("text-lg")

            n_empty = sum((c[0] == 0 for c in data_frame.count().iter_columns()))
            ui.label(
                f"Nr. detected columns: {len(data_frame.columns)} ({n_empty} empty)"
            ).classes("text-sm")

            ui.aggrid.from_polars(
                data_frame, theme="quartz", auto_size_columns=False
            ).classes("w-full h-64")

        # Retrieve file path from module-level variable
        selected_file_path = _selected_file_path

        if not selected_file_path:
            ui.notify("No file selected. Redirecting...", type="warning")
            ui.navigate.to("/dataset_importing")
            return

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

            N_ROWS_FOR_PREVIEW = 5
            import_preview = import_session.load_preview(n_records=N_ROWS_FOR_PREVIEW)

            # Declare containers for dynamic updates
            data_preview_container = None

            # Retry callback for dialog
            async def handle_retry(updated_session):
                """Handle retry from import options dialog."""
                nonlocal import_session, import_preview

                try:

                    # Update session
                    import_session = updated_session

                    # Reload preview with new settings
                    import_preview = import_session.load_preview(
                        n_records=N_ROWS_FOR_PREVIEW
                    )

                    # Clear and rebuild data preview
                    data_preview_container.clear()
                    with data_preview_container:
                        _make_preview_grid(data_frame=import_preview)

                    ui.notify(
                        "Preview updated successfully!",
                        color="secondary",
                        type="positive",
                    )

                except Exception as e:
                    ui.notify(f"Error: {str(e)}", type="negative")
                    print(f"Retry import error:\n{format_exc()}")

            # Open import options dialog
            async def open_import_options():
                dialog = ImportOptionsDialog(
                    import_session=import_session,
                    selected_file_path=selected_file_path,
                    on_retry=handle_retry,
                )
                await dialog

            async def _import_data_create_project():
                nonlocal new_project_name
                global project

                try:
                    # Call synchronous create_project
                    project = app.create_project(
                        name=new_project_name, importer_session=import_session
                    )

                    # Navigate FIRST
                    ui.navigate.to("/select_analyzer")

                except Exception as e:
                    ui.notify(f"Error creating project: {str(e)}", type="negative")
                    print(f"Project creation error:\n{format_exc()}")

            # Main content area - centered
            with ui.column().classes("items-center justify-center gap-6").style(
                "width: 100%; max-width: 1200px; margin: 0 auto; padding: 2rem; min-height: 70vh;"
            ):

                # Data Preview (with container for dynamic updates)
                # with ui.card().classes("w-full"):
                data_preview_container = ui.column().classes("w-full")
                with data_preview_container:

                    _make_preview_grid(import_preview)

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
                        on_click=_import_data_create_project,
                    )

        except Exception as e:
            ui.notify(f"Error loading preview: {str(e)}", type="negative")
            print(f"Preview error:\n{format_exc()}")
            ui.navigate.to("/dataset_importing")
            return

    # choose analysis page
    @ui.page("/select_analyzer")
    def select_analyzer():

        nonlocal new_project_name

        _set_colors()
        _make_header(
            title="Select Analysis", back_icon="arrow_back", back_url="/select_project"
        )
        _make_footer()

        # Then notify (will show on new page)
        ui.notify(
            f"Created project: {new_project_name}!",
            type="positive",
            color="secondary",
        )

        # Main content - centered
        with ui.column().classes("items-center justify-center gap-6").style(
            "width: 100%; max-width: 800px; margin: 0 auto; height: 80vh;"
        ):
            ui.label("Choose an analysis type").classes("text-lg")

            # Get primary analyzers from suite
            analyzers = app.context.suite.primary_anlyzers

            if not analyzers:
                ui.label("No analyzers available").classes("text-grey")
            else:
                # Create radio options from analyzers
                analyzer_options = {
                    analyzer.name: analyzer.short_description for analyzer in analyzers
                }

                # Create toggle button group for analyzer selection
                button_group = ToggleButtonGroup()
                with ui.row().classes("gap-4"):
                    for analyzer_name, description in analyzer_options.items():
                        button_group.add_button(analyzer_name)

                # populate a list of existing options
                now = datetime.now()
                analysis_options = sorted(
                    [
                        (
                            analysis_label(analysis, now),
                            analysis,
                        )
                        for analysis in project.list_analyses()
                    ],
                    key=lambda option: option[0],
                )

                previous_analyzer = None
                with ui.card():
                    if analysis_options:
                        previous_analyzer = ui.select(
                            label="Review previous analyses",
                            options=[e[0] for e in analysis_options],
                        )
                    else:
                        ui.label("No previous tests have been found.").classes(
                            "text-base"
                        )

                def on_proceed():
                    # Get current selections
                    new_selection = button_group.get_selected_text()
                    prev_selection = (
                        previous_analyzer.value if previous_analyzer else None
                    )

                    # Validation: both selected
                    if new_selection and prev_selection:
                        ui.notify(
                            "Please choose either a new analyzer OR a previous analysis, not both",
                            type="warning",
                        )
                        return

                    # Validation: none selected
                    if not new_selection and not prev_selection:
                        ui.notify("Please select an analyzer", type="warning")
                        return

                    # Valid selection - proceed
                    if new_selection:
                        ui.notify(f"New analyzer: {new_selection}", type="positive")
                        # TODO: Navigate to /configure_analysis with new analyzer
                        # ui.navigate.to("/configure_analysis")
                    else:
                        ui.notify(
                            f"Previous analysis: {prev_selection}", type="positive"
                        )
                        # TODO: Navigate to /view_analysis with previous results
                        # ui.navigate.to("/view_analysis")

                ui.button(
                    "Proceed",
                    icon="arrow_forward",
                    color="primary",
                    on_click=on_proceed,
                )

    # Launch in native mode
    ui.run(
        native=True,
        window_size=(800, 600),
        title="CIB Mango Tree",
        favicon="🥭",
        reload=False,
    )
