# Performance Testing Suite - Chunking Optimization

## Test Coverage

### Phase 1: Smart Memory Detection

- ✅ Auto-detection tiers (8GB/16GB/32GB systems)
- ✅ Manual override vs auto-detection
- ✅ Memory detection logging
- ✅ Updated pressure thresholds (more lenient)
- ✅ Updated chunk size factors (less aggressive)

### Phase 2: Adaptive Chunking Strategy

- ✅ Memory factor calculation (0.5x to 2.0x)
- ✅ Adaptive chunk scaling by dataset size
- ✅ Chunk size bounds enforcement (10K-500K)
- ✅ Base chunk increases validation (50K → 150K-200K)

### Phase 3: Fallback Optimization

- ✅ Fallback base chunk increase (25K → 100K)
- ✅ Memory-aware fallback thresholds (500K → 1.5M → 3M)
- ✅ Fallback threshold scaling validation

### Phase 4: Secondary Analyzer Updates

- ✅ N-gram stats chunk limits updated (1-10K → 5K-50K)
- ✅ Minimum chunk increase (1 → 5,000)
- ✅ Maximum chunk increase (10K → 50K)

### Phase 5: Testing & Validation

- ✅ System configuration validation
- ✅ Memory usage bounds checking
- ✅ Performance benchmarking
- ✅ Error handling and edge cases
- ✅ Regression prevention
- ✅ Integration validation

## Running Tests

⚠️ **Note**: Performance benchmarks are excluded from regular `pytest` runs by default to prevent long execution times during development.

### Quick Validation (Default)

```bash
# Run all tests EXCEPT performance benchmarks (default behavior)
pytest

# Run only performance tests from this directory (excluding benchmarks)
pytest testing/performance/test_chunking_optimization.py -v

# Run specific functionality tests
pytest testing/performance/ -v -k "not benchmark and not stress"
```

### Performance Benchmarks

```bash
# Run ONLY performance benchmarks (slow, comprehensive)
pytest -m performance -v

# Run performance benchmarks from specific file
pytest testing/performance/test_performance_benchmarks.py -m performance -v

# Run all tests INCLUDING performance benchmarks
pytest -m "" -v
# OR
pytest --ignore-markers -v
```

### Full Performance Suite

```bash
# Run all performance tests (includes benchmarks)
pytest testing/performance/ -m "" -v

# Run with verbose output and timing
pytest testing/performance/ -m "" -v -s --durations=10
```

### Specific Test Categories

```bash
# Memory detection tests
pytest testing/performance/ -v -k "memory_detection"

# Adaptive chunking tests
pytest testing/performance/ -v -k "adaptive_chunk"

# Performance benchmarks only (using pytest marks)
pytest -m performance -v

# System configuration tests
pytest testing/performance/ -v -k "system_config"

# All slow tests (including performance benchmarks)
pytest -m slow -v

# Exclude slow tests (faster development testing)
pytest -m "not slow" -v
```

## Test Organization & Markers

### Pytest Markers

The performance tests use custom pytest markers for organization:

- **`@pytest.mark.performance`**: Long-running performance benchmarks that measure actual execution times and memory usage
- **`@pytest.mark.slow`**: Any test that takes significant time to run (includes performance benchmarks)

### Default Behavior

- **`pytest`**: Excludes performance benchmarks (runs functional tests only)
- **`pytest -m performance`**: Runs only performance benchmarks
- **`pytest -m "not performance"`**: Explicitly excludes performance benchmarks
- **`pytest -m ""`**: Runs all tests including performance benchmarks

## Test Files

### `test_chunking_optimization.py`

Core functionality tests for all optimization phases:

- **TestMemoryAutoDetection**: Memory detection and configuration
- **TestAdaptiveChunkSizing**: Chunk size calculation and scaling
- **TestFallbackOptimization**: Fallback processor improvements
- **TestSecondaryAnalyzerUpdates**: Secondary analyzer optimizations
- **TestSystemConfigurationValidation**: System-specific validation
- **TestPerformanceBenchmarks**: Basic performance measurements
- **TestErrorHandlingAndEdgeCases**: Edge case and error handling
- **TestRegressionPrevention**: Backward compatibility validation
- **TestIntegrationValidation**: End-to-end integration tests

### `test_performance_benchmarks.py`

Comprehensive performance measurements and stress tests:

- **TestPerformanceBenchmarks**: Real performance measurement with datasets
- **TestStressTests**: Extreme condition testing and memory stability

## Expected Performance Improvements

### Time Performance

- **Small datasets (100K)**: 1.2x faster minimum
- **Medium datasets (500K)**: 1.5x faster minimum
- **Large datasets (1M+)**: 2.0x faster minimum

### I/O Efficiency

- **Chunk count reduction**: 2.5x to 6x fewer write operations
- **Progress reporting**: 3x fewer updates (reduced overhead)

### Memory Utilization

- **8GB systems**: 2.0GB allocation (25% vs old 4GB cap)
- **16GB systems**: 4.8GB allocation (30% vs old 4GB cap)
- **32GB systems**: 12.8GB allocation (40% vs old 4GB cap)

### System-Specific Scaling

- **Memory factors**: 0.5x (4GB) to 2.0x (32GB+) chunk scaling
- **Fallback thresholds**: 500K → 1.5M → 3M rows based on RAM
- **Pressure thresholds**: More lenient (70%/80%/90% vs 60%/75%/85%)

## Test Requirements

### Minimum System Requirements

- Python 3.12+
- 4GB RAM minimum (some tests require 8GB+)
- pytest, polars, psutil dependencies

### Optional Requirements

- 8GB+ RAM for comprehensive benchmarks
- 16GB+ RAM for high-memory system testing

### Test Data

Tests create synthetic datasets with realistic characteristics:

- Variable message lengths (10-40 tokens)
- Realistic word distributions
- Multiple user patterns
- Time-based variations

## Interpreting Results

### Success Criteria

All tests should pass, indicating:

- ✅ Memory detection works correctly for system configuration
- ✅ Chunk sizes scale appropriately with system memory
- ✅ Performance improvements meet or exceed targets
- ✅ Memory usage stays within detected limits
- ✅ Backward compatibility is preserved
- ✅ Error handling works for edge cases

### Performance Metrics

Look for these key improvements in test output:

- `time_improvement`: Should be ≥1.2x for small, ≥1.5x for medium, ≥2.0x for large
- `io_reduction`: Should be ≥2.5x fewer chunk operations
- `memory_factor`: Should scale from 0.5x to 2.0x based on system RAM
- `chunk_size`: Should be 3x larger than old 50K base (150K-300K typical)

### Failure Analysis

If tests fail, check:

1. **System memory**: Some tests require adequate RAM
2. **Memory pressure**: Close other applications during testing
3. **Test environment**: Ensure clean Python environment
4. **Implementation**: Verify all optimization phases are correctly implemented

## Development Notes

### Adding New Tests

When adding performance tests:

1. Use realistic test data with `_create_realistic_dataset()`
2. Include proper setup/teardown with garbage collection
3. Set reasonable performance expectations based on system capabilities
4. Include both positive and negative test cases
5. Add appropriate skip conditions for low-memory systems

### Benchmark Methodology

Performance benchmarks use:

- Synthetic but realistic datasets
- Multiple runs with garbage collection between tests
- Memory usage monitoring
- Time-based measurements with reasonable tolerances
- System-specific scaling expectations

### Maintenance

These tests should be updated when:

- New optimization phases are implemented
- Performance targets change
- New system configurations need support
- Benchmark methodology improves
