from json import load
from os import getenv, path
from pathlib import Path

from flask import Blueprint
from flask_cors import CORS
from pydantic import BaseModel

from app.app_context import AppContext


class ViteContext(BaseModel):
    app_context: AppContext
    vite_origin: str
    is_production: bool
    project_path: Path

    def __init__(self, app_context: AppContext) -> None:
        super().__init__(
            app_context=app_context,
            vite_origin=getenv("VITE_ORIGIN", "http://localhost:5173"),
            is_production=getenv("FLASK_DEBUG", "0") != "1",
            project_path=Path(path.dirname(path.abspath(__file__)))
            .resolve()
            .parent.parent,
        )

    def create_blueprint(self) -> Blueprint:
        blueprint = Blueprint(
            "vite_assets_blueprint",
            __name__,
            static_folder=self.project_path / "app/web_templates/build/bundled",
            static_url_path="/static/bundled",
        )
        manifest = {}

        if self.is_production:
            manifest_path = self.project_path / "app/web_templates/build/manifest.json"

            try:
                with open(manifest_path, "r") as content:
                    manifest = load(content)

            except OSError as exception:
                raise OSError(
                    "Manifest file not found. Run `npm run build`."
                ) from exception

        CORS(
            blueprint,
            resources={
                r"/*": {
                    "origins": "*",
                    "allow_headers": ["Content-Type", "Authorization"],
                    "supports_credentials": True,
                }
            },
        )

        @blueprint.app_context_processor
        def add_context():
            def dev_asset(file_path):
                return f"{self.vite_origin}/static/{file_path}"

            def prod_asset(file_path):
                try:
                    return f"/static/{manifest[file_path]['file']}"

                except KeyError:
                    return "asset-not-found"

            return {
                "asset": prod_asset if self.is_production else dev_asset,
                "is_production": self.is_production,
                "vite_origin": self.vite_origin,
            }

        return blueprint
