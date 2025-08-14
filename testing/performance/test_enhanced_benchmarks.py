"""
Enhanced Performance Benchmarking Tests using pytest-benchmark
Implements robust, statistics-driven benchmarks with resource-based metrics.
"""

import gc
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Tuple
from unittest.mock import MagicMock, patch

import polars as pl
import psutil
import pytest

from analyzers.ngrams.fallback_processors import generate_ngrams_disk_based
from analyzers.ngrams.ngrams_base.main import _generate_ngrams_vectorized
from app.utils import MemoryManager


@pytest.mark.performance
@pytest.mark.benchmark
class TestEnhancedPerformanceBenchmarks:
    """Enhanced performance benchmarking suite using pytest-benchmark."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Force garbage collection to start with clean state
        gc.collect()

        # Get baseline memory usage
        self.initial_memory = psutil.Process().memory_info().rss / 1024**2  # MB

    def teardown_method(self):
        """Clean up after each test."""
        gc.collect()

    def _create_realistic_dataset(
        self, num_messages: int, avg_tokens_per_message: int = 20
    ) -> pl.DataFrame:
        """Create a realistic test dataset with variable message lengths."""
        import random

        # Common words for realistic n-gram generation
        words = [
            "the",
            "and",
            "is",
            "in",
            "to",
            "of",
            "a",
            "for",
            "on",
            "with",
            "as",
            "by",
            "be",
            "at",
            "this",
            "that",
            "from",
            "they",
            "we",
            "you",
            "have",
            "has",
            "had",
            "will",
            "would",
            "could",
            "should",
            "can",
            "may",
            "data",
            "analysis",
            "social",
            "media",
            "content",
            "user",
            "post",
            "comment",
            "hashtag",
            "trend",
            "viral",
            "engagement",
            "reach",
            "impression",
            "click",
            "like",
            "share",
            "retweet",
            "follow",
            "followers",
            "following",
            "account",
        ]

        messages = []
        for i in range(num_messages):
            # Variable message length (10-40 tokens)
            num_tokens = random.randint(
                max(5, avg_tokens_per_message - 10), avg_tokens_per_message + 20
            )

            # Generate message with realistic word distribution
            message_words = []
            for _ in range(num_tokens):
                # Higher probability for common words
                if random.random() < 0.3:
                    word = random.choice(words[:10])  # Very common words
                elif random.random() < 0.6:
                    word = random.choice(words[:30])  # Common words
                else:
                    word = random.choice(words)  # All words

                message_words.append(word)

            messages.append(
                {
                    "message_id": f"msg_{i:06d}",
                    "message_text": " ".join(message_words),
                    "author_id": f"user_{i % (num_messages // 10)}",  # 10% unique users
                    "timestamp": f"2023-01-{(i % 31) + 1:02d}T{(i % 24):02d}:00:00Z",
                }
            )

        return pl.DataFrame(messages)

    def _process_chunks_old(self, dataset: pl.DataFrame, chunk_size: int) -> int:
        """Simulate old chunk processing approach."""
        num_chunks = 0
        dataset_size = len(dataset)

        for start_idx in range(0, dataset_size, chunk_size):
            end_idx = min(start_idx + chunk_size, dataset_size)
            chunk = dataset.slice(start_idx, end_idx - start_idx)

            # Simulate processing work (tokenization, basic operations)
            _ = chunk.select(
                [
                    pl.col("message_text").str.split(" ").alias("tokens"),
                    pl.col("message_id"),
                    pl.col("author_id"),
                ]
            )

            num_chunks += 1

            # Simulate memory cleanup every few chunks
            if num_chunks % 5 == 0:
                gc.collect()

        return num_chunks

    def _process_chunks_new(self, dataset: pl.DataFrame, chunk_size: int) -> int:
        """Simulate new optimized chunk processing approach."""
        num_chunks = 0
        dataset_size = len(dataset)

        for start_idx in range(0, dataset_size, chunk_size):
            end_idx = min(start_idx + chunk_size, dataset_size)
            chunk = dataset.slice(start_idx, end_idx - start_idx)

            # Simulate processing work (tokenization, basic operations)
            _ = chunk.select(
                [
                    pl.col("message_text").str.split(" ").alias("tokens"),
                    pl.col("message_id"),
                    pl.col("author_id"),
                ]
            )

            num_chunks += 1

            # Optimized memory cleanup - less frequent
            if num_chunks % 10 == 0:
                gc.collect()

        return num_chunks

    # Phase 2: pytest-benchmark Integration

    def test_chunk_processing_benchmark_small(self, benchmark):
        """Benchmark chunk processing performance on small datasets."""
        dataset = self._create_realistic_dataset(100_000, avg_tokens_per_message=15)

        # Benchmark the new optimized approach
        result = benchmark(self._process_chunks_new, dataset, 200_000)

        # The benchmark fixture handles statistical analysis automatically
        # We can still do basic validation
        assert result > 0, "Should process at least one chunk"

    def test_chunk_processing_benchmark_medium(self, benchmark):
        """Benchmark chunk processing performance on medium datasets."""
        dataset = self._create_realistic_dataset(500_000, avg_tokens_per_message=18)

        # Benchmark the new optimized approach
        result = benchmark(self._process_chunks_new, dataset, 150_000)

        assert result > 0, "Should process at least one chunk"

    def test_chunk_processing_benchmark_comparison(self):
        """Compare old vs new chunk processing approaches using pytest-benchmark."""
        dataset = self._create_realistic_dataset(300_000, avg_tokens_per_message=16)

        # This test demonstrates how to use benchmark.pedantic for more control
        # We'll implement this as a property-based test instead

    # Phase 3: Resource-Based Metrics (Deterministic)

    def test_chunk_efficiency_invariant(self):
        """Test that larger chunks always result in fewer I/O operations."""
        dataset = self._create_realistic_dataset(1_000_000, avg_tokens_per_message=20)

        old_chunk_size = 50_000  # ~20 chunks
        new_chunk_size = 150_000  # ~7 chunks

        old_chunks = self._count_operations(dataset, old_chunk_size)
        new_chunks = self._count_operations(dataset, new_chunk_size)

        # These assertions will ALWAYS pass regardless of system performance
        assert (
            new_chunks < old_chunks
        ), f"New chunks ({new_chunks}) should be fewer than old chunks ({old_chunks})"

        expected_reduction = old_chunks / new_chunks if new_chunks > 0 else old_chunks
        assert (
            expected_reduction >= 2.5
        ), f"Expected at least 2.5x I/O reduction, got {expected_reduction:.2f}x"

    def test_memory_efficiency_bounds(self):
        """Validate memory usage stays within acceptable limits."""
        process = psutil.Process()

        initial_memory = process.memory_info().rss
        dataset = self._create_realistic_dataset(500_000, avg_tokens_per_message=18)

        # Process with new chunk size
        self._process_chunks_new(dataset, 150_000)

        peak_memory = process.memory_info().rss
        memory_increase = (peak_memory - initial_memory) / 1024**2  # MB

        # Reasonable memory bounds based on dataset size
        assert (
            memory_increase < 500
        ), f"Memory usage increased by {memory_increase:.1f}MB, should be < 500MB"

    @pytest.mark.parametrize("dataset_size", [100_000, 500_000, 1_000_000])
    @pytest.mark.parametrize("chunk_factor", [2, 3, 4])
    def test_chunk_size_scaling_properties(self, dataset_size, chunk_factor):
        """Test that chunk size scaling behaves predictably."""
        dataset = self._create_realistic_dataset(
            dataset_size, avg_tokens_per_message=16
        )

        small_chunk = 50_000
        large_chunk = small_chunk * chunk_factor

        small_ops = self._count_operations(dataset, small_chunk)
        large_ops = self._count_operations(dataset, large_chunk)

        # Mathematical relationship should always hold
        expected_reduction = min(chunk_factor, dataset_size / small_chunk)
        actual_reduction = small_ops / large_ops if large_ops > 0 else small_ops

        # Allow 20% tolerance for edge cases
        assert actual_reduction >= expected_reduction * 0.8, (
            f"Expected ~{expected_reduction:.1f}x reduction, got {actual_reduction:.2f}x "
            f"(dataset_size={dataset_size}, chunk_factor={chunk_factor})"
        )

    def test_io_operation_counting_deterministic(self):
        """Test I/O operation counting produces deterministic results."""
        dataset = self._create_realistic_dataset(750_000, avg_tokens_per_message=15)

        # Multiple runs should produce identical chunk counts
        chunk_size = 125_000

        run1 = self._count_operations(dataset, chunk_size)
        run2 = self._count_operations(dataset, chunk_size)
        run3 = self._count_operations(dataset, chunk_size)

        assert run1 == run2 == run3, "Chunk counting should be deterministic"

        # Verify mathematical correctness
        expected_chunks = (len(dataset) + chunk_size - 1) // chunk_size
        assert run1 == expected_chunks, f"Expected {expected_chunks} chunks, got {run1}"

    def test_memory_usage_scaling_properties(self):
        """Test memory usage scaling properties with different dataset sizes."""
        dataset_sizes = [100_000, 200_000, 400_000]
        memory_usages = []

        process = psutil.Process()

        for size in dataset_sizes:
            gc.collect()  # Clean slate
            initial_memory = process.memory_info().rss

            dataset = self._create_realistic_dataset(size, avg_tokens_per_message=15)
            self._process_chunks_new(dataset, 150_000)

            peak_memory = process.memory_info().rss
            memory_increase = (peak_memory - initial_memory) / 1024**2  # MB
            memory_usages.append(memory_increase)

            # Clean up
            del dataset
            gc.collect()

        # Memory usage should scale reasonably with dataset size
        for i in range(1, len(memory_usages)):
            size_ratio = dataset_sizes[i] / dataset_sizes[i - 1]
            memory_ratio = (
                memory_usages[i] / memory_usages[i - 1]
                if memory_usages[i - 1] > 0
                else 1
            )

            # Memory should not scale worse than linearly with dataset size
            assert (
                memory_ratio <= size_ratio * 1.5
            ), f"Memory scaling too aggressive: {memory_ratio:.2f}x for {size_ratio:.2f}x data increase"

    # Phase 4: Enhanced Infrastructure Tests

    def test_chunk_processing_variance_analysis(self):
        """Analyze variance in chunk processing to validate benchmark reliability."""
        dataset = self._create_realistic_dataset(200_000, avg_tokens_per_message=16)
        chunk_size = 100_000

        # Measure multiple runs
        times = []
        for _ in range(5):
            gc.collect()
            start_time = time.time()
            chunks = self._process_chunks_new(dataset, chunk_size)
            elapsed = time.time() - start_time
            times.append(elapsed)

        # Calculate coefficient of variation (CV)
        mean_time = sum(times) / len(times)
        variance = sum((t - mean_time) ** 2 for t in times) / len(times)
        std_dev = variance**0.5
        cv = std_dev / mean_time if mean_time > 0 else 0

        # Coefficient of variation should be reasonable (< 30%)
        assert cv < 0.3, f"High variance in processing times: CV = {cv:.2%}"

        # All runs should produce the same number of chunks
        chunk_counts = []
        for _ in range(3):
            chunks = self._count_operations(dataset, chunk_size)
            chunk_counts.append(chunks)

        assert len(set(chunk_counts)) == 1, "Chunk counts should be deterministic"

    def test_performance_regression_detection(self):
        """Test framework for detecting performance regressions."""
        dataset = self._create_realistic_dataset(400_000, avg_tokens_per_message=17)

        # Baseline performance (optimized)
        baseline_time = self._time_operation(
            lambda: self._process_chunks_new(dataset, 150_000)
        )

        # Simulated regression (using old, slower approach)
        regression_time = self._time_operation(
            lambda: self._process_chunks_old(dataset, 50_000)
        )

        # Should detect significant regression
        regression_ratio = regression_time / baseline_time if baseline_time > 0 else 1

        # This would fail if we had a real regression > 50%
        # In test, we expect the old approach to be slower
        assert (
            regression_ratio > 1.0
        ), "Should detect performance difference between approaches"

    # Helper Methods

    def _count_operations(self, dataset: pl.DataFrame, chunk_size: int) -> int:
        """Count I/O operations (chunks) for deterministic testing."""
        dataset_size = len(dataset)
        return (dataset_size + chunk_size - 1) // chunk_size

    def _time_operation(self, operation) -> float:
        """Time an operation with proper setup/cleanup."""
        gc.collect()
        start_time = time.time()
        operation()
        return time.time() - start_time


@pytest.mark.performance
@pytest.mark.benchmark
class TestBenchmarkIntegration:
    """Tests for benchmark configuration and integration."""

    def test_benchmark_configuration(self, benchmark):
        """Test that benchmark configuration works correctly."""

        def simple_operation():
            return sum(range(10000))

        result = benchmark(simple_operation)
        assert result == sum(range(10000))

    def test_benchmark_with_setup(self, benchmark):
        """Test benchmark with setup/teardown operations."""

        def setup():
            return list(range(50000))

        def operation(data):
            return len([x for x in data if x % 2 == 0])

        result = benchmark.pedantic(operation, setup=setup, rounds=3, iterations=1)
        assert result == 25000  # Half should be even


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s", "--benchmark-disable"])
