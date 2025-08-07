import os
from pathlib import Path

import polars as pl

# Import the actual smart reader implementation from storage
from storage import Storage
from testing import ParquetTestData

from .ngram_stats.interface import OUTPUT_NGRAM_FULL, OUTPUT_NGRAM_STATS
from .ngram_stats.main import main
from .ngrams_base.interface import (
    OUTPUT_MESSAGE,
    OUTPUT_MESSAGE_NGRAMS,
    OUTPUT_NGRAM_DEFS,
)
from .test_data import test_data_dir


# This example shows you how to test a secondary analyzer.
# It runs on pytest.
def test_ngram_stats():
    """
    Custom test for ngram_stats that handles non-deterministic ngram_id assignment.

    This test compares the content by sorting by text content rather than ngram_id,
    since the ngram_id values can vary between runs due to hash-based operations.
    """
    import os
    import tempfile

    import polars as pl

    from testing.testers import TestSecondaryAnalyzerContext

    # Set up test data exactly like the standard test
    primary_outputs = {
        OUTPUT_MESSAGE_NGRAMS: ParquetTestData(
            filepath=str(Path(test_data_dir, OUTPUT_MESSAGE_NGRAMS + ".parquet"))
        ),
        OUTPUT_NGRAM_DEFS: ParquetTestData(
            filepath=str(Path(test_data_dir, OUTPUT_NGRAM_DEFS + ".parquet"))
        ),
        OUTPUT_MESSAGE: ParquetTestData(
            filepath=str(Path(test_data_dir, OUTPUT_MESSAGE + ".parquet"))
        ),
    }

    # Load expected outputs
    expected_ngram_stats = pl.read_parquet(
        str(Path(test_data_dir, OUTPUT_NGRAM_STATS + ".parquet"))
    )
    expected_ngram_full = pl.read_parquet(
        str(Path(test_data_dir, OUTPUT_NGRAM_FULL + ".parquet"))
    )

    # Run the analyzer
    with tempfile.TemporaryDirectory(
        delete=True
    ) as temp_dir, tempfile.TemporaryDirectory(
        delete=True
    ) as actual_output_dir, tempfile.TemporaryDirectory(
        delete=True
    ) as actual_base_output_dir:

        # Convert primary outputs to parquet files
        for output_id, output_data in primary_outputs.items():
            output_data.convert_to_parquet(
                os.path.join(actual_base_output_dir, f"{output_id}.parquet")
            )

        # Create test context
        context = TestSecondaryAnalyzerContext(
            temp_dir=temp_dir,
            primary_param_values={},
            primary_output_parquet_paths={
                output_id: os.path.join(actual_base_output_dir, f"{output_id}.parquet")
                for output_id in primary_outputs.keys()
            },
            dependency_output_parquet_paths={},
            output_parquet_root_path=actual_output_dir,
        )

        # Run the analyzer
        main(context)

        # Load actual outputs (use storage's smart reader for multi-file dataset support)
        actual_ngram_stats = pl.read_parquet(context.output_path(OUTPUT_NGRAM_STATS))
        # Create temporary storage instance to use its smart reader
        temp_storage = Storage(app_name="Test", app_author="Test")
        actual_ngram_full = temp_storage._read_parquet_smart(
            context.output_path(OUTPUT_NGRAM_FULL)
        )

        # Compare ngram_stats with content-based sorting
        # Sort both by words, n, total_reps, distinct_posters to normalize for comparison
        expected_stats_sorted = expected_ngram_stats.select(
            ["words", "n", "total_reps", "distinct_posters"]
        ).sort(["words", "n", "total_reps", "distinct_posters"])

        actual_stats_sorted = actual_ngram_stats.select(
            ["words", "n", "total_reps", "distinct_posters"]
        ).sort(["words", "n", "total_reps", "distinct_posters"])

        # Check shapes and content match
        assert actual_stats_sorted.shape == expected_stats_sorted.shape, (
            f"ngram_stats shape mismatch: expected {expected_stats_sorted.shape}, "
            f"got {actual_stats_sorted.shape}"
        )

        assert actual_stats_sorted.equals(
            expected_stats_sorted
        ), "ngram_stats content differs when sorted by content"

        # For ngram_full, compare content grouped by ngram text
        # Group by words and compare the counts and user data
        expected_full_grouped = (
            expected_ngram_full.group_by("words")
            .agg(
                [
                    pl.col("n").first(),
                    pl.col("total_reps").first(),
                    pl.col("distinct_posters").first(),
                    pl.col("user_id").count().alias("user_count"),
                    pl.col("message_surrogate_id").n_unique().alias("unique_messages"),
                ]
            )
            .sort("words")
        )

        actual_full_grouped = (
            actual_ngram_full.group_by("words")
            .agg(
                [
                    pl.col("n").first(),
                    pl.col("total_reps").first(),
                    pl.col("distinct_posters").first(),
                    pl.col("user_id").count().alias("user_count"),
                    pl.col("message_surrogate_id").n_unique().alias("unique_messages"),
                ]
            )
            .sort("words")
        )

        # Check that the grouped content matches
        assert actual_full_grouped.shape == expected_full_grouped.shape, (
            f"ngram_full grouped shape mismatch: expected {expected_full_grouped.shape}, "
            f"got {actual_full_grouped.shape}"
        )

        assert actual_full_grouped.equals(
            expected_full_grouped
        ), "ngram_full content differs when grouped by words"


