import polars as pl


def compare_dfs(actual: pl.DataFrame, expected: pl.DataFrame):
    if actual.shape != expected.shape:
        raise ValueError(
            "DataFrames have different shapes\n"
            f"Expected: {expected.shape}\n"
            f"Actual: {actual.shape}"
        )

    if set(actual.columns) != set(expected.columns):
        raise ValueError(
            "DataFrames have different columns\n"
            f"Expected: {sorted(expected.columns)}\n"
            f"Actual: {sorted(actual.columns)}"
        )

    if not actual.dtypes == expected.dtypes:
        combined = pl.concat([actual, expected], how="vertical_relaxed")
        actual = combined.head(actual.height)
        expected = combined.tail(expected.height)

        if not actual.dtypes == expected.dtypes:
            raise ValueError(
                "DataFrames have different types that cannot be reconciled:\n"
                f"Expected: {expected.dtypes}\n"
                f"Actual: {actual.dtypes}"
            )

    # First try exact equality
    if actual.equals(expected):
        return

    # For approximate floating point comparison, check each column separately
    floating_point_types = [pl.Float32, pl.Float64]

    # Check if all columns are approximately equal
    columns_match = True
    for col in actual.columns:
        actual_col = actual[col]
        expected_col = expected[col]

        if actual_col.dtype in floating_point_types:
            # Use approximate equality for floating point columns
            # Handle null values separately
            actual_is_null = actual_col.is_null()
            expected_is_null = expected_col.is_null()

            # Check if null patterns match
            if not actual_is_null.equals(expected_is_null):
                columns_match = False
                break

            # For non-null values, use approximate equality
            non_null_mask = ~actual_is_null
            if non_null_mask.any():
                actual_values = actual_col.filter(non_null_mask)
                expected_values = expected_col.filter(non_null_mask)

                # Check approximate equality with relative tolerance
                abs_diff = (actual_values - expected_values).abs()
                relative_tolerance = 1e-10  # Very tight tolerance
                absolute_tolerance = 1e-10
                max_allowed_diff = (
                    expected_values.abs() * relative_tolerance + absolute_tolerance
                )

                if not (abs_diff <= max_allowed_diff).all():
                    columns_match = False
                    break
        else:
            # Use exact equality for non-floating point columns
            if not actual_col.equals(expected_col):
                columns_match = False
                break

    if columns_match:
        return

    # find rows that are different
    row_index_column = "@row_index"
    actual = actual.select(
        [pl.Series(row_index_column, range(actual.height)), *actual.columns]
    )
    expected = expected.select(
        [pl.Series(row_index_column, range(expected.height)), *expected.columns]
    )

    # Find row-wise differences (using exact comparison for error reporting)
    mask = pl.any_horizontal([actual[col] != expected[col] for col in actual.columns])

    # Get differing rows with index
    actual_different = actual.filter(mask)
    expected_different = expected.filter(mask)

    difference_count = actual_different.height
    raise ValueError(
        f"DataFrames are different. Found {difference_count} differing rows.\n"
        f"Use the `{row_index_column}` column to find the differing rows.\n"
        f"Expected:\n{expected_different.head(10)}\n\n"
        f"Actual:\n{actual_different.head(10)}\n\n"
        + ("(Showing only the first 10 rows.)" if difference_count > 10 else "")
    )
