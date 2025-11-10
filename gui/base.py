"""
Base abstractions for GUI pages using Pydantic and ABC.

This module provides:
- GuiColors: Brand color constants
- GuiSession: Type-safe state container replacing module-level globals
"""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from gui.context import GUIContext
from importing import ImporterSession
from storage import AnalysisModel, ProjectModel


# Class for Managing Constants (colors and links)
class GuiConstants(BaseModel):
    """Mango Tree brand colors and UI constants."""

    model_config = ConfigDict(frozen=True)

    primary: str = Field(default="#609949", description="Mango dark green")
    secondary: str = Field(default="#f9bc30", description="Mango orange light")
    accent: str = Field(default="white", description="Accent color")

    # Additional colors for reference
    mango_orange: str = Field(default="#f3921e", description="Mango orange")

    # External URLs
    github_url: str = Field(
        default="https://github.com/civictechdc/mango-tango-cli",
        description="GitHub repository URL",
    )
    instagram_url: str = Field(
        default="https://www.instagram.com/civictechdc/",
        description="Instagram profile URL",
    )


# Singleton instance for easy access
GUI_COLORS_LINKS = GuiConstants()


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
