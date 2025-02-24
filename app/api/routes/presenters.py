from flask import jsonify
from flask.views import MethodView
from analyzer_interface.context import WebPresenterContext

class PresentersView(MethodView):
    def __init__(self, presenters_context: list[WebPresenterContext]):
        self.presenters = []

        for presenter_context in presenters_context:
            self.presenters.append(presenter_context.web_presenter.api_factory(presenter_context))

    def get(self):
        return jsonify({"code": 200, "data": self.presenters}), 200