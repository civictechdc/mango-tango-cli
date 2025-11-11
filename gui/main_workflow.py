"""
Main GUI screen with title and project selection.
"""

import os
from datetime import datetime
from pathlib import Path
from traceback import format_exc

from nicegui import ui

from app import App
from gui.base import GuiSession, gui_routes
from gui.context import GUIContext
from gui.import_options import ImportOptionsDialog
from gui.pages import (
    ImportDatasetPage,
    NewProjectPage,
    PreviewDatasetPage,
    SelectAnalyzerPage,
    SelectProjectPage,
    StartPage,
)
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

    @ui.page(gui_routes.root)
    def start_page():
        """Main/home page using GuiPage abstraction."""
        page = StartPage(session=gui_session)
        page.render()

    @ui.page(gui_routes.select_project)
    def select_project_page():
        """Sub-page showing list of existing projects using GuiPage abstraction."""
        page = SelectProjectPage(session=gui_session)
        page.render()

    @ui.page(gui_routes.new_project)
    def new_project():
        """Sub-page for creating a new project name before importing dataset"""
        page = NewProjectPage(session=gui_session)
        page.render()

    @ui.page(gui_routes.import_dataset)
    def dataset_importing():
        """Sub-page for importing dataset using GuiPage abstraction."""
        page = ImportDatasetPage(session=gui_session)
        page.render()

    @ui.page(gui_routes.preview_dataset)
    def preview_dataset():
        """Sub-page for rendering preview of the imported dataset"""
        page = PreviewDatasetPage(session=gui_session)
        page.render()

    # choose analysis page
    @ui.page(gui_routes.select_analyzer)
    def select_analyzer():
        """Analyzer selection page using GuiPage abstraction."""
        page = SelectAnalyzerPage(session=gui_session)
        page.render()

    # Launch in native mode
    ui.run(
        native=True,
        window_size=(800, 600),
        title="CIB Mango Tree",
        favicon="🥭",
        reload=False,
    )
