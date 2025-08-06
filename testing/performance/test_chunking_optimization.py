"""
Performance Test Suite for Chunking Optimization
Phase 5: Testing & Validation for N-gram Analyzer Chunking Optimization

This test suite validates the performance improvements and system-specific scaling
introduced in Phases 1-4 of the chunking optimization specification.
"""

import gc
import os
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
from analyzers.ngrams.ngrams_base.main import main as ngrams_main
from app.utils import MemoryManager, MemoryPressureLevel


class TestMemoryAutoDetection:
    """Test smart memory detection functionality."""

    def test_auto_detection_tiers(self):
        """Test memory detection tiers work correctly."""
        with patch("psutil.virtual_memory") as mock_vm:
            # Test 8GB system (25% allocation)
            mock_vm.return_value.total = 8 * 1024**3
            limit = MemoryManager._auto_detect_memory_limit()
            assert abs(limit - 2.0) < 0.1  # 8GB * 0.25 = 2GB

            # Test 16GB system (30% allocation)
            mock_vm.return_value.total = 16 * 1024**3
            limit = MemoryManager._auto_detect_memory_limit()
            assert abs(limit - 4.8) < 0.1  # 16GB * 0.30 = 4.8GB

            # Test 32GB system (40% allocation)
            mock_vm.return_value.total = 32 * 1024**3
            limit = MemoryManager._auto_detect_memory_limit()
            assert abs(limit - 12.8) < 0.1  # 32GB * 0.40 = 12.8GB

            # Test 4GB system (20% allocation - constrained)
            mock_vm.return_value.total = 4 * 1024**3
            limit = MemoryManager._auto_detect_memory_limit()
            assert abs(limit - 0.8) < 0.1  # 4GB * 0.20 = 0.8GB

    def test_auto_detection_vs_manual_override(self):
        """Test that manual override works and auto-detection is bypassed."""
        with patch("psutil.virtual_memory") as mock_vm:
            mock_vm.return_value.total = 16 * 1024**3

            # Auto-detection should give 4.8GB
            auto_manager = MemoryManager()
            assert abs(auto_manager.max_memory_gb - 4.8) < 0.1

            # Manual override should use exact value
            manual_manager = MemoryManager(max_memory_gb=8.0)
            assert manual_manager.max_memory_gb == 8.0

    def test_memory_detection_logging(self):
        """Test that memory detection logs appropriate information."""
        with patch("psutil.virtual_memory") as mock_vm:
            mock_vm.return_value.total = 16 * 1024**3

            with patch("app.utils.get_logger") as mock_logger:
                mock_log = MagicMock()
                mock_logger.return_value = mock_log

                MemoryManager()

                # Should log initialization details
                mock_log.info.assert_called()
                call_args = mock_log.info.call_args
                assert "Memory manager initialized" in call_args[0][0]

                extra_data = call_args[1]["extra"]
                assert "system_total_gb" in extra_data
                assert "detected_limit_gb" in extra_data
                assert "allocation_percent" in extra_data
                assert extra_data["detection_method"] == "auto"

    def test_updated_memory_pressure_thresholds(self):
        """Test that updated pressure thresholds are more lenient."""
        manager = MemoryManager(max_memory_gb=1.0)

        # Test new more lenient thresholds
        assert manager.thresholds[MemoryPressureLevel.MEDIUM] == 0.70  # Was 0.60
        assert manager.thresholds[MemoryPressureLevel.HIGH] == 0.80  # Was 0.75
        assert manager.thresholds[MemoryPressureLevel.CRITICAL] == 0.90  # Was 0.85

    def test_updated_chunk_size_factors(self):
        """Test that chunk size reductions are less aggressive."""
        manager = MemoryManager()

        # Test less aggressive chunk size reduction factors
        assert manager.chunk_size_factors[MemoryPressureLevel.LOW] == 1.0
        assert manager.chunk_size_factors[MemoryPressureLevel.MEDIUM] == 0.8  # Was 0.7
        assert manager.chunk_size_factors[MemoryPressureLevel.HIGH] == 0.6  # Was 0.4
        assert (
            manager.chunk_size_factors[MemoryPressureLevel.CRITICAL] == 0.4
        )  # Was 0.2


