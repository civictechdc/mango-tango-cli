from collections.abc import Awaitable, Callable

from fastapi import File, UploadFile
from nicegui import app, ui

from gui.component_path import create_vue_dist_path


class UploadButton(
    ui.element, component=create_vue_dist_path(__file__, "../dist/UploadButton.js")
):
    def __init__(
        self,
        on_upload: Callable[[UploadFile], Awaitable[None]],
        text: str | None = None,
        color: str = "primary",
        icon: str | None = None,
        redirect_url: str | None = None,
    ) -> None:
        super().__init__()

        url: str = f"/_nicegui/client/{self.client.id}/upload/{self.id}"
        self._props["text"] = text
        self._props["color"] = color
        self._props["icon"] = icon
        self._props["url"] = url

        @app.post(url)
        async def upload_route(file: UploadFile = File()) -> dict[str, str]:
            await on_upload(file)

            if redirect_url is not None and len(redirect_url) > 0:
                return {"href": redirect_url}

            return {"message": "success"}
