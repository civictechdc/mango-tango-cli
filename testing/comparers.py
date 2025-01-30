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

    if actual.equals(expected):
        return

    # find rows that are different
    row_index_column = "@row_index"
    actual = actual.select(
        [pl.Series(row_index_column, range(actual.height)), *actual.columns]
    )
    expected = expected.select(
        [pl.Series(row_index_column, range(expected.height)), *expected.columns]
    )

    # Find row-wise differences
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