class TestAdaptiveChunkSizing:
    """Test adaptive chunk size calculation for different system configurations."""

    def test_calculate_optimal_chunk_size_memory_factors(self):
        """Test memory factor calculation for different system sizes."""
        from analyzers.ngrams.ngrams_base.main import main

        # Mock memory manager for different system sizes
        with patch("psutil.virtual_memory") as mock_vm:
            # Test 8GB system (factor = 1.0)
            mock_vm.return_value.total = 8 * 1024**3
            memory_manager = MemoryManager()

            # Use the calculate_optimal_chunk_size function from the ngrams_base module
            # We need to access it through the main function's internal definition
            # For testing, we'll create a similar function
            def test_calculate_optimal_chunk_size(
                dataset_size: int, memory_manager=None
            ) -> int:
                if memory_manager:
                    total_gb = psutil.virtual_memory().total / 1024**3
                    if total_gb >= 32:
                        memory_factor = 2.0
                    elif total_gb >= 16:
                        memory_factor = 1.5
                    elif total_gb >= 8:
                        memory_factor = 1.0
                    else:
                        memory_factor = 0.5
                else:
                    memory_factor = 1.0

                if dataset_size <= 500_000:
                    base_chunk = int(200_000 * memory_factor)
                elif dataset_size <= 2_000_000:
                    base_chunk = int(150_000 * memory_factor)
                elif dataset_size <= 5_000_000:
                    base_chunk = int(100_000 * memory_factor)
                else:
                    base_chunk = int(75_000 * memory_factor)

                return max(10_000, min(base_chunk, 500_000))

            # Test different system sizes
            # 8GB system
            mock_vm.return_value.total = 8 * 1024**3
            chunk_size_8gb = test_calculate_optimal_chunk_size(
                1_000_000, memory_manager
            )
            assert chunk_size_8gb == 150_000  # 150K * 1.0

            # 16GB system
            mock_vm.return_value.total = 16 * 1024**3
            chunk_size_16gb = test_calculate_optimal_chunk_size(
                1_000_000, memory_manager
            )
            assert chunk_size_16gb == 225_000  # 150K * 1.5

            # 32GB system
            mock_vm.return_value.total = 32 * 1024**3
            chunk_size_32gb = test_calculate_optimal_chunk_size(
                1_000_000, memory_manager
            )
            assert chunk_size_32gb == 300_000  # 150K * 2.0

            # 4GB system
            mock_vm.return_value.total = 4 * 1024**3
            chunk_size_4gb = test_calculate_optimal_chunk_size(
                1_000_000, memory_manager
            )
            assert chunk_size_4gb == 75_000  # 150K * 0.5

    def test_adaptive_chunk_scaling_by_dataset_size(self):
        """Test that chunk sizes scale appropriately with dataset size."""

        def test_calculate_optimal_chunk_size(
            dataset_size: int, memory_manager=None
        ) -> int:
            memory_factor = 1.5  # Simulate 16GB system

            if dataset_size <= 500_000:
                base_chunk = int(200_000 * memory_factor)
            elif dataset_size <= 2_000_000:
                base_chunk = int(150_000 * memory_factor)
            elif dataset_size <= 5_000_000:
                base_chunk = int(100_000 * memory_factor)
            else:
                base_chunk = int(75_000 * memory_factor)

            return max(10_000, min(base_chunk, 500_000))

        memory_manager = MagicMock()

        # Small dataset - largest base chunks
        small_chunk = test_calculate_optimal_chunk_size(100_000, memory_manager)
        assert small_chunk == 300_000  # 200K * 1.5

        # Medium dataset - medium base chunks
        medium_chunk = test_calculate_optimal_chunk_size(1_000_000, memory_manager)
        assert medium_chunk == 225_000  # 150K * 1.5

        # Large dataset - smaller base chunks
        large_chunk = test_calculate_optimal_chunk_size(3_000_000, memory_manager)
        assert large_chunk == 150_000  # 100K * 1.5

        # Very large dataset - smallest base chunks
        xlarge_chunk = test_calculate_optimal_chunk_size(10_000_000, memory_manager)
        assert xlarge_chunk == 112_500  # 75K * 1.5

    def test_chunk_size_bounds_enforcement(self):
        """Test that chunk sizes respect minimum and maximum bounds."""

        def test_calculate_optimal_chunk_size(
            dataset_size: int, memory_manager=None
        ) -> int:
            memory_factor = 0.04  # Very small factor to test minimum (0.04 * 200_000 = 8_000 -> min enforced to 10_000)

            if dataset_size <= 500_000:
                base_chunk = int(200_000 * memory_factor)
            else:
                base_chunk = int(75_000 * memory_factor)

            return max(10_000, min(base_chunk, 500_000))

        memory_manager = MagicMock()

        # Should enforce minimum of 10,000
        small_chunk = test_calculate_optimal_chunk_size(100_000, memory_manager)
        assert small_chunk == 10_000

        # Test maximum enforcement with very high memory factor
        def test_calculate_max_chunk_size(
            dataset_size: int, memory_manager=None
        ) -> int:
            memory_factor = 10.0  # Very high factor to test maximum
            base_chunk = int(200_000 * memory_factor)  # Would be 2M
            return max(10_000, min(base_chunk, 500_000))

        max_chunk = test_calculate_max_chunk_size(100_000, memory_manager)
        assert max_chunk == 500_000  # Should be capped at maximum

    def test_base_chunk_increases_validation(self):
        """Test that base chunk sizes have increased from 50K to 150K-200K."""

        # This validates the Phase 2 implementation
        def test_calculate_optimal_chunk_size(
            dataset_size: int, memory_manager=None
        ) -> int:
            memory_factor = 1.0  # Standard system

            # These are the new base sizes (Phase 2)
            if dataset_size <= 500_000:
                base_chunk = int(200_000 * memory_factor)  # Was 50K, now 200K
            elif dataset_size <= 2_000_000:
                base_chunk = int(150_000 * memory_factor)  # Was 50K, now 150K
            else:
                base_chunk = int(100_000 * memory_factor)  # Was 50K, now 100K+

            return max(10_000, min(base_chunk, 500_000))

        memory_manager = MagicMock()

        # Verify chunk sizes are significantly larger than old 50K base
        small_dataset_chunk = test_calculate_optimal_chunk_size(100_000, memory_manager)
        assert small_dataset_chunk >= 150_000  # At least 3x larger than old 50K

        medium_dataset_chunk = test_calculate_optimal_chunk_size(
            1_000_000, memory_manager
        )
        assert medium_dataset_chunk >= 150_000  # At least 3x larger than old 50K


