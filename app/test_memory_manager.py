"""
Comprehensive tests for the MemoryManager class and memory-aware processing.
"""

import gc
import time
from unittest.mock import MagicMock, patch

import pytest

from app.utils import MemoryManager, MemoryPressureLevel


class TestMemoryManager:
    """Test core MemoryManager functionality."""

    def test_memory_manager_initialization(self):
        """Test MemoryManager initializes correctly."""
        manager = MemoryManager(max_memory_gb=2.0, process_name="test")

        assert manager.max_memory_bytes == 2.0 * 1024**3
        assert manager.process_name == "test"
        assert len(manager.thresholds) == 3
        assert len(manager.chunk_size_factors) == 4
        assert manager.memory_history == []

    def test_get_current_memory_usage(self):
        """Test memory usage statistics collection."""
        manager = MemoryManager()
        stats = manager.get_current_memory_usage()

        # Check all required fields are present
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
            assert isinstance(stats[field], (int, float, str))

        # Check memory history is updated
        assert len(manager.memory_history) == 1
        assert "timestamp" in manager.memory_history[0]
        assert "rss_bytes" in manager.memory_history[0]

    def test_memory_pressure_levels(self):
        """Test memory pressure level detection."""
        manager = MemoryManager(max_memory_gb=1.0)  # Small limit for testing

        # Mock different memory usage levels
        with patch.object(manager.process, "memory_info") as mock_memory:
            # Test LOW pressure (40% usage)
            mock_memory.return_value.rss = int(0.4 * manager.max_memory_bytes)
            assert manager.get_memory_pressure_level() == MemoryPressureLevel.LOW

            # Test MEDIUM pressure (65% usage)
            mock_memory.return_value.rss = int(0.65 * manager.max_memory_bytes)
            assert manager.get_memory_pressure_level() == MemoryPressureLevel.MEDIUM

            # Test HIGH pressure (80% usage)
            mock_memory.return_value.rss = int(0.80 * manager.max_memory_bytes)
            assert manager.get_memory_pressure_level() == MemoryPressureLevel.HIGH

            # Test CRITICAL pressure (90% usage)
            mock_memory.return_value.rss = int(0.90 * manager.max_memory_bytes)
            assert manager.get_memory_pressure_level() == MemoryPressureLevel.CRITICAL

    def test_adaptive_chunk_sizing(self):
        """Test adaptive chunk size calculation based on memory pressure."""
        manager = MemoryManager()
        base_size = 10000

        with patch("app.utils.MemoryManager.get_memory_pressure_level") as mock_pressure:
            # Test LOW pressure - no reduction
            mock_pressure.return_value = MemoryPressureLevel.LOW
            size = manager.calculate_adaptive_chunk_size(base_size, "tokenization")
            assert size == base_size

            # Test MEDIUM pressure - 30% reduction
            mock_pressure.return_value = MemoryPressureLevel.MEDIUM
            size = manager.calculate_adaptive_chunk_size(base_size, "tokenization")
            assert size == int(base_size * 0.7)

            # Test HIGH pressure - 60% reduction
            mock_pressure.return_value = MemoryPressureLevel.HIGH
            size = manager.calculate_adaptive_chunk_size(base_size, "tokenization")
            assert size == int(base_size * 0.4)

            # Test CRITICAL pressure - 80% reduction
            mock_pressure.return_value = MemoryPressureLevel.CRITICAL
            size = manager.calculate_adaptive_chunk_size(base_size, "tokenization")
            assert size == int(base_size * 0.2)

    def test_operation_specific_chunk_sizing(self):
        """Test operation-specific chunk size adjustments."""
        manager = MemoryManager()
        base_size = 10000

        with patch("app.utils.MemoryManager.get_memory_pressure_level") as mock_pressure:
            mock_pressure.return_value = MemoryPressureLevel.LOW

            # Test different operation types
            tokenization_size = manager.calculate_adaptive_chunk_size(
                base_size, "tokenization"
            )
            ngram_size = manager.calculate_adaptive_chunk_size(
                base_size, "ngram_generation"
            )
            unique_size = manager.calculate_adaptive_chunk_size(
                base_size, "unique_extraction"
            )

            # N-gram generation should be smaller (more memory intensive)
            assert ngram_size < tokenization_size
            # Unique extraction should be larger (less memory intensive)
            assert unique_size > tokenization_size

    def test_minimum_chunk_size_enforcement(self):
        """Test that minimum chunk size is enforced."""
        manager = MemoryManager()
        small_base = 5000

        with patch("app.utils.MemoryManager.get_memory_pressure_level") as mock_pressure:
            mock_pressure.return_value = MemoryPressureLevel.CRITICAL

            size = manager.calculate_adaptive_chunk_size(small_base, "ngram_generation")

            # Should not go below minimum (max of 1000 or base_size // 10)
            expected_min = max(1000, small_base // 10)
            assert size >= expected_min

    def test_gc_trigger_threshold(self):
        """Test garbage collection trigger logic."""
        manager = MemoryManager(max_memory_gb=1.0)

        with patch.object(manager.process, "memory_info") as mock_memory:
            # Below threshold - should not trigger
            mock_memory.return_value.rss = int(0.6 * manager.max_memory_bytes)
            assert not manager.should_trigger_gc()

            # Above threshold - should trigger
            mock_memory.return_value.rss = int(0.8 * manager.max_memory_bytes)
            assert manager.should_trigger_gc()

    def test_enhanced_gc_cleanup(self):
        """Test enhanced garbage collection functionality."""
        manager = MemoryManager()

        with patch("app.utils.MemoryManager.get_current_memory_usage") as mock_usage:
            # Mock memory before and after cleanup
            mock_usage.side_effect = [
                {"rss_mb": 1000, "pressure_level": "high"},  # Before
                {"rss_mb": 800, "pressure_level": "medium"},  # After
            ]

            with patch("gc.collect") as mock_gc:
                mock_gc.return_value = 50  # Some objects collected

                stats = manager.enhanced_gc_cleanup()

                assert "memory_freed_mb" in stats
                assert "memory_before_mb" in stats
                assert "memory_after_mb" in stats
                assert "pressure_before" in stats
                assert "pressure_after" in stats

                assert stats["memory_freed_mb"] == 200  # 1000 - 800
                assert mock_gc.call_count >= 1

    def test_memory_trend_analysis(self):
        """Test memory usage trend analysis."""
        manager = MemoryManager()

        # Not enough data
        assert manager.get_memory_trend() == "insufficient_data"

        # Add some increasing memory usage data
        for i in range(5):
            manager.memory_history.append(
                {
                    "timestamp": time.time(),
                    "rss_bytes": 1000 + (i * 100),  # Increasing
                    "pressure_level": "low",
                }
            )

        assert manager.get_memory_trend() == "increasing"

        # Add decreasing data
        manager.memory_history.clear()
        for i in range(5):
            manager.memory_history.append(
                {
                    "timestamp": time.time(),
                    "rss_bytes": 1500 - (i * 100),  # Decreasing
                    "pressure_level": "low",
                }
            )

        assert manager.get_memory_trend() == "decreasing"

        # Add stable data
        manager.memory_history.clear()
        for i in range(5):
            manager.memory_history.append(
                {
                    "timestamp": time.time(),
                    "rss_bytes": 1000 + (i % 2 * 50),  # Fluctuating
                    "pressure_level": "low",
                }
            )

        assert manager.get_memory_trend() == "stable"

    def test_memory_history_size_limit(self):
        """Test memory history size is properly limited."""
        manager = MemoryManager()
        manager.max_history_size = 5  # Small limit for testing

        # Add more entries than the limit
        for i in range(10):
            manager.get_current_memory_usage()

        # Should not exceed the limit
        assert len(manager.memory_history) <= manager.max_history_size


class TestMemoryManagerIntegration:
    """Integration tests for MemoryManager with other components."""

    def test_memory_manager_with_real_operations(self):
        """Test MemoryManager with actual memory operations."""
        manager = MemoryManager(max_memory_gb=8.0)  # Reasonable limit

        # Get baseline
        initial_stats = manager.get_current_memory_usage()
        assert initial_stats["pressure_level"] in ["low", "medium", "high", "critical"]

        # Perform some memory-intensive operations
        large_data = [list(range(1000)) for _ in range(100)]

        # Check memory increased
        after_stats = manager.get_current_memory_usage()
        assert after_stats["rss_mb"] >= initial_stats["rss_mb"]

        # Cleanup and verify GC works
        del large_data
        cleanup_stats = manager.enhanced_gc_cleanup()

        # Should have freed some memory
        assert cleanup_stats["memory_freed_mb"] >= 0

        # Verify trend analysis works with real data
        trend = manager.get_memory_trend()
        assert trend in ["insufficient_data", "increasing", "decreasing", "stable"]

    def test_adaptive_chunk_sizing_realistic_scenarios(self):
        """Test adaptive chunk sizing with realistic scenarios."""
        manager = MemoryManager(max_memory_gb=4.0)

        # Test various operation types with different base sizes
        operations = [
            "tokenization",
            "ngram_generation",
            "unique_extraction",
            "join_operations",
        ]
        base_sizes = [10000, 50000, 100000]

        for operation in operations:
            for base_size in base_sizes:
                adaptive_size = manager.calculate_adaptive_chunk_size(
                    base_size, operation
                )

                # Should never be zero or negative
                assert adaptive_size > 0

                # Should respect minimum size
                expected_min = max(1000, base_size // 10)
                assert adaptive_size >= expected_min

                # Should not exceed original size (except for unique_extraction which can be larger)
                if operation != "unique_extraction":
                    assert adaptive_size <= base_size


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