def test_ngram_stats_with_progress_manager():
    """
    Test that ngram_stats works correctly when provided with an existing progress manager.

    This test verifies that the analyzer can continue from an existing progress manager
    instead of creating a new one, which is the desired behavior when running as part
    of a pipeline with the primary n-gram analyzer.
    """
    import os
    import tempfile
    from unittest.mock import Mock

    from terminal_tools.progress import RichProgressManager
    from testing.testers import TestSecondaryAnalyzerContext

    # Set up test data
    primary_outputs = {
        OUTPUT_MESSAGE_NGRAMS: ParquetTestData(
            filepath=str(Path(test_data_dir, OUTPUT_MESSAGE_NGRAMS + ".parquet"))
        ),
        OUTPUT_NGRAM_DEFS: ParquetTestData(
            filepath=str(Path(test_data_dir, OUTPUT_NGRAM_DEFS + ".parquet"))
        ),
        OUTPUT_MESSAGE: ParquetTestData(
            filepath=str(Path(test_data_dir, OUTPUT_MESSAGE + ".parquet"))
        ),
    }

    # Run the analyzer with a mock progress manager
    with tempfile.TemporaryDirectory(
        delete=True
    ) as temp_dir, tempfile.TemporaryDirectory(
        delete=True
    ) as actual_output_dir, tempfile.TemporaryDirectory(
        delete=True
    ) as actual_base_output_dir:

        # Convert primary outputs to parquet files
        for output_id, output_data in primary_outputs.items():
            output_data.convert_to_parquet(
                os.path.join(actual_base_output_dir, f"{output_id}.parquet")
            )

        # Create test context with a mock progress manager
        context = TestSecondaryAnalyzerContext(
            temp_dir=temp_dir,
            primary_param_values={},
            primary_output_parquet_paths={
                output_id: os.path.join(actual_base_output_dir, f"{output_id}.parquet")
                for output_id in primary_outputs.keys()
            },
            dependency_output_parquet_paths={},
            output_parquet_root_path=actual_output_dir,
        )

        # Add a mock progress manager to the context using setattr to bypass Pydantic validation
        mock_progress_manager = Mock(spec=RichProgressManager)
        object.__setattr__(context, "progress_manager", mock_progress_manager)

        # Run the analyzer
        main(context)

        # Verify that the mock progress manager methods were called
        # This confirms that the analyzer used the existing progress manager
        assert (
            mock_progress_manager.add_step.called
        ), "add_step should have been called on existing progress manager"
        assert (
            mock_progress_manager.start_step.called
        ), "start_step should have been called on existing progress manager"
        assert (
            mock_progress_manager.complete_step.called
        ), "complete_step should have been called on existing progress manager"

        # Verify outputs were created (functionality still works)
        assert os.path.exists(
            context.output_path(OUTPUT_NGRAM_STATS)
        ), "ngram_stats output should exist"

        # For ngram_full, check if it exists as either file or directory (multi-file dataset)
        ngram_full_path = context.output_path(OUTPUT_NGRAM_FULL)
        ngram_full_exists = os.path.exists(ngram_full_path)
        if not ngram_full_exists and ngram_full_path.endswith(".parquet"):
            # Check for multi-file dataset version
            base_path = ngram_full_path[:-8]
            dataset_path = f"{base_path}_dataset"
            ngram_full_exists = os.path.exists(dataset_path)

        assert (
            ngram_full_exists
        ), "ngram_full output should exist (as file or dataset directory)"


