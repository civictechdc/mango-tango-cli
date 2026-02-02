from os.path import abspath
from nicegui import ui


class UploadButton(ui.element, component=abspath("../dist/UploadButton.js")):
    def __init__(self, text: str) -> None:
        super().__init__()

        self._props["text"] = text