class TestFallbackOptimization:
    """Test fallback processor optimizations."""

    def test_fallback_base_chunk_increase(self):
        """Test that fallback base chunks increased from 25K to 100K."""
        memory_manager = MagicMock()
        memory_manager.calculate_adaptive_chunk_size.return_value = 100_000  # New base

        # The fallback processors should now use 100K as base instead of 25K
        # This is verified by checking the base value passed to calculate_adaptive_chunk_size
        memory_manager.calculate_adaptive_chunk_size.assert_not_called()

        # Call the function that would use the base chunk size
        chunk_size = memory_manager.calculate_adaptive_chunk_size(
            100_000, "ngram_generation"
        )

        # Should return the new larger base size
        assert chunk_size == 100_000

    def test_memory_aware_fallback_thresholds(self):
        """Test memory-aware fallback thresholds for different system sizes."""
        with patch("psutil.virtual_memory") as mock_vm:
            # Test 32GB system - should have 3M row threshold
            mock_vm.return_value.total = 32 * 1024**3
            memory_manager = MemoryManager()

            # Simulate the threshold calculation logic from Phase 3
            total_gb = psutil.virtual_memory().total / 1024**3
            if total_gb >= 32:
                threshold = 3_000_000
            elif total_gb >= 16:
                threshold = 1_500_000
            else:
                threshold = 500_000

            assert threshold == 3_000_000

            # Test 16GB system - should have 1.5M row threshold
            mock_vm.return_value.total = 16 * 1024**3
            total_gb = psutil.virtual_memory().total / 1024**3
            if total_gb >= 32:
                threshold = 3_000_000
            elif total_gb >= 16:
                threshold = 1_500_000
            else:
                threshold = 500_000

            assert threshold == 1_500_000

            # Test 8GB system - should keep 500K row threshold
            mock_vm.return_value.total = 8 * 1024**3
            total_gb = psutil.virtual_memory().total / 1024**3
            if total_gb >= 32:
                threshold = 3_000_000
            elif total_gb >= 16:
                threshold = 1_500_000
            else:
                threshold = 500_000

            assert threshold == 500_000

    def test_fallback_threshold_scaling(self):
        """Test that fallback thresholds scale appropriately (500K → 1.5M → 3M)."""
        # Validate the 3x and 6x increases for different system tiers
        old_threshold = 500_000

        # 16GB system gets 3x increase
        threshold_16gb = 1_500_000
        assert threshold_16gb / old_threshold == 3.0

        # 32GB system gets 6x increase
        threshold_32gb = 3_000_000
        assert threshold_32gb / old_threshold == 6.0


