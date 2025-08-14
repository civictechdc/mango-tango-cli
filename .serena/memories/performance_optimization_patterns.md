# Performance Optimization Patterns for N-gram Analysis

## Memory-Aware Chunking Strategy

### Core Principle

Intelligent chunk sizing that scales with system memory capabilities while maintaining safety for constrained environments.

### Implementation Pattern

```python
def calculate_optimal_chunk_size(dataset_size: int, memory_manager: MemoryManager = None) -> int:
    # Get memory capacity factor based on system RAM
    if memory_manager:
        total_gb = psutil.virtual_memory().total / 1024**3
        if total_gb >= 32:
            memory_factor = 2.0      # High-memory systems
        elif total_gb >= 16:
            memory_factor = 1.5      # Standard systems
        elif total_gb >= 8:
            memory_factor = 1.0      # Lower-memory systems
        else:
            memory_factor = 0.5      # Very constrained systems
    else:
        memory_factor = 1.0

    # Tiered base chunk sizes scaled by memory capacity
    if dataset_size <= 500_000:
        base_chunk = int(200_000 * memory_factor)
    elif dataset_size <= 2_000_000:
        base_chunk = int(150_000 * memory_factor)
    elif dataset_size <= 5_000_000:
        base_chunk = int(100_000 * memory_factor)
    else:
        base_chunk = int(75_000 * memory_factor)

    return max(10_000, min(base_chunk, 500_000))
```

### System-Specific Optimization Results

#### Memory Allocation Strategy

- **≥32GB systems**: 40% allocation (12-16GB available)
- **≥16GB systems**: 30% allocation (5-8GB available)
- **≥8GB systems**: 25% allocation (2-4GB available)
- **<8GB systems**: 20% allocation (conservative)

#### Chunk Size Scaling

- **High-memory (≥32GB)**: 2.0x multiplier for all chunk calculations
- **Standard (≥16GB)**: 1.5x multiplier
- **Lower-memory (≥8GB)**: 1.0x multiplier (baseline)
- **Constrained (<8GB)**: 0.5x multiplier (conservative)

#### Fallback Thresholds

- **≥32GB systems**: 3M rows before disk-based processing
- **≥16GB systems**: 1.5M rows before disk-based processing
- **<16GB systems**: 500K rows (maintains conservative behavior)

## Performance Impact Measurements

### Before Optimization (16GB System)

- Memory limit: 4.0GB (hardcoded)
- Base chunks: 50,000 rows
- Fallback threshold: 500,000 rows
- Secondary analyzer chunks: 1-10,000 rows

### After Optimization (16GB System)

- Memory limit: 4.8GB (30% auto-detected, 20% improvement)
- Base chunks: 150,000-225,000 rows (1.5x memory factor)
- Fallback threshold: 1,500,000 rows (3x improvement)
- Secondary analyzer chunks: 5,000-50,000 rows (5x-10x improvement)

### Expected Performance Gains

- **2-4x faster processing** for medium datasets (1-5M rows)
- **5-10x reduction in I/O operations** due to larger, more efficient chunks
- **3x higher fallback threshold** enables in-memory processing for larger datasets
- **Better memory utilization** on high-memory systems

## Code Integration Patterns

### Memory Manager Auto-Detection

```python
# Preferred: Auto-detection
memory_manager = MemoryManager()  # Detects system capacity

# Manual override (backward compatible)
memory_manager = MemoryManager(max_memory_gb=8.0)
```

### Function Integration Pattern

```python
def enhanced_processing_function(context, memory_manager=None):
    # Calculate optimal chunk size for current system and dataset
    chunk_size = calculate_optimal_chunk_size(len(dataset), memory_manager)

    # Use adaptive chunking throughout processing pipeline
    for chunk in process_in_chunks(dataset, chunk_size):
        # Processing logic with optimal chunk sizes
        result = process_chunk(chunk)
```

### Progress Reporting Integration

```python
with ProgressManager("Analysis Progress") as progress:
    # Add main steps with calculated chunk counts
    total_chunks = math.ceil(len(dataset) / chunk_size)
    progress.add_step("process", f"Processing {len(dataset)} rows", total=total_chunks)

    # Use hierarchical sub-steps for detailed operations
    progress.add_substep("process", "write", "Writing results", total=output_count)
```

## Memory Pressure Handling

### Adjusted Thresholds (More Lenient)

- **MEDIUM pressure**: 70% (was 60%) - allows more headroom
- **HIGH pressure**: 80% (was 75%) - delays aggressive scaling
- **CRITICAL pressure**: 90% (was 85%) - emergency threshold

### Less Aggressive Chunk Reduction

- **MEDIUM pressure**: 80% retention (was 70%)
- **HIGH pressure**: 60% retention (was 40%)
- **CRITICAL pressure**: 40% retention (was 20%)

## Fallback Optimization Patterns

### Disk-Based Processing Improvements

- **Fallback processor chunks**: 25,000 → 60,000-120,000 rows
- **Memory-aware thresholds**: Scale with system RAM capacity
- **Conservative behavior**: Maintained for <16GB systems

### Secondary Analyzer Optimizations

- **Minimum chunk size**: 1 → 5,000 rows (eliminates tiny chunks)
- **Maximum chunk size**: 10,000 → 50,000 rows (5x improvement)
- **Calculation base**: 100,000 → 500,000 rows (5x scaling factor)

## Best Practices

### Implementation Guidelines

1. **Always pass memory_manager** to chunk calculation functions
2. **Use auto-detection by default** for new installations
3. **Preserve manual overrides** for specialized deployments
4. **Test on various system sizes** during development
5. **Monitor memory usage** during processing

### Validation Patterns

```python
# Validate memory auto-detection
def test_memory_detection():
    mm = MemoryManager()
    total_gb = psutil.virtual_memory().total / 1024**3
    expected_percent = 0.4 if total_gb >= 32 else 0.3 if total_gb >= 16 else 0.25
    assert abs(mm.max_memory_gb - (total_gb * expected_percent)) < 0.1

# Validate chunk size scaling
def test_chunk_scaling():
    mm = MemoryManager()
    chunk_size = calculate_optimal_chunk_size(1_000_000, mm)
    assert chunk_size >= 150_000  # Should be scaled up from base
```

### Error Handling

- **Memory detection failures**: Fall back to conservative 4GB limit
- **Chunk calculation errors**: Use safe minimum bounds (10K-500K)
- **Pressure detection issues**: Default to most aggressive reduction

## Architecture Impact

### Backward Compatibility

- All existing manual memory limits continue to work
- Existing chunk size overrides remain functional
- Test suites pass without modification
- API signatures unchanged (optional parameters added)

### Future Enhancement Opportunities

- Machine learning-based chunk size prediction
- Per-dataset optimal parameter learning
- Container/cloud environment detection
- Real-time memory usage feedback loops

This optimization provides a foundation for intelligent, scalable N-gram processing that adapts to system capabilities while maintaining robust fallback behavior.
