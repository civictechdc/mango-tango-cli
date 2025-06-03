from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, field_validator


class FileDownloadChoiceEnum(str, Enum):
    Excel = "excel"
    JSON = "json"
    CSV = "csv"


class PresenterQueryParamsValidator(BaseModel):
    output: Optional[str] = None
    filter_key: Optional[str] = None
    filter_value: Optional[Union[str, int]] = None

    @field_validator("output")
    @classmethod
    def validate_output(cls, value):
        if (not value is None) and len(value) == 0:
            raise ValueError("'output' cannot be empty")

        return value

    @field_validator("filter_key")
    @classmethod
    def validate_filter_key(cls, value):
        if (not value is None) and len(value) == 0:
            raise ValueError("'filter_key' cannot be empty")

        return value

    @field_validator("filter_value", mode="after")
    @classmethod
    def validate_filter_value(cls, value, validation_information):
        filter_key = (
            validation_information.data["filter_key"]
            if "filter_key" in validation_information.data
            else None
        )

        if not value is None and len(value) == 0:
            raise ValueError("'filter_value' cannot be empty")

        if (filter_key is None and not value is None) or (
            not filter_key is None and len(filter_key) == 0
        ):
            raise ValueError("'filter_key' must be defined")

        return value


class PresenterQueryDownloadValidator(PresenterQueryParamsValidator):
    file_type: FileDownloadChoiceEnum