def test_ngram_full_multi_file_dataset():
    """
    Test that the ngram_full output is correctly created as a multi-file dataset.

    This test verifies that:
    1. The output is created as a directory (not a single file)
    2. The directory contains multiple chunk files
    3. Reading the multi-file dataset produces the same result as the expected output
    """
    import os
    import tempfile

    import polars as pl

    from testing.testers import TestSecondaryAnalyzerContext

    # Set up test data
    primary_outputs = {
        OUTPUT_MESSAGE_NGRAMS: ParquetTestData(
            filepath=str(Path(test_data_dir, OUTPUT_MESSAGE_NGRAMS + ".parquet"))
        ),
        OUTPUT_NGRAM_DEFS: ParquetTestData(
            filepath=str(Path(test_data_dir, OUTPUT_NGRAM_DEFS + ".parquet"))
        ),
        OUTPUT_MESSAGE: ParquetTestData(
            filepath=str(Path(test_data_dir, OUTPUT_MESSAGE + ".parquet"))
        ),
    }

    # Load expected output for comparison
    expected_ngram_full = pl.read_parquet(
        str(Path(test_data_dir, OUTPUT_NGRAM_FULL + ".parquet"))
    )

    # Run the analyzer
    with tempfile.TemporaryDirectory(
        delete=True
    ) as temp_dir, tempfile.TemporaryDirectory(
        delete=True
    ) as actual_output_dir, tempfile.TemporaryDirectory(
        delete=True
    ) as actual_base_output_dir:

        # Convert primary outputs to parquet files
        for output_id, output_data in primary_outputs.items():
            output_data.convert_to_parquet(
                os.path.join(actual_base_output_dir, f"{output_id}.parquet")
            )

        # Create test context
        context = TestSecondaryAnalyzerContext(
            temp_dir=temp_dir,
            primary_param_values={},
            primary_output_parquet_paths={
                output_id: os.path.join(actual_base_output_dir, f"{output_id}.parquet")
                for output_id in primary_outputs.keys()
            },
            dependency_output_parquet_paths={},
            output_parquet_root_path=actual_output_dir,
        )

        # Run the analyzer
        main(context)

        # Check that the output path is a directory (multi-file dataset)
        output_path = context.output_path(OUTPUT_NGRAM_FULL)

        # The analyzer creates a directory at the expected file path
        # because it calls os.makedirs(output_path, exist_ok=True)
        assert os.path.isdir(
            output_path
        ), f"Expected {output_path} to be a directory (multi-file dataset)"

        # Check that the directory contains chunk files
        chunk_files = [
            f
            for f in os.listdir(output_path)
            if f.startswith("chunk_") and f.endswith(".parquet")
        ]
        assert (
            len(chunk_files) > 0
        ), "Multi-file dataset directory should contain chunk files"
        assert any(
            f.startswith("chunk_0001") for f in chunk_files
        ), "Should contain chunk_0001.parquet"

        # Verify we can read the multi-file dataset using storage's smart reader
        temp_storage = Storage(app_name="Test", app_author="Test")
        actual_ngram_full = temp_storage._read_parquet_smart(output_path)

        # Verify the data is equivalent (using same grouping approach as main test)
        expected_full_grouped = (
            expected_ngram_full.group_by("words")
            .agg(
                [
                    pl.col("n").first(),
                    pl.col("total_reps").first(),
                    pl.col("distinct_posters").first(),
                    pl.col("user_id").count().alias("user_count"),
                    pl.col("message_surrogate_id").n_unique().alias("unique_messages"),
                ]
            )
            .sort("words")
        )

        actual_full_grouped = (
            actual_ngram_full.group_by("words")
            .agg(
                [
                    pl.col("n").first(),
                    pl.col("total_reps").first(),
                    pl.col("distinct_posters").first(),
                    pl.col("user_id").count().alias("user_count"),
                    pl.col("message_surrogate_id").n_unique().alias("unique_messages"),
                ]
            )
            .sort("words")
        )

        # Verify the multi-file dataset produces the same result
        assert actual_full_grouped.equals(
            expected_full_grouped
        ), "Multi-file dataset content should match expected output"
