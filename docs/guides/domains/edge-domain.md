## Edge Domain

The Edge domain governs data import and export.

### Importers

The Importers live inside the `importing` directory inside the project root. Each importer offers a new way to import data into the workspace. The importers should be agnostic about the available analyzers. However, the Importers currently provide a terminal user flow so that their options can be customized by the user—a necessity since each importer may expose different sets of options and may have different UX approaches for their configuration.

The importers eventually write data to a parquet file, whose path is provisioned by the application.

Here's what the entrypoint for the importer module looks like

**./importing/__init__.py**:

```python
from .csv import CSVImporter
from .excel import ExcelImporter
from .importer import Importer, ImporterSession

importers: list[Importer[ImporterSession]] = [CSVImporter(), ExcelImporter()]
```

### Semantic Preprocessor

The Semantic Preprocessor lives inside the `preprocessing` directory inside the project root. It defines all the column data semantics—a kind of type system that is used to guide the user in selecting the right columns for the right analysis. It is agnostic about the specific analyzers but does depend on them in a generic way—the available semantics exist to support the needs of analyzers and will be extended as necessary.

Here's what the entrypoint for the preprocessing module looks like

**./preprocessing/series_semantic.py**:

```python
from datetime import datetime
from typing import Callable, Type, Union

import polars as pl
from pydantic import BaseModel

from analyzer_interface import DataType


class SeriesSemantic(BaseModel):
    semantic_name: str
    column_type: Union[Type[pl.DataType], Callable[[pl.DataType], bool]]
    prevalidate: Callable[[pl.Series], bool] = lambda s: True
    try_convert: Callable[[pl.Series], pl.Series]
    validate_result: Callable[[pl.Series], pl.Series] = lambda s: s.is_not_null()
    data_type: DataType

    def check(self, series: pl.Series, threshold: float = 0.8, sample_size: int = 100):
        if not self.check_type(series):
            return False

        sample = sample_series(series, sample_size)
        try:
            if not self.prevalidate(sample):
                return False
            result = self.try_convert(sample)
        except Exception:
            return False
        return self.validate_result(result).sum() / sample.len() > threshold

    def check_type(self, series: pl.Series):
        if isinstance(self.column_type, type):
            return isinstance(series.dtype, self.column_type)
        return self.column_type(series.dtype)


datetime_string = SeriesSemantic(
    semantic_name="datetime",
    column_type=pl.String,
    try_convert=lambda s: s.str.strptime(pl.Datetime, strict=False),
    data_type="datetime",
)


timestamp_seconds = SeriesSemantic(
    semantic_name="timestamp_seconds",
    column_type=lambda dt: dt.is_numeric(),
    try_convert=lambda s: (s * 1_000).cast(pl.Datetime(time_unit="ms")),
    validate_result=lambda s: ((s > datetime(2000, 1, 1)) & (s < datetime(2100, 1, 1))),
    data_type="datetime",
)

timestamp_milliseconds = SeriesSemantic(
    semantic_name="timestamp_milliseconds",
    column_type=lambda dt: dt.is_numeric(),
    try_convert=lambda s: s.cast(pl.Datetime(time_unit="ms")),
    validate_result=lambda s: ((s > datetime(2000, 1, 1)) & (s < datetime(2100, 1, 1))),
    data_type="datetime",
)

url = SeriesSemantic(
    semantic_name="url",
    column_type=pl.String,
    try_convert=lambda s: s.str.strip_chars(),
    validate_result=lambda s: s.str.count_matches("^https?://").gt(0),
    data_type="url",
)

identifier = SeriesSemantic(
    semantic_name="identifier",
    column_type=pl.String,
    try_convert=lambda s: s.str.strip_chars(),
    validate_result=lambda s: s.str.count_matches(r"^@?[A-Za-z0-9_.:-]+$").eq(1),
    data_type="identifier",
)

text_catch_all = SeriesSemantic(
    semantic_name="free_text",
    column_type=pl.String,
    try_convert=lambda s: s,
    validate_result=lambda s: constant_series(s, True),
    data_type="text",
)

integer_catch_all = SeriesSemantic(
    semantic_name="integer",
    column_type=lambda dt: dt.is_integer(),
    try_convert=lambda s: s,
    validate_result=lambda s: constant_series(s, True),
    data_type="integer",
)

float_catch_all = SeriesSemantic(
    semantic_name="float",
    column_type=lambda dt: dt.is_float(),
    try_convert=lambda s: s,
    validate_result=lambda s: constant_series(s, True),
    data_type="float",
)

boolean_catch_all = SeriesSemantic(
    semantic_name="boolean",
    column_type=pl.Boolean,
    try_convert=lambda s: s,
    validate_result=lambda s: constant_series(s, True),
    data_type="boolean",
)

all_semantics = [
    datetime_string,
    timestamp_seconds,
    timestamp_milliseconds,
    url,
    identifier,
    text_catch_all,
    integer_catch_all,
    float_catch_all,
    boolean_catch_all,
]


def infer_series_semantic(
    series: pl.Series, *, threshold: float = 0.8, sample_size=100
):
    for semantic in all_semantics:
        if semantic.check(series, threshold=threshold, sample_size=sample_size):
            return semantic
    return None


def sample_series(series: pl.Series, n: int = 100):
    if series.len() < n:
        return series
    return series.sample(n, seed=0)


def constant_series(series: pl.Series, constant) -> pl.Series:
    """Create a series with a constant value for each row of `series`."""
    return pl.Series([constant] * series.len(), dtype=pl.Boolean)
```

# Next Steps

Once you finish reading this section it would be a good idea to review the other domain sections. Might also be a good idea to review the sections that discuss implementing  [Shiny](https://shiny.posit.co/py/), and [React](https://react.dev) dashboards.

- [Core Domain](./core-domain.md)
- [Content Domain](./content-domain.md)
- [Shiny Dashboards](../dashboards/shiny.md)
- [React Dashboards](../dashboards/react.md)