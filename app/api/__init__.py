from pydantic import BaseModel
from flask import Blueprint
from analyzer_interface.context import WebPresenterContext
from ..analysis_context import AnalysisContext
from .routes import endpoints

class APIContext(BaseModel):
    analysis_context: AnalysisContext
    presenters_context: list[WebPresenterContext]

    def create_blueprint(self) -> Blueprint:
        presenters = []
        output = Blueprint(
            "api",
            __name__,
            url_prefix="/api",
        )

        for presenter_context in self.presenters_context:
            presenters.append(presenter_context.web_presenter.api_factory(presenter_context))

        for endpoint in endpoints:
            output.add_url_rule(endpoint.path, view_func=endpoint.view.as_view(
                endpoint.name,
                presenters
            ))

        return output