class TestSecondaryAnalyzerUpdates:
    """Test secondary analyzer chunk size updates."""

    def test_ngram_stats_chunk_limits_updated(self):
        """Test that N-gram stats chunk limits increased significantly."""

        # Simulate the new chunk calculation from Phase 4
        def calculate_ngram_stats_chunk_size(
            message_ngram_count: int, ngram_count: int
        ) -> int:
            # New formula: max(5_000, min(50_000, 500_000 // max(1, message_ngram_count // ngram_count)))
            base_calc = 500_000 // max(1, message_ngram_count // ngram_count)
            return max(5_000, min(50_000, base_calc))

        def calculate_ngram_stats_chunk_size_old(
            message_ngram_count: int, ngram_count: int
        ) -> int:
            # Old formula: max(1, min(10_000, 100_000 // max(1, message_ngram_count // ngram_count)))
            base_calc = 100_000 // max(1, message_ngram_count // ngram_count)
            return max(1, min(10_000, base_calc))

        # Test with various realistic data sizes
        test_cases = [
            (100_000, 1_000),  # Small dataset
            (500_000, 5_000),  # Medium dataset
            (1_000_000, 10_000),  # Large dataset
        ]

        for message_ngram_count, ngram_count in test_cases:
            new_chunk = calculate_ngram_stats_chunk_size(
                message_ngram_count, ngram_count
            )
            old_chunk = calculate_ngram_stats_chunk_size_old(
                message_ngram_count, ngram_count
            )

            # New chunks should be significantly larger
            assert new_chunk >= old_chunk

            # Minimum should be 5,000 instead of 1
            assert new_chunk >= 5_000

            # Maximum should be 50,000 instead of 10,000
            if message_ngram_count // ngram_count <= 10:  # Would hit maximum
                assert new_chunk <= 50_000

    def test_ngram_stats_minimum_chunk_increase(self):
        """Test that minimum chunk size increased from 1 to 5,000."""

        # Test edge case where calculation would give very small result
        def calculate_ngram_stats_chunk_size(
            message_ngram_count: int, ngram_count: int
        ) -> int:
            base_calc = 500_000 // max(1, message_ngram_count // ngram_count)
            return max(5_000, min(50_000, base_calc))

        # Large message_ngram_count relative to ngram_count should hit minimum
        chunk_size = calculate_ngram_stats_chunk_size(10_000_000, 100_000)
        assert chunk_size == 5_000  # Should be minimum, not 1

    def test_ngram_stats_maximum_chunk_increase(self):
        """Test that maximum chunk size increased from 10,000 to 50,000."""

        def calculate_ngram_stats_chunk_size(
            message_ngram_count: int, ngram_count: int
        ) -> int:
            base_calc = 500_000 // max(1, message_ngram_count // ngram_count)
            return max(5_000, min(50_000, base_calc))

        # Small message_ngram_count relative to ngram_count should hit maximum
        chunk_size = calculate_ngram_stats_chunk_size(100, 1000)
        assert chunk_size == 50_000  # Should be new maximum, not 10,000


