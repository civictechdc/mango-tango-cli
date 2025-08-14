# Progress Reporting Architecture

## Overview

The Mango Tango CLI uses a sophisticated hierarchical progress reporting system built on the Rich library. This system provides real-time feedback during long-running analysis operations and eliminates silent processing periods.

## Core Components

### ProgressManager (`terminal_tools/progress.py`)

The primary progress manager with full hierarchical support:

**Key Features:**

- Hierarchical step and sub-step management
- Rich terminal integration with progress bars and status indicators
- Thread-safe operations with display locks
- Context manager support for clean setup/teardown
- Memory-aware progress calculations

**State Management:**

- `pending` (⏸): Not yet started
- `active` (⏳): Currently running with progress bar
- `completed` (✓): Successfully finished
- `failed` (❌): Failed with optional error message

### ProgressReporter (`terminal_tools/progress.py`)

Basic multiprocess-compatible progress reporting for simple use cases.

### AdvancedProgressReporter (`terminal_tools/progress.py`)

tqdm-based progress reporting with ETA calculation and advanced formatting.

## API Reference

### ProgressManager Methods

**Main Step Management:**

- `add_step(step_id, title, total=None)` - Add progress steps
- `start_step(step_id)` - Start/activate steps
- `update_step(step_id, progress)` - Update step progress
- `complete_step(step_id)` - Mark steps complete
- `fail_step(step_id, error_msg=None)` - Handle step failures

**Hierarchical Sub-Step Management:**

- `add_substep(parent_step_id, substep_id, description, total=None)` - Add sub-steps
- `start_substep(parent_step_id, substep_id)` - Start/activate sub-steps
- `update_substep(parent_step_id, substep_id, progress)` - Update sub-step progress
- `complete_substep(parent_step_id, substep_id)` - Mark sub-steps complete
- `fail_substep(parent_step_id, substep_id, error_msg=None)` - Sub-step error handling

**Internal Methods:**

- `_update_parent_progress(parent_step_id)` - Calculate parent progress from sub-steps
- `_update_display()` - Rich terminal display with hierarchical visualization

## Enhanced N-gram Integration

The enhanced N-gram analyzer (`analyzers/ngrams/ngrams_base/main.py`) demonstrates the recommended pattern:

**Progress Flow:**

- Steps 1-8: Traditional progress reporting for data processing
- Steps 9-11: Hierarchical sub-step progress for final write operations
  - Each write operation broken into 4 sub-steps: prepare, transform, sort, write
  - Eliminates silent processing periods during final 20-30% of analysis time
  - Memory-aware progress calculation based on dataset size

**Enhanced Write Functions:**

- `_enhanced_write_message_ngrams()` - Message writing with sub-step progress
- `_enhanced_write_ngram_definitions()` - Definition writing with sub-step progress
- `_enhanced_write_message_metadata()` - Metadata writing with sub-step progress

**Streaming Optimization:**

- `_stream_unique_batch_accumulator()` - Memory-efficient batch processing
- `_stream_unique_to_temp_file()` - Streaming to temporary files
- `_generate_ngrams_vectorized()` - Vectorized n-gram generation
- `_generate_ngrams_simple()` - Simple n-gram generation fallback

## Integration Points

### AnalysisContext Integration

- `AnalysisContext.progress_callback` provides progress manager to analyzers
- Enhanced write functions use sub-step progress for granular feedback
- Thread-safe progress updates with display locks

### Testing Framework

Comprehensive test coverage with 68+ tests:

- `TestProgressManager` - Basic progress manager functionality
- `TestProgressManagerHierarchical` - 18 methods covering substep functionality, validation, error handling, performance
- `TestProgressReporter` - Basic progress reporter tests
- `TestAdvancedProgressReporter` - Advanced progress reporter with tqdm integration

## Usage Patterns

### Basic Analyzer Pattern

```python
def main(context):
    with ProgressManager("Analysis Progress") as progress:
        progress.add_step("load", "Loading data", total=row_count)
        progress.start_step("load")
        # ... processing with progress.update_step() calls
        progress.complete_step("load")
```

### Hierarchical Pattern (Recommended for Complex Operations)

```python
def main(context):
    with ProgressManager("Enhanced Analysis") as progress:
        progress.add_step("write_outputs", "Writing outputs")
        progress.add_substep("write_outputs", "prepare", "Preparing", total=100)
        progress.add_substep("write_outputs", "write", "Writing", total=200)

        progress.start_step("write_outputs")
        progress.start_substep("write_outputs", "prepare")
        # ... processing with progress.update_substep() calls
        progress.complete_substep("write_outputs", "prepare")
        progress.complete_step("write_outputs")
```

## Technical Implementation

### Rich Integration

- Uses Rich Progress components with custom column configuration
- SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn, TaskProgressColumn, TimeRemainingColumn
- Live display with Group rendering for hierarchical layout
- Responsive terminal layout with proper cleanup

### Thread Safety

- Internal `_display_lock` for synchronizing terminal operations
- Safe for concurrent progress updates from multiple threads
- Graceful handling of KeyboardInterrupt during display updates

### Memory Efficiency

- Lightweight progress tracking with minimal overhead
- Efficient Rich task ID management
- Optimized display updates to prevent performance impact

### Error Handling

- Graceful degradation when display updates fail
- Proper cleanup on exceptions and interrupts
- Informative error messages for debugging

## Performance Characteristics

- **Update Frequency**: Optimal at 100-1000 item intervals
- **Memory Usage**: Minimal overhead, scales with number of steps/substeps
- **Display Refresh**: 4Hz refresh rate for smooth updates
- **Thread Safety**: Full thread safety with minimal locking overhead

## Backward Compatibility

- `ProgressManager (default)` alias maintains compatibility
- Existing ProgressReporter and AdvancedProgressReporter unchanged
- Enhanced analyzers gracefully degrade if progress manager unavailable
