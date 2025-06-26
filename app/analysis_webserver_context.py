from os import path
from pathlib import Path
from tempfile import TemporaryDirectory
from dash import Dash
from flask import Flask, render_template
from pydantic import BaseModel
from shiny import App
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import RedirectResponse
from uvicorn import Config, Server
from a2wsgi import WSGIMiddleware
from analyzers.hashtags_web.app import set_df_global_state, app_layout, server
from context import WebPresenterContext
from .analysis_context import AnalysisContext
from .app_context import AppContext

class AnalysisWebServerContext(BaseModel):
    app_context: AppContext
    analysis_context: AnalysisContext

    def start(self):
        containing_dir = str(Path(__file__).resolve().parent)
        static_folder = path.join(containing_dir, "web_static")
        template_folder = path.join(containing_dir, "web_templates")
        web_presenters = self.analysis_context.web_presenters
        project_name = self.analysis_context.project_context.display_name
        analyzer_name = self.analysis_context.display_name

        async def relay(_):
            return RedirectResponse("/shiny" if web_presenters[0].shiny else "/dash")

        web_server = Flask(
            __name__,
            template_folder=template_folder,
            static_folder=static_folder,
            static_url_path="/static"
        )
        wsgi_middleware = WSGIMiddleware(web_server)
        shiny_app = App(ui=app_layout, server=server, debug=True)
        app = Starlette(debug=True, routes=[
            Route("/", relay),
            Mount("/dash", app=wsgi_middleware, name="dash_app"),
            Mount("/shiny", app=shiny_app, name="shiny_app")
        ])

        @web_server.route("/")
        def index():
            return render_template(
                "index.html",
                panels=[(presenter.id, presenter.name) for presenter in web_presenters],
                project_name=project_name,
                analyzer_name=analyzer_name,
            )

        web_server.logger.disabled = True
        temp_dirs: list[TemporaryDirectory] = []

        for presenter in web_presenters:
            dash_app = Dash(
                presenter.server_name,
                server=web_server,
                requests_pathname_prefix=f"/dash/{presenter.id}/",
                routes_pathname_prefix=f"/{presenter.id}/",
                external_stylesheets=["/dash/static/dashboard_base.css"],
            )
            temp_dir = TemporaryDirectory()
            presenter_context = WebPresenterContext(
                analysis=self.analysis_context.model,
                web_presenter=presenter,
                store=self.app_context.storage,
                temp_dir=temp_dir.name,
                dash_app=dash_app,
                shiny_app=shiny_app
            )
            temp_dirs.append(temp_dir)
            result = presenter.factory(presenter_context)

            if presenter.id == "hashtags_dashboard":
                set_df_global_state(df_input=result["raw_dataframe"], df_output=result["hashtags_dataframe"])

        try:
            config = Config(app, host="0.0.0.0", port=8050, log_level="error")
            uvi_server = Server(config)

            uvi_server.run()

        except Exception as err:
            print(err)

        for temp_dir in temp_dirs:
            temp_dir.cleanup()
