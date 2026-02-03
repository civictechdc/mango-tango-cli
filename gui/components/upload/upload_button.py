from nicegui import ui
from gui.component_path import create_vue_dist_path


class UploadButton(
    ui.element, component=create_vue_dist_path(__file__, "../dist/UploadButton.js")
):
    def __init__(
        self, text: str | None = None, color: str = "primary", icon: str | None = None
    ) -> None:
        super().__init__()

        self._props["text"] = text
        self._props["color"] = color
        self._props["icon"] = icon
