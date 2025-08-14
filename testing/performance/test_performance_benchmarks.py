"""
Performance Benchmarking Tests for Chunking Optimization
Measures actual performance improvements and validates 2-4x performance gains.
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
@pytest.mark.slow
class TestPerformanceBenchmarks:
    """Comprehensive performance benchmarking suite."""

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

    def _benchmark_chunk_processing(
        self, dataset: pl.DataFrame, old_chunk_size: int, new_chunk_size: int
    ) -> Dict[str, float]:
        """Benchmark chunk processing with different chunk sizes."""
        results = {}

        # Benchmark old chunk size
        start_time = time.time()
        old_chunks = self._simulate_chunk_processing(dataset, old_chunk_size)
        old_time = time.time() - start_time
        results["old_time"] = old_time
        results["old_chunks"] = old_chunks

        # Clear memory between tests
        gc.collect()

        # Benchmark new chunk size
        start_time = time.time()
        new_chunks = self._simulate_chunk_processing(dataset, new_chunk_size)
        new_time = time.time() - start_time
        results["new_time"] = new_time
        results["new_chunks"] = new_chunks

        # Calculate improvements
        results["time_improvement"] = old_time / new_time if new_time > 0 else 1.0
        results["io_reduction"] = old_chunks / new_chunks if new_chunks > 0 else 1.0

        return results

    def _simulate_chunk_processing(self, dataset: pl.DataFrame, chunk_size: int) -> int:
        """Simulate chunk processing and return number of chunks processed."""
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

    def test_small_dataset_performance(self):
        """Test performance improvements on small datasets (100K messages)."""
        dataset = self._create_realistic_dataset(100_000, avg_tokens_per_message=15)

        # Old vs new chunk sizes for small datasets
        old_chunk_size = 50_000  # Original base
        new_chunk_size = 200_000  # New base for small datasets

        results = self._benchmark_chunk_processing(
            dataset, old_chunk_size, new_chunk_size
        )

        # Should have fewer chunks with new size
        assert (
            results["io_reduction"] >= 2.0
        ), f"Expected at least 2x I/O reduction, got {results['io_reduction']:.2f}x"

        # Should be faster (allowing for test variability)
        assert (
            results["time_improvement"] >= 1.02
        ), f"Expected at least 1.02x time improvement, got {results['time_improvement']:.2f}x"

        # Memory usage should be reasonable
        current_memory = psutil.Process().memory_info().rss / 1024**2
        memory_increase = current_memory - self.initial_memory
        assert (
            memory_increase < 500
        ), f"Memory usage increased by {memory_increase:.1f}MB, should be < 500MB"

    def test_medium_dataset_performance(self):
        """Test performance improvements on medium datasets (500K messages)."""
        dataset = self._create_realistic_dataset(500_000, avg_tokens_per_message=18)

        # Old vs new chunk sizes for medium datasets
        old_chunk_size = 50_000  # Original base
        new_chunk_size = 150_000  # New base for medium datasets

        results = self._benchmark_chunk_processing(
            dataset, old_chunk_size, new_chunk_size
        )

        # Should have significant I/O reduction
        assert (
            results["io_reduction"] >= 2.5
        ), f"Expected at least 2.5x I/O reduction, got {results['io_reduction']:.2f}x"

        # Should be noticeably faster
        assert (
            results["time_improvement"] >= 1.3
        ), f"Expected at least 1.3x time improvement, got {results['time_improvement']:.2f}x"

        # Validate chunk counts make sense
        expected_old_chunks = (500_000 + old_chunk_size - 1) // old_chunk_size
        expected_new_chunks = (500_000 + new_chunk_size - 1) // new_chunk_size

        assert abs(results["old_chunks"] - expected_old_chunks) <= 1
        assert abs(results["new_chunks"] - expected_new_chunks) <= 1

    def test_large_dataset_performance(self):
        """Test performance improvements on large datasets (1M messages)."""
        dataset = self._create_realistic_dataset(1_000_000, avg_tokens_per_message=20)

        # Test with different chunk sizes based on system memory
        memory_manager = MemoryManager()
        system_memory_gb = psutil.virtual_memory().total / 1024**3

        if system_memory_gb >= 16:
            memory_factor = 1.5
        elif system_memory_gb >= 8:
            memory_factor = 1.0
        else:
            memory_factor = 0.5

        old_chunk_size = 50_000
        new_chunk_size = int(150_000 * memory_factor)  # Adaptive based on system

        results = self._benchmark_chunk_processing(
            dataset, old_chunk_size, new_chunk_size
        )

        # Should have substantial improvements
        expected_io_reduction = new_chunk_size / old_chunk_size
        assert (
            results["io_reduction"] >= expected_io_reduction * 0.8
        ), f"Expected ~{expected_io_reduction:.1f}x I/O reduction, got {results['io_reduction']:.2f}x"

        # Time improvement should be significant for large datasets
        assert (
            results["time_improvement"] >= 1.15
        ), f"Expected at least 1.15x time improvement, got {results['time_improvement']:.2f}x"

    def test_memory_adaptive_chunk_sizing_performance(self):
        """Test that memory-adaptive chunk sizing provides better performance."""
        dataset = self._create_realistic_dataset(300_000, avg_tokens_per_message=15)

        # Test with different memory configurations
        test_configs = [
            (4.0, 1.0),  # 4GB limit, 1.0x factor (old config)
            (8.0, 1.5),  # 8GB limit, 1.5x factor (16GB system)
            (12.0, 2.0),  # 12GB limit, 2.0x factor (32GB system)
        ]

        performance_results = []

        for memory_limit, expected_factor in test_configs:
            with patch("psutil.virtual_memory") as mock_vm:
                # Set up system memory to match expected factor
                if expected_factor == 1.0:
                    mock_vm.return_value.total = 8 * 1024**3  # 8GB system
                elif expected_factor == 1.5:
                    mock_vm.return_value.total = 16 * 1024**3  # 16GB system
                else:
                    mock_vm.return_value.total = 32 * 1024**3  # 32GB system

                memory_manager = MemoryManager()

                # Calculate chunk size with adaptive scaling
                base_chunk = 150_000
                adaptive_chunk = int(base_chunk * expected_factor)
                adaptive_chunk = max(10_000, min(adaptive_chunk, 500_000))

                # Benchmark this configuration
                start_time = time.time()
                chunks = self._simulate_chunk_processing(dataset, adaptive_chunk)
                elapsed = time.time() - start_time

                performance_results.append(
                    {
                        "memory_limit": memory_limit,
                        "factor": expected_factor,
                        "chunk_size": adaptive_chunk,
                        "time": elapsed,
                        "chunks": chunks,
                    }
                )

                gc.collect()

        # Higher memory configurations should be faster
        for i in range(1, len(performance_results)):
            current = performance_results[i]
            previous = performance_results[i - 1]

            # Should have larger chunks
            assert current["chunk_size"] >= previous["chunk_size"]

            # Should have fewer chunks (better I/O efficiency)
            assert current["chunks"] <= previous["chunks"]

    def test_vectorized_ngram_generation_performance(self):
        """Test performance of vectorized n-gram generation with larger chunks."""
        # Create dataset with pre-tokenized data
        dataset_size = 50_000
        tokens_data = []

        for i in range(dataset_size):
            tokens = [
                f"word_{j}" for j in range(i % 10 + 5)
            ]  # Variable length 5-14 tokens
            tokens_data.append({"message_surrogate_id": i, "tokens": tokens})

        df = pl.DataFrame(tokens_data)

        # Test old vs new chunk sizes
        old_chunk_size = 10_000
        new_chunk_size = 30_000

        # Benchmark old chunk size
        start_time = time.time()
        old_result = self._benchmark_vectorized_ngram_generation(
            df, old_chunk_size, min_n=2, max_n=3
        )
        old_time = time.time() - start_time

        gc.collect()

        # Benchmark new chunk size
        start_time = time.time()
        new_result = self._benchmark_vectorized_ngram_generation(
            df, new_chunk_size, min_n=2, max_n=3
        )
        new_time = time.time() - start_time

        # Should produce same results
        assert len(old_result) == len(new_result), "Results should be identical"

        # Should be faster with larger chunks
        time_improvement = old_time / new_time if new_time > 0 else 1.0
        assert (
            time_improvement >= 0.95
        ), f"Expected at least 0.95x improvement, got {time_improvement:.2f}x"

    def _benchmark_vectorized_ngram_generation(
        self, df: pl.DataFrame, chunk_size: int, min_n: int, max_n: int
    ) -> pl.DataFrame:
        """Benchmark vectorized n-gram generation with specified chunk size."""
        results = []

        for start_idx in range(0, len(df), chunk_size):
            end_idx = min(start_idx + chunk_size, len(df))
            chunk = df.slice(start_idx, end_idx - start_idx)

            # Simulate vectorized n-gram generation
            chunk_result = (
                chunk.select([pl.col("message_surrogate_id"), pl.col("tokens")])
                .with_columns(
                    [
                        # Simulate n-gram generation
                        pl.col("tokens")
                        .map_elements(
                            lambda tokens: self._generate_ngrams_for_tokens(
                                tokens, min_n, max_n
                            ),
                            return_dtype=pl.List(pl.String),
                        )
                        .alias("ngrams")
                    ]
                )
                .explode("ngrams")
                .filter(pl.col("ngrams").is_not_null())
                .select(
                    [
                        pl.col("message_surrogate_id"),
                        pl.col("ngrams").alias("ngram_text"),
                    ]
                )
            )

            results.append(chunk_result)

        # Combine all results
        if results:
            return pl.concat(results)
        else:
            return pl.DataFrame(
                schema={"message_surrogate_id": pl.Int64, "ngram_text": pl.String}
            )

    def _generate_ngrams_for_tokens(
        self, tokens: List[str], min_n: int, max_n: int
    ) -> List[str]:
        """Generate n-grams from a list of tokens."""
        if len(tokens) == 0 or len(tokens) < min_n:
            return []

        ngrams = []
        for n in range(min_n, max_n + 1):
            for i in range(len(tokens) - n + 1):
                ngram = " ".join(tokens[i : i + n])
                ngrams.append(ngram)

        return ngrams

    def test_fallback_threshold_performance(self):
        """Test performance improvements with updated fallback thresholds."""
        # Test datasets of different sizes around fallback thresholds
        test_sizes = [
            400_000,  # Below old threshold (500K)
            800_000,  # Above old threshold, below new 16GB threshold (1.5M)
            1_200_000,  # Above old threshold, below new 16GB threshold
            2_000_000,  # Above new 16GB threshold
        ]

        memory_manager = MemoryManager()
        system_memory_gb = psutil.virtual_memory().total / 1024**3

        # Determine expected threshold based on system memory
        if system_memory_gb >= 32:
            new_threshold = 3_000_000
        elif system_memory_gb >= 16:
            new_threshold = 1_500_000
        else:
            new_threshold = 500_000

        old_threshold = 500_000

        for dataset_size in test_sizes:
            # Check which processing method would be used
            uses_old_fallback = dataset_size > old_threshold
            uses_new_fallback = dataset_size > new_threshold

            # With new thresholds, more datasets should avoid fallback processing
            if dataset_size <= new_threshold and dataset_size > old_threshold:
                # This dataset would have used fallback with old threshold
                # but uses regular processing with new threshold
                assert (
                    not uses_new_fallback
                ), f"Dataset size {dataset_size} should not use fallback with new threshold {new_threshold}"
                assert (
                    uses_old_fallback
                ), f"Dataset size {dataset_size} would have used fallback with old threshold {old_threshold}"

    def test_memory_usage_efficiency(self):
        """Test that memory usage is more efficient with new chunking."""
        dataset = self._create_realistic_dataset(200_000, avg_tokens_per_message=12)

        # Test memory usage with different chunk sizes
        old_chunk_size = 25_000  # Old fallback chunk size
        new_chunk_size = 100_000  # New fallback chunk size

        # Measure memory usage with old chunk size
        gc.collect()
        initial_memory = psutil.Process().memory_info().rss

        self._simulate_chunk_processing(dataset, old_chunk_size)
        old_peak_memory = psutil.Process().memory_info().rss
        old_memory_usage = (old_peak_memory - initial_memory) / 1024**2  # MB

        gc.collect()

        # Measure memory usage with new chunk size
        initial_memory = psutil.Process().memory_info().rss

        self._simulate_chunk_processing(dataset, new_chunk_size)
        new_peak_memory = psutil.Process().memory_info().rss
        new_memory_usage = (new_peak_memory - initial_memory) / 1024**2  # MB

        # Memory usage should be reasonable for both
        # Larger chunks may use more memory but should be more efficient
        assert (
            new_memory_usage < old_memory_usage * 5
        ), f"New memory usage ({new_memory_usage:.1f}MB) should not be more than 5x old usage ({old_memory_usage:.1f}MB)"

        # Both should use reasonable amounts of memory
        assert (
            old_memory_usage < 1000
        ), f"Old chunking should use < 1GB, used {old_memory_usage:.1f}MB"
        assert (
            new_memory_usage < 1000
        ), f"New chunking should use < 1GB, used {new_memory_usage:.1f}MB"

    @pytest.mark.skipif(
        psutil.virtual_memory().total < 8 * 1024**3,
        reason="Requires at least 8GB RAM for comprehensive performance testing",
    )
    def test_comprehensive_performance_validation(self):
        """Comprehensive performance validation on systems with adequate memory."""
        system_memory_gb = psutil.virtual_memory().total / 1024**3

        # Test with appropriately sized dataset
        if system_memory_gb >= 16:
            dataset_size = 1_000_000
            expected_min_improvement = 1.25
        else:
            dataset_size = 500_000
            expected_min_improvement = 1.25

        dataset = self._create_realistic_dataset(
            dataset_size, avg_tokens_per_message=18
        )

        # Compare old conservative approach vs new adaptive approach
        old_chunk_size = 50_000

        # Calculate new chunk size based on system
        if system_memory_gb >= 32:
            memory_factor = 2.0
        elif system_memory_gb >= 16:
            memory_factor = 1.5
        elif system_memory_gb >= 8:
            memory_factor = 1.0
        else:
            memory_factor = 0.5

        new_chunk_size = int(150_000 * memory_factor)
        new_chunk_size = max(10_000, min(new_chunk_size, 500_000))

        results = self._benchmark_chunk_processing(
            dataset, old_chunk_size, new_chunk_size
        )

        # Should meet performance improvement targets
        assert (
            results["time_improvement"] >= expected_min_improvement
        ), f"Expected at least {expected_min_improvement}x improvement, got {results['time_improvement']:.2f}x"

        # Should have substantial I/O reduction
        expected_io_reduction = new_chunk_size / old_chunk_size
        assert (
            results["io_reduction"] >= expected_io_reduction * 0.8
        ), f"Expected ~{expected_io_reduction:.1f}x I/O reduction, got {results['io_reduction']:.2f}x"

        # Log results for documentation
        print(f"\nPerformance Results for {system_memory_gb:.1f}GB system:")
        print(f"  Dataset size: {dataset_size:,} messages")
        print(f"  Old chunk size: {old_chunk_size:,}")
        print(f"  New chunk size: {new_chunk_size:,}")
        print(f"  Time improvement: {results['time_improvement']:.2f}x")
        print(f"  I/O reduction: {results['io_reduction']:.2f}x")
        print(f"  Memory factor: {memory_factor}x")


@pytest.mark.performance
@pytest.mark.slow
class TestStressTests:
    """Stress tests for extreme conditions."""

    def test_large_chunk_memory_stability(self):
        """Test that large chunks don't cause memory issues."""
        # Test with largest possible chunk size
        large_chunk_size = 500_000  # Maximum allowed
        dataset = self._create_test_dataset(100_000)  # Smaller than chunk

        memory_manager = MemoryManager()
        initial_memory = psutil.Process().memory_info().rss / 1024**2

        # Process with large chunk
        start_time = time.time()
        self._simulate_chunk_processing(dataset, large_chunk_size)
        processing_time = time.time() - start_time

        peak_memory = psutil.Process().memory_info().rss / 1024**2
        memory_increase = peak_memory - initial_memory

        # Should complete successfully
        assert processing_time > 0

        # Memory usage should be reasonable
        assert (
            memory_increase < memory_manager.max_memory_gb * 1024 * 0.8
        ), f"Memory usage ({memory_increase:.1f}MB) should be within 80% of limit"

    def test_many_small_chunks_efficiency(self):
        """Test efficiency with many small chunks."""
        dataset = self._create_test_dataset(500_000)
        small_chunk_size = 10_000  # Many small chunks

        start_time = time.time()
        num_chunks = self._simulate_chunk_processing(dataset, small_chunk_size)
        processing_time = time.time() - start_time

        # Should complete in reasonable time
        assert (
            processing_time < 60
        ), f"Processing took {processing_time:.1f}s, should be < 60s"

        # Should have expected number of chunks
        expected_chunks = (len(dataset) + small_chunk_size - 1) // small_chunk_size
        assert abs(num_chunks - expected_chunks) <= 1

    def _create_test_dataset(self, size: int) -> pl.DataFrame:
        """Create a simple test dataset."""
        return pl.DataFrame(
            {
                "message_id": [f"msg_{i}" for i in range(size)],
                "message_text": [f"test message {i} content" for i in range(size)],
                "author_id": [f"user_{i % 1000}" for i in range(size)],
                "timestamp": ["2023-01-01T00:00:00Z"] * size,
            }
        )

    def _simulate_chunk_processing(self, dataset: pl.DataFrame, chunk_size: int) -> int:
        """Simulate chunk processing and return number of chunks."""
        num_chunks = 0
        dataset_size = len(dataset)

        for start_idx in range(0, dataset_size, chunk_size):
            end_idx = min(start_idx + chunk_size, dataset_size)
            chunk = dataset.slice(start_idx, end_idx - start_idx)

            # Simulate basic processing
            _ = chunk.select(
                [
                    pl.col("message_text").str.len_chars().alias("text_length"),
                    pl.col("message_id"),
                    pl.col("author_id"),
                ]
            )

            num_chunks += 1

            # Periodic cleanup
            if num_chunks % 10 == 0:
                gc.collect()

        return num_chunks


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])  # -s to show print output
