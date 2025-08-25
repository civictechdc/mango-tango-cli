from datetime import datetime

import polars as pl

from preprocessing.series_semantic import (
    date_string,
    datetime_string,
    infer_series_semantic,
    native_date,
    native_datetime,
    parse_datetime_with_tz,
    text_catch_all,
    time_string,
)


# Individual Semantic Pattern Tests
def test_native_date_recognition():
    """Test that pl.Date columns get recognized correctly"""
    series = pl.Series(
        [datetime(2025, 1, 1).date(), datetime(2025, 1, 2).date()], dtype=pl.Date
    )
    assert native_date.check(series)


def test_native_datetime_recognition():
    """Test that pl.Datetime columns get recognized correctly"""
    series = pl.Series([datetime(2025, 1, 1, 12, 0), datetime(2025, 1, 2, 13, 0)])
    assert native_datetime.check(series)


def test_datetime_with_timezone_parsing():
    """Test parsing datetime strings with timezone"""
    series = pl.Series(["2025-02-28 00:36:15 UTC", "2025-02-28 00:36:13 UTC"])
    assert datetime_string.check(series)

    # Test conversion
    result = datetime_string.try_convert(series)
    assert result.dtype == pl.Datetime
    assert result.is_not_null().all()


def test_date_string_parsing():
    """Test date-only string parsing"""
    series = pl.Series(["2025-02-28", "2025-02-27"])
    assert date_string.check(series)

    result = date_string.try_convert(series)
    assert result.dtype == pl.Date
    assert result.is_not_null().all()


def test_time_string_parsing():
    """Test time-only string parsing"""
    series = pl.Series(["14:30:15", "09:15:30"])
    assert time_string.check(series)

    result = time_string.try_convert(series)
    assert result.dtype == pl.Time
    assert result.is_not_null().all()


def test_text_catch_all():
    """Test free form text parsing"""
    series = pl.Series(
        ["First post with some content!", "a different no all caps post", "THIRD POST"]
    )
    assert text_catch_all.check(series)

    result = text_catch_all.try_convert(series)
    assert result.dtype == pl.String

    semantic = infer_series_semantic(series)
    assert semantic.semantic_name == "free_text"
    assert semantic.data_type == "text"


def test_datetime_timezone_inference():
    """Test main inference function with timezone datetime"""
    series = pl.Series(["2025-02-28 00:36:15 UTC"] * 10)
    semantic = infer_series_semantic(series)

    assert semantic is not None
    assert semantic.semantic_name == "datetime"
    assert semantic.data_type == "datetime"


def test_native_types_inference():
    """Test that native temporal types get recognized"""
    date_series = pl.Series([datetime(2025, 1, 1).date()] * 10, dtype=pl.Date)
    datetime_series = pl.Series([datetime(2025, 1, 1, 12, 0)] * 10)

    assert infer_series_semantic(date_series).semantic_name == "native_date"
    assert infer_series_semantic(datetime_series).semantic_name == "native_datetime"


def test_threshold_behavior():
    """Test that recognition threshold works correctly"""

    # 70% of data is date, the rest is text
    mixed_series = pl.Series(["2025-01-01 UTC"] * 7 + ["not_a_date"] * 3)

    # Should work with the right threshold (i.e. > 50%)
    semantic_low = infer_series_semantic(mixed_series, threshold=0.5)
    assert semantic_low.semantic_name == "datetime"

    # Check a threshold that's not met, should defer to free_text
    semantic_high = infer_series_semantic(mixed_series, threshold=0.8)
    assert semantic_high.semantic_name == "free_text"


# Phase 3: Helper Function Tests
def test_parse_datetime_with_tz():
    """Test timezone parsing helper function"""

    # Use same timezone to avoid warning
    series = pl.Series(["2025-02-28 00:36:15 UTC", "2025-02-28 00:36:13 UTC"])
    result = parse_datetime_with_tz(series)

    assert isinstance(result, pl.Series)
    assert result.dtype == pl.Datetime
    assert result.is_not_null().all()


def test_parse_datetime_with_tz_no_timezone():
    """Test datetime parsing without timezone suffix"""
    series = pl.Series(["2025-02-28 00:36:15", "2025-02-28 00:36:13"])
    result = parse_datetime_with_tz(series)

    assert result.dtype == pl.Datetime
    assert result.is_not_null().all()


def test_parse_datetime_with_tz_offset():
    """Test datetime parsing with timezone offset format"""
    series = pl.Series(
        ["2025-01-27 00:07:12.056000-05:00", "2025-01-27 00:07:16.126000-05:00"]
    )
    result = parse_datetime_with_tz(series)

    assert result.dtype == pl.Datetime
    assert result.is_not_null().all()


def test_datetime_with_timezone_offset_parsing():
    """Test timezone offset datetime strings get recognized as datetime semantic"""
    series = pl.Series(
        ["2025-01-27 00:07:12.056000-05:00", "2025-01-27 00:07:16.126000-05:00"]
    )
    assert datetime_string.check(series)

    # Test conversion
    result = datetime_string.try_convert(series)
    assert result.dtype == pl.Datetime
    assert result.is_not_null().all()


def test_parse_datetime_mixed_timezones_warning():
    """Test that mixed timezones trigger a warning"""
    import warnings

    # Series with mixed timezone abbreviations and offsets
    series = pl.Series(
        [
            "2025-01-27 00:07:12 UTC",
            "2025-01-27 00:07:16-05:00",
            "2025-01-27 00:07:20 EST",
        ]
    )

    # Capture warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = parse_datetime_with_tz(series)

        # Should have issued a warning
        assert len(w) == 1
        assert issubclass(w[0].category, UserWarning)
        assert "Multiple timezones found" in str(w[0].message)
        assert "UTC" in str(w[0].message)
        assert "-05:00" in str(w[0].message)
        assert "EST" in str(w[0].message)

    # But parsing should still work
    assert result.dtype == pl.Datetime
    assert result.is_not_null().all()


# Edge cases
def test_all_none_series():
    """Test series with all null values"""
    null_series = pl.Series([None, None, None], dtype=pl.String)
    semantic = infer_series_semantic(null_series)
    assert semantic.semantic_name == "free_text"


def test_mixed_valid_invalid_dates():
    """Test series with mix of valid and invalid datetime strings"""
    mixed_series = pl.Series(["2025-01-01 UTC", "invalid_date", "2025-01-02 UTC"])
    semantic = infer_series_semantic(mixed_series)
    # should be free_text with threshold 0.8
    assert semantic.semantic_name == "free_text"

    semantic = infer_series_semantic(series=mixed_series, threshold=0.2)
    assert semantic.semantic_name == "datetime"
