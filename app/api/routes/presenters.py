from io import BytesIO, StringIO
from typing import Any, Union
from datetime import datetime
from json import dumps
from csv import DictWriter
from xlsxwriter import Workbook
from flask import jsonify, request, send_file
from flask.views import MethodView
from pydantic import ValidationError

from analyzer_interface.context import WebPresenterContext

from ..validators.presenters import (
    PresenterQueryParamsValidator,
    PresenterQueryDownloadValidator,
    FileDownloadChoiceEnum
)

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
            output_data = presenter.get(output_key, None)

            if output_data is None:
                return jsonify({"code": 404, "error": "Presenter not found"}), 404

            if id == output_data["id"]:
                output = output_data

        return (jsonify({"code": 200, "data": output}), 200) if not output is None else \
            (jsonify({"code": 404, "error": "Presenter not found"}), 404)

class PresenterDownloadView(MethodView):
        def __init__(
            self,
            presenters: list[dict[str, Any]],
            presenters_context: list[WebPresenterContext],
        ):
            self.presenters = presenters
            self.presenters_context = presenters_context

        def get(self, id: str, file_type: str):
            output_name = request.args.get("output", None)
            filter_key = request.args.get("filter_field", None)
            filter_value = request.args.get("filter_value", None)

            try:
                PresenterQueryDownloadValidator(
                    file_type=file_type,
                    output=output_name,
                    filter_key=filter_key,
                    filter_value=filter_value,
                )

            except ValidationError as e:
                return str(e), 422

            output = None
            output_key = ""
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
                presenter_key = (
                    output_name if not output_name is None else presenter["default_output"]
                )
                presenter_data = presenter.get(presenter_key, None)

                if presenter_data is None:
                    continue

                if id == presenter_data["id"]:
                    output = presenter_data
                    output_key = presenter_key
                    break

            if output is None:
                return "Presenter not found", 404

            analyzer_output = None

            for analyzer_dependecy in output["depends_on"]:
                if analyzer_dependecy["id"] != output_key:
                    continue

                for analyzer_out in analyzer_dependecy["outputs"]:
                    if analyzer_out["id"] == output_key:
                        analyzer_output = analyzer_out
                        break

            if analyzer_output is None:
                return "analyzer output could not be found", 404

            buffer = BytesIO()
            file_format = ""
            mime_type = ""
            columns = [
                column for column in analyzer_output["columns"] if not column["api_field"] is None
            ]
            data_length = 0

            if len(columns) > 0:
                column = columns[0]
                data_length = len(output[column["api_field"]][column["dict_field"]]) \
                    if type(output[column["api_field"]]) is dict \
                    else len(output[column["api_field"]])

            file_payload = [{}] * data_length

            for index in range(0, data_length):
                item = {}

                for column in columns:
                    item_key = column["api_name"] if not column.get("api_name", None) is None else column["api_field"]
                    item_value = None

                    if column["data_type"] == "text" or column["data_type"] == "datetime":
                        column_data = output[column["api_field"]]
                        item_value = column_data[column["dict_field"]][index] if type(column_data) is dict else column_data[index]

                    if column["data_type"] == "integer":
                        column_data = output[column["api_field"]]
                        item_value = int(
                            column_data[column["dict_field"]][index] if type(column_data) is dict else column_data[index]
                        )

                    item[item_key] = item_value

                file_payload[index] = item

            if file_type.lower() == FileDownloadChoiceEnum.JSON.value:
                file_format = "json"
                mime_type = "application/json"

                buffer.write(dumps(file_payload).encode("utf-8"))

            if file_type.lower() == FileDownloadChoiceEnum.CSV.value:
                file_format = "csv"
                mime_type = "text/csv"
                string_buffer = StringIO()
                writer = DictWriter(string_buffer, fieldnames=[
                    column["api_name"] if not column.get("api_name", None) is None else column["api_field"] for column
                    in columns
                ])

                writer.writeheader()
                writer.writerows(file_payload)
                buffer.write(string_buffer.getvalue().encode("utf-8"))

            if file_type.lower() == FileDownloadChoiceEnum.Excel.value:
                row_index = 1
                file_format = "xlsx"
                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                workbook = Workbook(buffer)
                worksheet = workbook.add_worksheet(output["id"])
                column_names = [
                    column["api_name"] if not column.get("api_name", None) is None else column["api_field"] for column
                    in columns
                ]

                worksheet.write_row("A1", column_names)

                for index in range(0, data_length):
                    row = [file_payload[index][column_name] for column_name in column_names]

                    worksheet.write_row(row_index, 0, row)
                    row_index += 1

                worksheet.autofit()
                workbook.close()

            buffer.seek(0)

            return send_file(
                buffer,
                mime_type,
                True,
                f"{output["id"]}_{datetime.now().strftime("%Y%m%d%H%M%S")}.{file_format}"
            ), 200
