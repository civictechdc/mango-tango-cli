import os.path
from contextlib import ExitStack
from tempfile import TemporaryDirectory
from typing import Callable

import polars as pl
import pytest

from analyzer_interface import AnalyzerInterface, SecondaryAnalyzerInterface
from analyzer_interface.context import PrimaryAnalyzerContext, SecondaryAnalyzerContext

from .comparers import compare_dfs
from .context import TestPrimaryAnalyzerContext, TestSecondaryAnalyzerContext
from .testdata import TestData


@pytest.mark.skip()
def test_primary_analyzer(
    interface: AnalyzerInterface,
    main: Callable[[PrimaryAnalyzerContext], None],
    *,
    input: TestData,
    outputs: dict[str, TestData],
):
    """
    Runs the primary analyzer test.

    Args:
        interface (AnalyzerInterface): The interface of the analyzer.
        main (Callable[[PrimaryAnalyzerContext], None]): The main function of the analyzer.
        input (TestData): The input data.
        outputs (dict[str, TestData]): The output data, keyed by output ID.
    """
    with ExitStack() as exit_stack:
        temp_dir = exit_stack.enter_context(TemporaryDirectory(delete=True))
        actual_output_dir = exit_stack.enter_context(TemporaryDirectory(delete=True))
        actual_input_dir = exit_stack.enter_context(TemporaryDirectory(delete=True))

        input_path = os.path.join(actual_input_dir, "input.parquet")
        input.convert_to_parquet(input_path)

        context = TestPrimaryAnalyzerContext(
            temp_dir=temp_dir,
            input_parquet_path=input_path,
            output_parquet_root_path=actual_output_dir,
        )
        main(context)

        specified_outputs = [output_spec.id for output_spec in interface.outputs]
        unused_outputs = [
            output_id
            for output_id in outputs.keys()
            if output_id not in specified_outputs
        ]
        if unused_outputs:
            raise ValueError(
                f"The test case provided outputs that are not specified in the interface: {unused_outputs}"
            )

        has_compared_output = any(
            outputs.get(output_spec.id) is not None for output_spec in interface.outputs
        )
        if not has_compared_output:
            raise ValueError("The test case did not compare any outputs.")

        for output_spec in interface.outputs:
            expected_output_data = outputs.get(output_spec.id)
            if expected_output_data is None:
                continue

            actual_output_path = context.output_path(output_spec.id)

            expected_output = expected_output_data.load()
            actual_output = pl.read_parquet(actual_output_path)
            compare_dfs(actual_output, expected_output)


@pytest.mark.skip()
def test_secondary_analyzer(
    interface: AnalyzerInterface,
    main: Callable[[SecondaryAnalyzerContext], None],
    *,
    primary_outputs: dict[str, TestData],
    dependency_outputs: dict[str, dict[str, TestData]] = dict(),
    expected_outputs: dict[str, TestData],
):
    """
    Runs the secondary analyzer test.

    Args:
        interface (AnalyzerInterface): The interface of the analyzer.
        main (Callable[[SecondaryAnalyzerInterface], None]): The main function of the analyzer.
        primary_outputs (dict[str, TestData]): The primary output data, keyed by output ID.
        dependency_outputs (dict[str, dict[str, TestData]]): The dependency output data, keyed by dependency ID and then by output ID.
        expected_outputs (dict[str, TestData]): The expected output data, keyed by output ID.
    """
    with ExitStack() as exit_stack:
        temp_dir = exit_stack.enter_context(TemporaryDirectory(delete=True))
        actual_output_dir = exit_stack.enter_context(TemporaryDirectory(delete=True))
        actual_base_output_dir = exit_stack.enter_context(
            TemporaryDirectory(delete=True)
        )
        actual_dependency_output_dirs = {
            dependency_id: exit_stack.enter_context(TemporaryDirectory(delete=True))
            for dependency_id in dependency_outputs.keys()
        }

        for output_id, output_data in primary_outputs.items():
            output_data.convert_to_parquet(
                os.path.join(actual_base_output_dir, f"{output_id}.parquet")
            )

        for dependency_id, dependency_output in dependency_outputs.items():
            for output_id, output_data in dependency_output.items():
                output_data.convert_to_parquet(
                    os.path.join(
                        actual_dependency_output_dirs[dependency_id],
                        f"{output_id}.parquet",
                    )
                )

        context = TestSecondaryAnalyzerContext(
            temp_dir=temp_dir,
            primary_output_parquet_paths={
                output_id: os.path.join(actual_base_output_dir, f"{output_id}.parquet")
                for output_id in primary_outputs.keys()
            },
            dependency_output_parquet_paths={
                dependency_id: {
                    output_id: os.path.join(
                        actual_dependency_output_dirs[dependency_id],
                        f"{output_id}.parquet",
                    )
                    for output_id in dependency_output.keys()
                }
                for dependency_id, dependency_output in dependency_outputs.items()
            },
            output_parquet_root_path=actual_output_dir,
        )
        main(context)

        specified_outputs = [output_spec.id for output_spec in interface.outputs]
        unused_outputs = [
            output_id
            for output_id in expected_outputs.keys()
            if output_id not in specified_outputs
        ]
        if unused_outputs:
            raise ValueError(
                f"The test case provided outputs that are not specified in the interface: {unused_outputs}"
            )

        has_compared_output = any(
            expected_outputs.get(output_spec.id) is not None
            for output_spec in interface.outputs
        )
        if not has_compared_output:
            raise ValueError("The test case did not compare any outputs.")

        for output_spec in interface.outputs:
            expected_output_data = expected_outputs.get(output_spec.id)
            if expected_output_data is None:
                continue

            actual_output_path = context.output_path(output_spec.id)

            expected_output = expected_output_data.load()
            actual_output = pl.read_parquet(actual_output_path)
            compare_dfs(actual_output, expected_output)
