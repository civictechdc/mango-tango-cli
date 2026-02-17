"""
Main GUI workflow including all pages.
"""

from nicegui import ui

from app import App
from gui.base import GuiSession, gui_routes
from gui.context import GUIContext
from gui.pages import (
    ConfigureAnalaysisParams,
    ConfigureAnalysis,
    ImportDatasetPage,
    NewProjectPage,
    PreviewDatasetPage,
    RunAnalysisPage,
    SelectAnalyzerForkPage,
    SelectNewAnalyzerPage,
    SelectPreviousAnalyzerPage,
    SelectProjectPage,
    StartPage,
)


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

    @ui.page(gui_routes.select_analyzer_fork)
    def select_analyzer_fork():
        page = SelectAnalyzerForkPage(session=gui_session)
        page.render()

    @ui.page(gui_routes.select_analyzer)
    def select_analyzer():
        """New analyzer selection page using GuiPage abstraction."""
        page = SelectNewAnalyzerPage(session=gui_session)
        page.render()

    @ui.page(gui_routes.select_previous_analyzer)
    def select_previous_analyzer():
        """Previous analyzer selection page using GuiPage abstraction."""
        page = SelectPreviousAnalyzerPage(session=gui_session)
        page.render()

    @ui.page(gui_routes.configure_analysis)
    def configure_analysis():
        page = ConfigureAnalysis(session=gui_session)
        page.render()

    @ui.page(gui_routes.configure_analysis_parameters)
    def configure_analysis_parameters():
        page = ConfigureAnalaysisParams(session=gui_session)
        page.render()

    @ui.page(gui_routes.configure_analysis)
    def run_analysis():
        page = RunAnalysisPage(session=gui_session)
        page.render()

    # Launch in native mode
    ui.run(
        native=True,
        fullscreen=True,
        title="CIB Mango Tree",
        favicon="🥭",
        reload=False,
    )
