# Testing Infrastructure Symbols

## Test Utilities (`testing/`)

### Test Data Management

- `TestData` - `testing/testdata.py` - Base class for test data handling
- `FileTestData` - File-based test data with path management
- `CsvTestData` - CSV file testing with configurable parsing (`CsvConfig`)
- `JsonTestData` - JSON file testing support
- `ExcelTestData` - Excel file testing with sheet selection
- `ParquetTestData` - Parquet file testing for analyzer outputs
- `PolarsTestData` - In-memory Polars DataFrame testing

### Test Context Framework

- `TestPrimaryAnalyzerContext` - `testing/context.py` - Mock context for primary analyzer testing
- `TestSecondaryAnalyzerContext` - Mock context for secondary analyzer testing
- `TestInputColumnProvider` - Column mapping testing support
- `TestTableReader` - Mock data reader for testing
- `TestOutputWriter` - Mock output writer for testing
- `TestOutputReaderGroupContext` - Multi-output testing context

### Test Execution Framework

- `test_primary_analyzer()` - `testing/testers.py` - Standardized primary analyzer testing
- `test_secondary_analyzer()` - Standardized secondary analyzer testing
- `compare_dfs()` - `testing/comparers.py` - DataFrame comparison utilities

### Progress Reporting Tests

- `TestProgressManager` - `terminal_tools/test_progress.py` - Progress manager tests
  - Core test methods covering progress tracking and reporting
- `TestProgressReporter` - Validates legacy progress reporting components

### Performance Testing Infrastructure

**Performance Testing Suite** (`testing/performance/`):

- `test_performance_benchmarks.py` - Core performance benchmarks for analyzer operations
- `test_enhanced_benchmarks.py` - Enhanced benchmarking with memory profiling
- `test_chunking_optimization.py` - Chunking strategy validation and performance tests
- `test_integration_validation.py` - Integration tests for performance optimizations
- `run_performance_tests.py` - Performance test runner with configurable parameters
- `run_enhanced_benchmarks.py` - Enhanced benchmark execution with detailed metrics

## Terminal Tools (`terminal_tools/`)

### Progress Reporting System

- `ProgressManager` - `terminal_tools/progress.py` - Modern Textual-based progress reporting
  - **Main step management**:
    - `add_step(step_id, title, total=None)` - Add progress steps
    - `start_step(step_id)`, `update_step(step_id, progress)`, `complete_step(step_id)` - Step lifecycle
    - `fail_step(step_id, error_msg=None)` - Error handling

- `ProgressReporter` - Lightweight multiprocess progress reporting (legacy)

### Other Terminal Utilities

- `file_selector()` - `terminal_tools/prompts.py` - Interactive file selection
- `clear_terminal()` - `terminal_tools/utils.py` - Terminal screen clearing
- `enable_windows_ansi_support()` - `terminal_tools/utils.py` - Windows terminal color support

## Example Tests

- `analyzers/ngrams/test_ngrams_base.py` - Comprehensive n-gram analyzer tests with multiple configurations
- `analyzers/ngrams/test_ngram_stats.py` - N-gram statistics analyzer tests
- `analyzers/hashtags/test_hashtags_analyzer.py` - Hashtag analyzer tests
- `analyzers/example/test_example_base.py` - Example analyzer tests
- `app/test_utils.py` - Utility function tests
- Test data directories co-located with analyzers (`test_data/` subdirectories)

## Development Patterns

### Context Pattern

All major operations use context objects for dependency injection:

- Eliminates direct dependencies between layers
- Enables easy testing with mock contexts
- Provides clear interfaces between components

### Interface-First Design

Analyzers define interfaces before implementation:

- Declarative input/output schemas
- Parameter definitions with types and defaults
- Clear separation between primary, secondary, and web analyzers

### Parquet-Centric Architecture

All data flows through Parquet files:

- Efficient columnar operations
- Schema validation and type safety
- Cross-analyzer data sharing