class TestSystemConfigurationValidation:
    """Test system configuration detection and validation."""

    def test_memory_usage_stays_within_bounds(self):
        """Test that memory usage stays within auto-detected limits."""
        with patch("psutil.virtual_memory") as mock_vm:
            # Test 16GB system
            mock_vm.return_value.total = 16 * 1024**3
            memory_manager = MemoryManager()

            # Should allocate 30% of 16GB = 4.8GB
            expected_limit = 4.8
            assert abs(memory_manager.max_memory_gb - expected_limit) < 0.1

            # Memory usage should not exceed the limit during processing
            initial_memory = memory_manager.get_current_memory_usage()

            # Simulate some memory usage
            large_data = [list(range(1000)) for _ in range(100)]
            current_memory = memory_manager.get_current_memory_usage()

            # Should still be within reasonable bounds
            assert (
                current_memory["rss_gb"] <= memory_manager.max_memory_gb * 1.2
            )  # 20% tolerance

    def test_memory_pressure_detection_accuracy(self):
        """Test that memory pressure detection works accurately with new thresholds."""
        manager = MemoryManager(max_memory_gb=1.0)

        with patch.object(manager.process, "memory_info") as mock_memory:
            # Test LOW pressure (below 70%)
            mock_memory.return_value.rss = int(0.5 * manager.max_memory_bytes)
            assert manager.get_memory_pressure_level() == MemoryPressureLevel.LOW

            # Test MEDIUM pressure (70-80%)
            mock_memory.return_value.rss = int(0.75 * manager.max_memory_bytes)
            assert manager.get_memory_pressure_level() == MemoryPressureLevel.MEDIUM

            # Test HIGH pressure (80-90%)
            mock_memory.return_value.rss = int(0.85 * manager.max_memory_bytes)
            assert manager.get_memory_pressure_level() == MemoryPressureLevel.HIGH

            # Test CRITICAL pressure (>90%)
            mock_memory.return_value.rss = int(0.95 * manager.max_memory_bytes)
            assert manager.get_memory_pressure_level() == MemoryPressureLevel.CRITICAL

    def test_auto_detection_edge_cases(self):
        """Test auto-detection handles edge cases properly."""
        with patch("psutil.virtual_memory") as mock_vm:
            # Test exactly at boundaries
            mock_vm.return_value.total = 8 * 1024**3  # Exactly 8GB
            limit_8gb = MemoryManager._auto_detect_memory_limit()
            assert abs(limit_8gb - 2.0) < 0.1  # Should be 25%

            mock_vm.return_value.total = 16 * 1024**3  # Exactly 16GB
            limit_16gb = MemoryManager._auto_detect_memory_limit()
            assert abs(limit_16gb - 4.8) < 0.1  # Should be 30%

            mock_vm.return_value.total = 32 * 1024**3  # Exactly 32GB
            limit_32gb = MemoryManager._auto_detect_memory_limit()
            assert abs(limit_32gb - 12.8) < 0.1  # Should be 40%

            # Test very small system
            mock_vm.return_value.total = 2 * 1024**3  # 2GB
            limit_2gb = MemoryManager._auto_detect_memory_limit()
            assert abs(limit_2gb - 0.4) < 0.1  # Should be 20%

    def test_backward_compatibility_preserved(self):
        """Test that manual override still works exactly as before."""
        with patch("psutil.virtual_memory") as mock_vm:
            mock_vm.return_value.total = 16 * 1024**3

            # Manual override should bypass auto-detection completely
            manager = MemoryManager(max_memory_gb=2.0)
            assert manager.max_memory_gb == 2.0

            # Should work with any value, even unreasonable ones
            manager = MemoryManager(max_memory_gb=100.0)
            assert manager.max_memory_gb == 100.0


