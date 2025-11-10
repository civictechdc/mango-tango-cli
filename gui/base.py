"""
Base abstractions for GUI pages using Pydantic and ABC.

This module provides:
- GuiColors: Brand color constants
- GuiSession: Type-safe state container replacing module-level globals
- GuiPage: Abstract base class for all GUI pages
"""

import abc
from pathlib import Path
from typing import Optional

from nicegui import ui
from pydantic import BaseModel, ConfigDict, Field

from gui.context import GUIContext
from importing import ImporterSession
from storage import AnalysisModel, ProjectModel


class GuiColors(BaseModel):
    """Mango Tree brand colors"""

    model_config = ConfigDict(frozen=True)

    primary: str = Field(default="#609949", description="Mango dark green")
    secondary: str = Field(default="#f9bc30", description="Mango orange light")
    accent: str = Field(default="white", description="Accent color")

    # Additional colors for reference
    mango_orange: str = Field(default="#f3921e", description="Mango orange")


# Class for Managing Constants (colors and links)
class GuiURLS(BaseModel):
    """UI URL constants."""

    model_config = ConfigDict(frozen=True)

    # External URLs
    github_url: str = Field(
        default="https://github.com/civictechdc/mango-tango-cli",
        description="GitHub repository URL",
    )
    instagram_url: str = Field(
        default="https://www.instagram.com/civictechdc/",
        description="Instagram profile URL",
    )


class GuiConstants(BaseModel):
    """Container for both colors and urls"""

    model_config = ConfigDict(frozen=True)

    colors = GuiColors()
    urls = GuiURLS()


# Singleton instance for easy access
GUI_COLORS = GuiColors()
GUI_URLS = GuiURLS()
GUI_CONSTANTS = GuiConstants()


# Class for handling information that
# must persist throught a session
class GuiSession(BaseModel):
    """
    Application-wide session state container.

    Replaces module-level global variables with a type-safe,
    validated state container. Provides access to
    application context and workflow state.

    Attributes:
        context: Application context wrapping App instance
        current_project: Currently selected/active project
        selected_file_path: Path to file selected for import
        new_project_name: Name for project being created
        import_session: Active importer session for data preview
        selected_analyzer: ID of selected primary analyzer
        current_analysis: Currently selected/active analysis

    Example:
        ```python
        context = GUIContext(app=app)
        session = GuiSession(context=context)

        # Set project
        session.current_project = project

        # Access app
        projects = session.app.list_projects()
        ```
    """

    # Core context
    context: GUIContext

    # Workflow state - project creation
    current_project: Optional[ProjectModel] = None
    selected_file_path: Optional[Path] = None
    new_project_name: Optional[str] = None
    import_session: Optional[ImporterSession] = None

    # Workflow state - analysis
    selected_analyzer: Optional[str] = None
    current_analysis: Optional[AnalysisModel] = None

    # Allow arbitrary types (for NiceGUI components, ImporterSession, etc.)
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def app(self):
        """Access underlying App instance."""
        return self.context.app

    def reset_project_workflow(self) -> None:
        """Clear project creation workflow state."""
        self.new_project_name = None
        self.selected_file_path = None
        self.import_session = None

    def reset_analysis_workflow(self) -> None:
        """Clear analysis workflow state."""
        self.selected_analyzer = None
        self.current_analysis = None

    def validate_project_selected(self) -> bool:
        """Check if a project is currently selected."""
        return self.current_project is not None

    def validate_file_selected(self) -> bool:
        """Check if a file is currently selected."""
        return self.selected_file_path is not None

    def validate_project_name_set(self) -> bool:
        """Check if new project name is set."""
        return bool(self.new_project_name and self.new_project_name.strip())


