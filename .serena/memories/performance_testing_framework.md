# Performance Testing Framework

## Overview

The Mango Tango CLI includes a comprehensive performance testing and benchmarking framework designed to validate performance optimizations, particularly for the N-gram analyzer chunking strategy. This framework ensures that performance improvements meet targets and don't introduce regressions.

## Framework Architecture

### Test Organization

**Core Test Files** (`testing/performance/`):

- `test_chunking_optimization.py` - Primary optimization functionality tests
- `test_performance_benchmarks.py` - Real performance measurements and stress tests
- `test_enhanced_benchmarks.py` - Enhanced benchmarking with memory profiling
- `test_integration_validation.py` - End-to-end integration tests
- `run_performance_tests.py` - Performance test runner with configurable parameters
- `run_enhanced_benchmarks.py` - Enhanced benchmark execution with detailed metrics

### Test Categories and Coverage

#### Phase 1: Smart Memory Detection
- ✅ Auto-detection validation for different system tiers (8GB/16GB/32GB+)
- ✅ Manual override vs auto-detection behavior
- ✅ Memory detection logging and transparency
- ✅ Updated pressure thresholds validation (70%/80%/90% vs old 60%/75%/85%)
- ✅ Less aggressive chunk size reduction factors

#### Phase 2: Adaptive Chunking Strategy
- ✅ Memory factor calculation (0.5x to 2.0x scaling based on system RAM)
- ✅ Adaptive chunk scaling by dataset size (tiered approach)
- ✅ Chunk size bounds enforcement (10K minimum, 500K maximum)
- ✅ Base chunk size increases (50K → 150K-200K depending on system)

#### Phase 3: Fallback Optimization
- ✅ Fallback processor base chunk increases (25K → 100K+)
- ✅ Memory-aware fallback thresholds (500K → 1.5M → 3M rows)
- ✅ System-specific fallback threshold scaling validation

#### Phase 4: Secondary Analyzer Updates
- ✅ N-gram stats chunk limit improvements (1-10K → 5K-50K rows)
- ✅ Minimum chunk size increases (1 → 5,000 rows)
- ✅ Maximum chunk size improvements (10K → 50K rows)

#### Phase 5: Comprehensive Validation
- ✅ System configuration validation across different RAM sizes
- ✅ Memory usage bounds checking and safety validation
- ✅ Performance benchmarking with real dataset measurements
- ✅ Error handling and edge case validation
- ✅ Regression prevention (backward compatibility)
- ✅ Integration validation (end-to-end workflows)

## Test Execution Framework

### Pytest Markers and Organization

**Custom Pytest Markers**:
- `@pytest.mark.performance` - Long-running benchmarks measuring actual performance
- `@pytest.mark.slow` - Any test requiring significant execution time
- `@pytest.mark.stress` - Extreme condition testing and memory stability

**Default Behavior**:
- `pytest` - Excludes performance benchmarks (functional tests only)
- `pytest -m performance` - Runs only performance benchmarks
- `pytest -m "not performance"` - Explicitly excludes performance benchmarks
- `pytest -m ""` - Runs all tests including performance benchmarks

### Test Execution Patterns

#### Quick Development Validation
```bash
pytest testing/performance/test_chunking_optimization.py -v
pytest testing/performance/ -v -k "not benchmark and not stress"
```

#### Performance Benchmarking
```bash
pytest -m performance -v
pytest testing/performance/test_performance_benchmarks.py -m performance -v
python testing/performance/run_enhanced_benchmarks.py
```

#### Comprehensive Testing
```bash
pytest testing/performance/ -m "" -v
pytest testing/performance/ -m "" -v -s --durations=10
```

#### Targeted Test Categories
```bash
pytest testing/performance/ -v -k "memory_detection"
pytest testing/performance/ -v -k "adaptive_chunk"  
pytest testing/performance/ -v -k "system_config"
```

## Performance Validation Metrics

### Expected Improvements

**Time Performance**:
- Small datasets (100K rows): ≥1.2x faster minimum
- Medium datasets (500K rows): ≥1.5x faster minimum
- Large datasets (1M+ rows): ≥2.0x faster minimum

