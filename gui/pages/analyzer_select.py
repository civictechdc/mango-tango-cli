from gui.base import GuiPage, GuiSession, gui_routes
from gui.choice_fork import two_button_choice_fork_content


class SelectAnalyzerForkPage(GuiPage):
    """A forking page with two buttons for either advancing to start a new analysis or selecting an old one"""

    def __init__(self, session: GuiSession):
        super().__init__(
            session=session,
            route=gui_routes.select_analyzer_fork,
            title=session.current_project.display_name
            if session.current_project is not None
            else "",
            show_back_button=True,
            back_route=gui_routes.select_project,
            show_footer=True,
        )

    def render_content(self):
        two_button_choice_fork_content(
            prompt="What do you want to do next?",
            left_button_label="Start a New Test",
            left_button_icon="computer",
            left_button_on_click=lambda: self.navigate_to(gui_routes.select_analyzer),
            right_button_label="Review a Previous Test",
            right_button_on_click=lambda: self.navigate_to(
                gui_routes.select_previous_analyzer
            ),
            right_button_icon="refresh",
        )