class GuiPage(BaseModel, abc.ABC):
    """
    Abstract base class for all GUI pages.

    Provides common page structure and lifecycle using the Template Method
    pattern. Subclasses implement `render_content()` for page-specific UI
    while inheriting consistent header/footer rendering.

    Attributes:
        session: Session state container with app context
        route: URL route for this page (e.g., "/", "/projects")
        title: Page title shown in header
        show_back_button: Whether to show back navigation button
        back_route: Route to navigate when back button clicked
        back_icon: Icon for back button (default: "arrow_back")
        back_text: Optional text label for back button
        show_footer: Whether to render footer

    Usage:
        ```python
        class MyPage(GuiPage):
            def __init__(self, session: GuiSession):
                super().__init__(
                    session=session,
                    route="/my_page",
                    title="My Page",
                    show_back_button=True,
                    back_route="/",
                )

            def render_content(self) -> None:
                with ui.column().classes("items-center"):
                    ui.label("My page content")

        # Register with NiceGUI
        @ui.page("/my_page")
        def my_page():
            page = MyPage(session)
            page.render()
        ```
    """

    # Link to main session state/variables
    session: GuiSession

    # Page configuration
    route: str = "/"
    title: str = "CIB Mango Tree"

    # Navigation configuration
    show_back_button: bool = False
    back_route: Optional[str] = None
    back_icon: str = "arrow_back"
    back_text: Optional[str] = None

    # Footer configuration
    show_footer: bool = True

    # Allow arbitrary types
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # main rendering function
    def render(self) -> None:
        """
        Main rendering method implementing template pattern.

        Call this method from the NiceGUI @ui.page decorator to render
        the complete page with header, content, and footer.

        Lifecycle:
        1. Setup colors
        2. Render header
        3. Render content (abstract - implemented by subclasses)
        4. Render footer
        """
        self._setup_colors()
        self._render_header()
        self.render_content()
        if self.show_footer:
            self._render_footer()

    @abc.abstractmethod
    def render_content(self) -> None:
        """
        Render page-specific content.

        Subclasses MUST implement this method to provide the main
        page content. This is called automatically by render().

        Example:
            ```python
            def render_content(self) -> None:
                with ui.column().classes("items-center"):
                    ui.label("Welcome")
                    ui.button("Click me", on_click=self._handle_click)
            ```
        """
        raise NotImplementedError

    def _setup_colors(self) -> None:
        """Setup Mango Tree brand colors for NiceGUI."""
        ui.colors(
            primary=GUI_COLORS.primary,
            secondary=GUI_COLORS.secondary,
            accent=GUI_COLORS.accent,
        )

    def _render_header(self) -> None:
        """
        Render standardized header with 3-column layout.

        Layout:
        - Left: Back button (if show_back_button=True)
        - Center: Page title
        - Right: Home button (if not on home page)
        """
        with ui.header(elevated=True):
            with ui.row().classes("w-full items-center").style(
                "justify-content: space-between"
            ):
                # Left: Back button or spacer
                with ui.element("div").classes("flex items-center"):
                    if self.show_back_button and self.back_route:
                        ui.button(
                            text=self.back_text,
                            icon=self.back_icon,
                            color="accent",
                            on_click=lambda: self.navigate_to(self.back_route),
                        ).props("flat")

                # Center: Title
                ui.label(self.title).classes("text-h6")

                # Right: Home button (if not on home page)
                with ui.element("div").classes("flex items-center"):
                    if self.show_back_button:  # Not on home if back button shown
                        ui.button(
                            icon="home",
                            color="accent",
                            on_click=lambda: self.navigate_to("/"),
                        ).props("flat")

    def _render_footer(self) -> None:
        """
        Render standardized footer with 3-column layout.

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
                self._render_footer_links()

    def _render_footer_links(self) -> None:
        """Render social media links in footer."""
        with ui.element("div").classes("flex items-center gap-2"):
            # GitHub button
            github_btn = ui.button(
                color="accent",
                on_click=lambda: self.navigate_to_external(GUI_URLS.github_url),
            ).props("flat round")
            with github_btn:
                github_svg = self._load_svg_icon("github")
                ui.html(github_svg).style(
                    "width: 20px; height: 20px; fill: currentColor"
                )
                ui.tooltip("Visit our GitHub")

            # Instagram button
            instagram_btn = ui.button(
                color="accent",
                on_click=lambda: self.navigate_to_external(GUI_URLS.instagram_url),
            ).props("flat round")
            with instagram_btn:
                instagram_svg = self._load_svg_icon("instagram")
                ui.html(instagram_svg).style(
                    "width: 20px; height: 20px; fill: currentColor"
                )
                ui.tooltip("Follow us on Instagram")

    # Navigation helpers
    def navigate_to(self, route: str) -> None:
        """
        Navigate to another page in the application.

        Args:
            route: Target route path (e.g., "/projects", "/new_project")
        """
        ui.navigate.to(route)

    def navigate_to_external(self, url: str) -> None:
        """
        Navigate to external URL in new tab.

        Args:
            url: External URL to open
        """
        ui.navigate.to(url, new_tab=True)

    def go_back(self) -> None:
        """Navigate to the configured back route."""
        if self.back_route:
            self.navigate_to(self.back_route)

    def go_home(self) -> None:
        """Navigate to home page."""
        self.navigate_to("/")

    # utilities
    def _load_svg_icon(self, icon_name: str) -> str:
        """
        Load SVG icon from the icons directory.

        Args:
            icon_name: Name of icon file (without .svg extension)

        Returns:
            SVG content as string
        """
        icon_path = Path(__file__).parent / "icons" / f"{icon_name}.svg"
        return icon_path.read_text()

    def notify_success(self, message: str) -> None:
        """Show success notification."""
        ui.notify(message, type="positive", color="secondary")

    def notify_warning(self, message: str) -> None:
        """Show warning notification."""
        ui.notify(message, type="warning")

    def notify_error(self, message: str) -> None:
        """Show error notification."""
        ui.notify(message, type="negative")


# standalone uitility functions
def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: File size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB", "3.2 GB")

    Example:
        >>> format_file_size(1536)
        '1.5 KB'
        >>> format_file_size(1048576)
        '1.0 MB'
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def present_separator(value: str) -> str:
    """
    Format separator/quote character for display.

    Args:
        value: Separator character

    Returns:
        Human-readable representation

    Example:
        >>> present_separator("\\t")
        'Tab'
        >>> present_separator(",")
        ', (Comma)'
    """
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
