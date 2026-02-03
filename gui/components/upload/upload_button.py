from nicegui import ui
from nicegui.events import GenericEventArguments
from gui.component_path import create_vue_dist_path
from collections.abc import Callable


class UploadButton(
    ui.element, component=create_vue_dist_path(__file__, "../dist/UploadButton.js")
):
    def __init__(
        self,
        text: str | None = None,
        color: str = "primary",
        icon: str | None = None,
        on_click: Callable[[GenericEventArguments | None], None] | None = None,
        on_change: Callable[[GenericEventArguments | None], None] | None = None,
    ) -> None:
        super().__init__()

        self._props["text"] = text
        self._props["color"] = color
        self._props["icon"] = icon

        if on_click is not None:
            self.on("click", on_click)

        if on_change is not None:
            self.on("change", on_change)
