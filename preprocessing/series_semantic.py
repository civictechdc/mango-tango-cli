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


def parse_time_military(s: pl.Series) -> pl.Series:
    """Parse time strings with multiple format attempts"""
    # Try different time formats
    FORMATS_TO_TRY = ["%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p"]

    for fmt in FORMATS_TO_TRY:
        try:
            result = s.str.strptime(pl.Time, format=fmt, strict=False)
            if result.is_not_null().sum() > 0:  # If any parsed successfully
                return result
        except:
            continue

    # If all formats fail, return nulls
    return pl.Series([None] * s.len(), dtype=pl.Time)


def parse_datetime_with_tz(s: pl.Series) -> pl.Series:
    """Parse datetime strings with timezone info (both abbreviations and offsets)"""
    import warnings

    # Handle timezone abbreviations like "UTC", "EST"
    tz_abbrev_regex = r" ([A-Z]{3,4})$"  # UTC, EST, etc.

    # Handle timezone offsets like "-05:00", "+00:00"
    tz_offset_regex = r"[+-]\d{2}:\d{2}$"  # -05:00, +00:00, etc.

    # Check for multiple different timezones
    abbrev_matches = s.str.extract_all(tz_abbrev_regex)
    offset_matches = s.str.extract_all(tz_offset_regex)

    # Get unique timezone abbreviations
    unique_abbrevs = set()
    if not abbrev_matches.is_empty():
        for match_list in abbrev_matches.to_list():
            if match_list:  # Not empty
                unique_abbrevs.update(match_list)

    # Get unique timezone offsets
    unique_offsets = set()
    if not offset_matches.is_empty():
        for match_list in offset_matches.to_list():
            if match_list:  # Not empty
                unique_offsets.update(match_list)

    # Warn if multiple different timezones found
    total_unique_tz = len(unique_abbrevs) + len(unique_offsets)
    if total_unique_tz > 1:
        all_tz = list(unique_abbrevs) + list(unique_offsets)
        warnings.warn(
            f"Multiple timezones found in datetime column: {all_tz}. "
            f"Assuming all timestamps represent the same timezone for analysis purposes.",
            UserWarning,
        )

    # Try to remove timezone abbreviations first
    result = s.str.replace(tz_abbrev_regex, "")

    # Then remove timezone offsets
    result = result.str.replace(tz_offset_regex, "")

    return result.str.strptime(pl.Datetime(), strict=False)


native_date = SeriesSemantic(
    semantic_name="native_date",
    column_type=pl.Date,  # Matches native Date columns
    try_convert=lambda s: s,  # No conversion needed
    validate_result=lambda s: constant_series(s, True),  # Always valid
    data_type="datetime",
)

native_datetime = SeriesSemantic(
    semantic_name="native_datetime",
    column_type=pl.Datetime,  # Matches native DateTime columns
    try_convert=lambda s: s,  # No conversion needed
    validate_result=lambda s: constant_series(s, True),  # Always valid
    data_type="datetime",
)

time_military = SeriesSemantic(
    semantic_name="time_military",
    column_type=pl.String,
    try_convert=parse_time_military,
    validate_result=lambda s: s.is_not_null(),
    data_type="datetime",
)

datetime_string = SeriesSemantic(
    semantic_name="datetime",
    column_type=pl.String,
    try_convert=parse_datetime_with_tz,
    validate_result=lambda s: s.is_not_null(),
    data_type="datetime",
)

date_string = SeriesSemantic(
    semantic_name="date",
    column_type=pl.String,
    try_convert=lambda s: s.str.strptime(pl.Date, strict=False),  # Convert to pl.Date
    validate_result=lambda s: s.is_not_null(),
    data_type="datetime",  # Still maps to datetime for analyzer compatibility
)

time_string = SeriesSemantic(
    semantic_name="time",
    column_type=pl.String,
    try_convert=lambda s: s.str.strptime(pl.Time, strict=False),  # Convert to pl.Time
    validate_result=lambda s: s.is_not_null(),
    data_type="time",
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
    native_datetime,
    native_date,
    datetime_string,
    date_string,
    time_string,
    time_military,
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
