from asyncio import CancelledError, Event, create_task
from os import path
from pathlib import Path
from signal import SIGINT, default_int_handler, signal
from tempfile import TemporaryDirectory

from a2wsgi import WSGIMiddleware
from dash import Dash
from flask import Flask, render_template
from pydantic import BaseModel
from shiny import App
from starlette.applications import Starlette
from starlette.responses import RedirectResponse
from starlette.routing import Mount, Route
from uvicorn import Config, Server

from context import WebPresenterContext

from .analysis_context import AnalysisContext
from .app_context import AppContext
from .shiny import LayoutManager, ServerHandleManager


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
        server_handler_manager = ServerHandleManager()
        layout_manager = LayoutManager()
        web_server = Flask(
            __name__,
            template_folder=template_folder,
            static_folder=static_folder,
            static_url_path="/static",
        )

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
            )
            temp_dirs.append(temp_dir)
            result = presenter.factory(presenter_context)

            if result is None or result.shiny is None:
                continue

            server_handler_manager.add(result.shiny.server_handler)
            layout_manager.add(result.shiny.panel)

        async def relay(_):
            return RedirectResponse("/shiny" if web_presenters[0].shiny else "/dash")

        shiny_app = App(
            ui=layout_manager.build_layout(),
            server=server_handler_manager.call_handlers,
            debug=False,
        )
        app = Starlette(
            debug=False,
            routes=[
                Route("/", relay),
                Mount("/dash", app=WSGIMiddleware(web_server), name="dash_app"),
                Mount("/shiny", app=shiny_app, name="shiny_app"),
            ],
        )
        config = Config(
            app, host="0.0.0.0", port=8050, log_level="error", lifespan="off"
        )
        uvi_server = Server(config)
        shutdown_event = Event()

        async def shutdown_handler():
            if shutdown_event.is_set():
                return

            shutdown_event.set()
            uvi_server.should_exit = True

        def signal_handler(sig, frame):
            create_task(shutdown_handler())

        signal(SIGINT, signal_handler)

        try:
            uvi_server.run()

        except KeyboardInterrupt:
            print("gracefully shutting down server...")

        except CancelledError:
            print("gracefully shutting down server...")

        except Exception as err:
            if not isinstance(err, (KeyboardInterrupt, CancelledError)):
                print(f"Unexpected error: {err}")

        signal(SIGINT, default_int_handler)

        for temp_dir in temp_dirs:
            temp_dir.cleanup()
