from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from cibmangotree.tui.tools.inception import TerminalContext

if TYPE_CHECKING:
    from cibmangotree.app import App


class ViewContext(BaseModel):
    terminal: TerminalContext
    app: "App"
    model_config = ConfigDict(arbitrary_types_allowed=True)
