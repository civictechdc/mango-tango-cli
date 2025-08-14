"""
Performance Testing Suite for Chunking Optimization

This package contains comprehensive tests for validating the performance improvements
introduced in the N-gram analyzer chunking optimization (Phases 1-4).

Test Modules:
- test_chunking_optimization.py: Core functionality and system configuration tests
- test_performance_benchmarks.py: Real performance measurements and stress tests

Usage:
    pytest tests/performance/ -v                    # Run all performance tests
    pytest tests/performance/ -v -k "not benchmark" # Skip expensive benchmark tests
    pytest tests/performance/ -v --tb=short         # Concise output
    pytest tests/performance/ -v -s                 # Show print output from benchmarks
"""

# Performance test configuration
PERFORMANCE_TEST_CONFIG = {
    "small_dataset_size": 100_000,
    "medium_dataset_size": 500_000,
    "large_dataset_size": 1_000_000,
    "stress_dataset_size": 2_000_000,
    "expected_min_improvement": {
        "small": 1.2,  # 20% minimum improvement for small datasets
        "medium": 1.5,  # 50% minimum improvement for medium datasets
        "large": 2.0,  # 100% minimum improvement for large datasets
    },
    "memory_thresholds": {
        "test_timeout_seconds": 300,  # 5 minute timeout for long tests
        "max_memory_increase_mb": 1000,  # Maximum acceptable memory increase
        "gc_frequency": 10,  # Trigger GC every N chunks in tests
    },
}