**I/O Efficiency**:
- Chunk count reduction: 2.5x to 6x fewer write operations
- Progress reporting: 3x fewer updates (reduced overhead)

**Memory Utilization**:
- 8GB systems: 2.0GB allocation (25% vs old hardcoded 4GB)
- 16GB systems: 4.8GB allocation (30% vs old hardcoded 4GB)
- 32GB systems: 12.8GB allocation (40% vs old hardcoded 4GB)

**System-Specific Scaling**:
- Memory factors: 0.5x (constrained) to 2.0x (high-memory) chunk scaling
- Fallback thresholds: 500K → 1.5M → 3M rows based on system RAM
- Pressure thresholds: More lenient scaling prevents premature downscaling

### Benchmark Methodology

**Dataset Generation**:
- Synthetic but realistic data with variable message lengths (10-40 tokens)
- Realistic word distributions and user patterns
- Time-based variations and multiple data characteristics
- Scalable dataset sizes for different test scenarios

**Measurement Approach**:
- Multiple runs with garbage collection between tests
- Memory usage monitoring throughout execution
- Time-based measurements with reasonable tolerances
- System-specific scaling expectations and validation

**Validation Criteria**:
- Performance improvements meet or exceed targets
- Memory usage stays within auto-detected limits
- Backward compatibility preserved for manual configurations
- Error handling works correctly for edge cases and constrained systems

## Test Infrastructure Components

### Test Classes and Structure

**TestMemoryAutoDetection**:
- System RAM detection and configuration validation
- Manual override vs auto-detection behavior verification
- Memory allocation percentage validation for different system tiers

**TestAdaptiveChunkSizing**:
- Chunk size calculation and scaling validation
- Memory factor application verification (0.5x to 2.0x)
- Bounds enforcement testing (10K minimum, 500K maximum)

**TestPerformanceBenchmarks**:
- Real dataset performance measurements
- Time improvement validation against targets
- I/O operation reduction verification

**TestStressTests**:
- Extreme condition testing and memory stability
- Large dataset handling validation
- Memory pressure response testing

**TestIntegrationValidation**:
- End-to-end workflow testing
- Integration with existing analyzer infrastructure
- Regression prevention validation

## Development and Maintenance

### Adding New Performance Tests

**Best Practices**:
1. Use `_create_realistic_dataset()` for consistent test data
2. Include proper setup/teardown with garbage collection
3. Set reasonable performance expectations based on system capabilities
4. Include both positive and negative test cases
5. Add appropriate skip conditions for low-memory systems

**Test Data Characteristics**:
- Variable message lengths reflecting real-world data
- Realistic token distributions and user patterns
- Scalable dataset generation for different test scenarios
- Consistent data quality for reliable benchmarking

### Maintenance Requirements

**Update Triggers**:
- New optimization phases implementation
- Performance target adjustments
- New system configuration support requirements
- Benchmark methodology improvements

**Validation Process**:
- All tests must pass for optimization validation
- Performance metrics must meet or exceed targets
- Memory usage must stay within detected system limits
- Backward compatibility must be preserved

## Integration with CI/CD

**Fast Development Pipeline**:
- Default `pytest` runs exclude performance benchmarks
- Quick functional validation for development iteration
- Memory detection and basic functionality verification

**Comprehensive Validation Pipeline**:
- Full performance benchmark execution for release validation
- Stress testing for stability verification
- Multi-system configuration validation
- Performance regression detection

## Usage Recommendations

### Development Workflow
1. Run quick validation tests during development (`pytest testing/performance/test_chunking_optimization.py -v`)
2. Validate specific functionality areas (`pytest -k "adaptive_chunk"`)
3. Run comprehensive benchmarks before major releases (`pytest -m performance -v`)

### Performance Analysis
1. Monitor time improvement metrics (≥1.2x, ≥1.5x, ≥2.0x targets)
2. Verify I/O operation reduction (≥2.5x fewer chunks)
3. Validate memory utilization scaling (system-appropriate allocation)
4. Check system-specific scaling behavior

This comprehensive testing framework ensures that performance optimizations deliver measurable improvements while maintaining system stability and backward compatibility across diverse deployment environments.