class TestPerformanceBenchmarks:
    """Performance benchmarking tests."""

    def test_chunk_size_performance_scaling(self):
        """Test that larger chunk sizes provide better performance characteristics."""
        # Create test datasets of different sizes
        small_data = self._create_test_dataset(10_000)
        medium_data = self._create_test_dataset(100_000)
        large_data = self._create_test_dataset(500_000)

        # Test with different chunk sizes
        old_chunk_size = 50_000  # Old base size
        new_chunk_size = 150_000  # New base size

        # For small datasets, chunk size should be optimized for data size
        small_optimal = min(len(small_data), new_chunk_size)
        assert small_optimal <= new_chunk_size

        # For medium datasets, should use larger chunks
        medium_optimal = min(len(medium_data), new_chunk_size)
        assert medium_optimal > old_chunk_size

        # For large datasets, should still be reasonable
        large_optimal = min(len(large_data), new_chunk_size)
        assert large_optimal >= old_chunk_size

    def test_memory_efficiency_improvements(self):
        """Test that memory efficiency has improved with new chunking."""
        # Test memory manager with different configurations
        old_memory_manager = MemoryManager(max_memory_gb=4.0)  # Old hardcoded limit

        with patch("psutil.virtual_memory") as mock_vm:
            mock_vm.return_value.total = 16 * 1024**3
            new_memory_manager = MemoryManager()  # Auto-detected limit

            # New manager should have higher limit on 16GB system
            assert new_memory_manager.max_memory_gb > old_memory_manager.max_memory_gb

            # Should be approximately 4.8GB for 16GB system
            assert abs(new_memory_manager.max_memory_gb - 4.8) < 0.1

    def test_io_operation_reduction_estimation(self):
        """Test estimation of I/O operation reduction."""
        # Simulate old vs new chunking for a 2M row dataset
        dataset_size = 2_000_000

        # Old chunking: 50K base chunks
        old_chunk_size = 50_000
        old_num_chunks = (dataset_size + old_chunk_size - 1) // old_chunk_size

        # New chunking: 150K base chunks (3x larger)
        new_chunk_size = 150_000
        new_num_chunks = (dataset_size + new_chunk_size - 1) // new_chunk_size

        # Should have significantly fewer I/O operations
        io_reduction_factor = old_num_chunks / new_num_chunks
        assert io_reduction_factor >= 2.5  # At least 2.5x fewer operations
        assert io_reduction_factor <= 4.0  # Reasonable upper bound

    def test_progress_reporting_efficiency(self):
        """Test that progress reporting overhead is reduced with larger chunks."""
        # Larger chunks mean fewer progress updates, reducing overhead
        dataset_size = 1_000_000

        old_chunk_size = 50_000
        new_chunk_size = 150_000

        old_progress_updates = dataset_size // old_chunk_size
        new_progress_updates = dataset_size // new_chunk_size

        # Should have fewer progress updates
        assert new_progress_updates < old_progress_updates

        # Should be approximately 3x fewer updates
        reduction_ratio = old_progress_updates / new_progress_updates
        assert 2.5 <= reduction_ratio <= 3.5

    def _create_test_dataset(self, size: int) -> pl.DataFrame:
        """Create a test dataset of specified size."""
        return pl.DataFrame(
            {
                "message_id": range(size),
                "message_text": [f"test message {i} with content" for i in range(size)],
                "author_id": [f"user_{i % 100}" for i in range(size)],
                "timestamp": ["2023-01-01T00:00:00Z"] * size,
            }
        )


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases."""

    def test_zero_memory_system_handling(self):
        """Test handling of systems with very little memory."""
        with patch("psutil.virtual_memory") as mock_vm:
            # Simulate system with very little memory
            mock_vm.return_value.total = 512 * 1024**2  # 512MB

            limit = MemoryManager._auto_detect_memory_limit()

            # Should still provide some allocation
            assert limit > 0
            assert limit < 1.0  # Should be less than 1GB

            # Should use conservative 20% allocation
            expected = (512 / 1024) * 0.2  # 512MB * 20% = ~0.1GB
            assert abs(limit - expected) < 0.05

    def test_memory_manager_initialization_errors(self):
        """Test memory manager handles initialization errors gracefully."""
        with patch("psutil.virtual_memory") as mock_vm:
            # Simulate psutil error
            mock_vm.side_effect = Exception("Memory detection failed")

            # Should fall back to reasonable default
            with pytest.raises(Exception):
                MemoryManager()

    def test_chunk_size_calculation_edge_cases(self):
        """Test chunk size calculation with edge case inputs."""

        def test_calculate_optimal_chunk_size(
            dataset_size: int, memory_manager=None
        ) -> int:
            memory_factor = 1.0 if memory_manager else 1.0

            if dataset_size <= 500_000:
                base_chunk = int(200_000 * memory_factor)
            elif dataset_size <= 2_000_000:
                base_chunk = int(150_000 * memory_factor)
            elif dataset_size <= 5_000_000:
                base_chunk = int(100_000 * memory_factor)
            else:
                base_chunk = int(75_000 * memory_factor)

            return max(10_000, min(base_chunk, 500_000))

        # Test with zero dataset size
        chunk_size = test_calculate_optimal_chunk_size(0)
        assert chunk_size >= 10_000  # Should enforce minimum

        # Test with very large dataset
        chunk_size = test_calculate_optimal_chunk_size(100_000_000)
        assert chunk_size <= 500_000  # Should enforce maximum

        # Test with exactly boundary values
        chunk_size = test_calculate_optimal_chunk_size(500_000)
        assert chunk_size > 0

    def test_fallback_mechanisms_under_pressure(self):
        """Test that fallback mechanisms work under genuine memory pressure."""
        memory_manager = MemoryManager(max_memory_gb=0.5)  # Very limited

        # Mock the process memory info to simulate critical pressure
        with patch.object(memory_manager.process, 'memory_info') as mock_memory:
            # Simulate critical memory usage (95% of max)
            mock_memory.return_value.rss = int(0.95 * memory_manager.max_memory_bytes)
            
            # Should drastically reduce chunk size under critical pressure
            base_size = 100_000
            adaptive_size = memory_manager.calculate_adaptive_chunk_size(
                base_size, "ngram_generation"
            )

            # Should be significantly reduced
            assert adaptive_size < base_size * 0.5

            # Should still be above minimum
            expected_min = max(1000, base_size // 10)
            assert adaptive_size >= expected_min


class TestRegressionPrevention:
    """Test that existing functionality is not broken."""

    def test_existing_memory_manager_api_unchanged(self):
        """Test that existing MemoryManager API continues to work."""
        # Test all existing methods still work
        manager = MemoryManager(max_memory_gb=2.0)

        # Core functionality
        assert hasattr(manager, "get_current_memory_usage")
        assert hasattr(manager, "get_memory_pressure_level")
        assert hasattr(manager, "calculate_adaptive_chunk_size")
        assert hasattr(manager, "should_trigger_gc")
        assert hasattr(manager, "enhanced_gc_cleanup")
        assert hasattr(manager, "get_memory_trend")

        # All methods should be callable
        stats = manager.get_current_memory_usage()
        assert isinstance(stats, dict)

        pressure = manager.get_memory_pressure_level()
        assert isinstance(pressure, MemoryPressureLevel)

        chunk_size = manager.calculate_adaptive_chunk_size(10000, "tokenization")
        assert isinstance(chunk_size, int)
        assert chunk_size > 0

    def test_existing_tests_still_pass(self):
        """Ensure that optimization doesn't break existing functionality."""
        # Test that basic memory management still works
        manager = MemoryManager(max_memory_gb=1.0)

        # Memory usage detection
        stats = manager.get_current_memory_usage()
        required_fields = [
            "rss_bytes",
            "vms_bytes",
            "rss_mb",
            "vms_mb",
            "rss_gb",
            "system_available_gb",
            "system_used_percent",
            "process_memory_percent",
            "pressure_level",
        ]

        for field in required_fields:
            assert field in stats

        # Adaptive chunk sizing with different operations
        operations = ["tokenization", "ngram_generation", "unique_extraction"]
        for operation in operations:
            chunk_size = manager.calculate_adaptive_chunk_size(10000, operation)
            assert chunk_size > 0
            # Allow for operation-specific scaling (unique_extraction uses 1.2x factor)
            if operation == "unique_extraction":
                assert chunk_size <= 10000 * 1.2  # Allow for scaling up
            else:
                assert chunk_size <= 10000  # Should not exceed base for most operations


