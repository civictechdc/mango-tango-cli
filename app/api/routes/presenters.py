from typing import Any

from flask import jsonify, request
from flask.views import MethodView
from pydantic import ValidationError

from analyzer_interface.context import WebPresenterContext

from ..validators.presenters import PresenterQueryParamsValidator


class PresentersView(MethodView):
    def __init__(
        self,
        presenters: list[dict[str, Any]],
        presenters_context: list[WebPresenterContext],
    ):
        self.presenters = presenters
        self.presenters_context = presenters_context

    def get(self):
        output_name = request.args.get("output", None)
        filter_key = request.args.get("filter_field", None)
        filter_value = request.args.get("filter_value", None)

        try:
            PresenterQueryParamsValidator(
                output=output_name, filter_key=filter_key, filter_value=filter_value
            )

        except ValidationError as e:
            return jsonify({"code": 422, "error": e.json()}), 422

        output = []
        presenters = (
            [
                presenter_context.web_presenter.api_factory(
                    presenter_context, {"matcher": filter_value}
                )
                for presenter_context in self.presenters_context
            ]
            if (not filter_value is None or not output_name is None)
            else self.presenters
        )

        for presenter in presenters:
            output_key = (
                output_name if not output_name is None else presenter["default_output"]
            )

            output.append(presenter[output_key])

        return (
            jsonify({"code": 200, "count": len(output), "data": output}),
            200,
        )


class PresenterView(MethodView):
    def __init__(
        self,
        presenters: list[dict[str, Any]],
        presenters_context: list[WebPresenterContext],
    ):
        self.presenters = presenters
        self.presenters_context = presenters_context

    def get(self, id: str):
        output_name = request.args.get("output", None)
        filter_key = request.args.get("filter_field", None)
        filter_value = request.args.get("filter_value", None)

        try:
            PresenterQueryParamsValidator(
                output=output_name, filter_key=filter_key, filter_value=filter_value
            )

        except ValidationError as e:
            return jsonify({"code": 422, "error": e.json()}), 422

        output = None
        presenters = (
            [
                presenter_context.web_presenter.api_factory(
                    presenter_context, {"matcher": filter_value}
                )
                for presenter_context in self.presenters_context
            ]
            if (not filter_value is None or not output_name is None)
            else self.presenters
        )

        for presenter in presenters:
            output_key = (
                output_name if not output_name is None else presenter["default_output"]
            )

            if id == presenter[output_key]["id"]:
                output = presenter[output_key]

        if output is None:
            return jsonify({"code": 404, "error": "Presenter not found"}), 404

        return (
            jsonify({"code": 200, "data": output}),
            200,
        )
