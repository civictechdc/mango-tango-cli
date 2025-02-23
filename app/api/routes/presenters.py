import polars as pl
from flask import jsonify
from flask.views import MethodView
from analyzer_interface.context import WebPresenterContext


class PresentersView(MethodView):
    def __init__(self, presenters_context: list[WebPresenterContext]):
        self.presenters_context = presenters_context

    def get(self):
        presenters = []

        for presenter_context in self.presenters_context:
            presenter_model = presenter_context.web_presenter.model_dump()
            data_frame = pl.read_parquet(presenter_context.base.table("character_count").parquet_path)
            presenter_model["data_frame_values"] = data_frame["character_count"].to_list()

            presenter_model.pop("factory")
            presenters.append(presenter_model)

        return jsonify({"code": 200, "data": presenters}), 200