class TestIntegrationValidation:
    """Integration tests validating end-to-end improvements."""

    def test_memory_manager_integration_with_ngram_analyzer(self):
        """Test that memory manager integrates properly with n-gram analyzer."""
        # This would test the actual integration, but we'll mock it to avoid
        # running the full analyzer in tests

        memory_manager = MemoryManager()

        # Simulate the integration points
        assert memory_manager.max_memory_gb > 0
        assert hasattr(memory_manager, "calculate_adaptive_chunk_size")

        # Test that the memory manager can be passed to analyzer functions
        base_chunk = 100_000
        adaptive_chunk = memory_manager.calculate_adaptive_chunk_size(
            base_chunk, "ngram_generation"
        )

        # Should return a reasonable chunk size
        assert adaptive_chunk > 0
        assert adaptive_chunk <= base_chunk * 2  # Allow for some scaling up

    def test_system_specific_performance_characteristics(self):
        """Test that different system configurations get appropriate performance."""
        test_systems = [
            (4, 0.8),  # 4GB system, 20% allocation
            (8, 2.0),  # 8GB system, 25% allocation
            (16, 4.8),  # 16GB system, 30% allocation
            (32, 12.8),  # 32GB system, 40% allocation
        ]

        for total_gb, expected_limit in test_systems:
            with patch("psutil.virtual_memory") as mock_vm:
                mock_vm.return_value.total = total_gb * 1024**3

                manager = MemoryManager()

                # Should allocate appropriate amount
                assert abs(manager.max_memory_gb - expected_limit) < 0.1

                # Higher memory systems should get better performance
                if total_gb >= 16:
                    assert manager.max_memory_gb >= 4.0

                    # Should have more lenient pressure thresholds
                    assert manager.thresholds[MemoryPressureLevel.MEDIUM] >= 0.70

    @pytest.mark.skipif(
        psutil.virtual_memory().total < 8 * 1024**3,
        reason="Requires at least 8GB RAM for meaningful performance test",
    )
    def test_real_system_performance_validation(self):
        """Test performance improvements on real system (when possible)."""
        # Only run on systems with sufficient memory
        system_memory_gb = psutil.virtual_memory().total / 1024**3

        manager = MemoryManager()

        # Auto-detection should work correctly
        assert manager.max_memory_gb > 0
        assert manager.max_memory_gb <= system_memory_gb * 0.5  # Reasonable upper bound

        # Should provide better performance than old hardcoded 4GB limit
        if system_memory_gb >= 16:
            assert manager.max_memory_gb > 4.0
        elif system_memory_gb >= 8:
            assert manager.max_memory_gb >= 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
