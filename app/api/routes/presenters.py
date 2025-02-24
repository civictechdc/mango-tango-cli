from flask import jsonify
from flask.views import MethodView
from analyzer_interface.context import WebPresenterContext

class PresentersView(MethodView):
    def __init__(self, presenters: list):
        self.presenters = presenters

    def get(self):
        return jsonify({"code": 200, "data": self.presenters}), 200