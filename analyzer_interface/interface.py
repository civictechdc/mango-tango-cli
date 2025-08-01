from typing import Literal, Optional

import polars as pl
from pydantic import BaseModel

from .params import ParamType, ParamValue


class BaseAnalyzerInterface(BaseModel):
    id: str
    """
  The static ID for the analyzer that, with the version, uniquely identifies the
  analyzer and will be stored as metadata as part of the output data.
  """

    version: str
    """
  The version ID for the analyzer. In future, we may choose to support output
  migration between versions of the same analyzer.
  """

    name: str
    """
  The short human-readable name of the analyzer.
  """

    short_description: str
    """
  A short, one-liner description of what the analyzer does.
  """

    long_description: Optional[str] = None
    """
  A longer description of what the analyzer does that will be shown separately.
  """


class AnalyzerInput(BaseModel):
    columns: list["InputColumn"]


class AnalyzerParam(BaseModel):
    id: str
    """
    The name of the parameter. This becomes the key in the parameters dictionary
    that is passed to the analyzer.
    """

    human_readable_name: Optional[str] = None
    """
    The human-friendly name for the parameter. This is used in the UI to
    represent the parameter.
    """

    description: Optional[str] = None
    """
    A short description of the parameter. This is used in the UI to represent
    the parameter.
    """

    type: ParamType
    """
    The type of the parameter. This is used for validation and for customizing
    the UX for parameter input.
    """

    default: Optional[ParamValue] = None
    """
    Optional: define a static default value for this parameter. A parameter
    without a default will need to be chosen explicitly by the user.
    """

    backfill_value: Optional[ParamValue] = None
    """
    Recommended if this is a parameter that is newly introduced in a previously
    released analyzer. The backfill is show what this parameter was before it
    became customizable.
    """

    @property
    def print_name(self):
        return self.human_readable_name or self.id


class AnalyzerOutput(BaseModel):
    id: str
    """
  Uniquely identifies the output data schema for the analyzer. The analyzer
  must include this key in the output dictionary.
  """

    name: str
    """The human-friendly for the output."""

    description: Optional[str] = None

    columns: list["OutputColumn"]

    internal: bool = False

    def get_column_by_name(self, name: str):
        for column in self.columns:
            if column.name == name:
                return column
        return None

    def transform_output(self, output_df: pl.LazyFrame | pl.DataFrame):
        output_columns = output_df.lazy().collect_schema().names()
        return output_df.select(
            [
                pl.col(col_name).alias(
                    output_spec.human_readable_name_or_fallback()
                    if output_spec
                    else col_name
                )
                for col_name in output_columns
                if (output_spec := self.get_column_by_name(col_name)) or True
            ]
        )


class AnalyzerInterface(BaseAnalyzerInterface):
    input: AnalyzerInput
    """
  Specifies the input data schema for the analyzer.
  """

    params: list[AnalyzerParam] = []
    """
  A list of parameters that the analyzer accepts.
  """

    outputs: list["AnalyzerOutput"]
    """
  Specifies the output data schema for the analyzer.
  """

    kind: Literal["primary"] = "primary"


class DerivedAnalyzerInterface(BaseAnalyzerInterface):
    base_analyzer: AnalyzerInterface
    """
  The base analyzer that this secondary analyzer extends. This is always a primary
  analyzer. If your module depends on other secondary analyzers (which must have
  the same base analyzer), you can specify them in the `depends_on` field.
  """

    depends_on: list["SecondaryAnalyzerInterface"] = []
    """
  A dictionary of secondary analyzers that must be run before the current analyzer
  secondary analyzer is run. These secondary analyzers must have the same
  primary base.
  """


class SecondaryAnalyzerInterface(DerivedAnalyzerInterface):
    outputs: list[AnalyzerOutput]
    """
  Specifies the output data schema for the analyzer.
  """

    kind: Literal["secondary"] = "secondary"


class WebPresenterInterface(DerivedAnalyzerInterface):
    kind: Literal["web"] = "web"


DataType = Literal[
    "text", "integer", "float", "boolean", "datetime", "identifier", "url", "time"
]
"""
The semantic data type for a data column. This is not quite the same as
structural data types like polars or pandas or even arrow types, but they
represent how the data is intended to be interpreted.

- `text` is expected to be a free-form human-readable text content.
- `integer` and `float` are meant to be manipulated arithmetically.
- `boolean` is a binary value.
- `datetime` represents time and are meant to be manipulated as time values.
- `time` represents time within a day, not including the date information.
- `identifier` is a unique identifier for a record. It is not expected to be manipulated in any way.
- `url` is a string that represents a URL.
"""


class Column(BaseModel):
    name: str
    human_readable_name: Optional[str] = None
    description: Optional[str] = None
    data_type: DataType

    def human_readable_name_or_fallback(self):
        return self.human_readable_name or self.name


class InputColumn(Column):
    name_hints: list[str] = []
    """
  Specifies a list of space-separated words that are likely to be found in the
  column name of the user-provided data. This is used to help the user map the
  input columns to the expected columns.

  Any individual hint matching is sufficient for a match to be called. The hint
  in turn is matched if every word matches some part of the column name.
  """


class OutputColumn(Column):
    pass


def backfill_param_values(
    param_values: dict[str, ParamValue], analyzer_spec: AnalyzerInterface
) -> dict[str, ParamValue]:
    return {
        param_spec.id: param_values.get(param_spec.id) or param_spec.backfill_value
        for param_spec in analyzer_spec.params
    }
