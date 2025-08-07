# Symbol Reference Guide

> **Note**: This reference is generated from semantic code analysis and reflects the actual codebase structure. Update as the codebase evolves.

## Core Domain Objects

### Application Layer (`app/`)

#### `App` class - `app/app.py:10`

Main application controller and workspace orchestrator

- `context: AppContext` - Dependency injection container
- `list_projects() -> list[ProjectModel]` - Retrieve all projects
- `create_project(name, input_file) -> ProjectModel` - Initialize new project
- `file_selector_state() -> AppFileSelectorStateManager` - File picker state

#### `AppContext` class - `app/app_context.py`

Application-wide dependency injection container

- Provides storage, analyzer suite, and core services
- Used throughout the application for accessing shared resources

#### `ProjectContext` class - `app/project_context.py`

Project-specific operations and column semantic mapping

- Handles data preprocessing and column type resolution
- Maps user data columns to analyzer requirements
- `UserInputColumn` - Column metadata with semantic types

#### `AnalysisContext` class - `app/analysis_context.py`

Analysis execution environment

- `AnalysisRunProgressEvent` - Progress tracking for long-running analyses
- Provides file paths, preprocessing functions, and progress callbacks

### Storage Layer (`storage/`)

#### `Storage` class - `storage/__init__.py:60`

Main data persistence and workspace management

Project Management:

- `init_project(name, input_path) -> ProjectModel` - Create new project
- `list_projects() -> list[ProjectModel]` - List all projects
- `get_project(project_id) -> ProjectModel` - Retrieve project by ID
- `delete_project(project_id)` - Remove project and data
- `rename_project(project_id, new_name)` - Update project name

Data Operations:

- `load_project_input(project_id) -> polars.DataFrame` - Load project data
- `get_project_input_stats(project_id) -> TableStats` - Data preview/stats
- `save_project_primary_outputs(project_id, outputs)` - Store analysis results
- `save_project_secondary_outputs(project_id, outputs)` - Store processed results

Analysis Management:

- `init_analysis(project_id, interface, name, params) -> AnalysisModel`
- `list_project_analyses(project_id) -> list[AnalysisModel]`
- `save_analysis(analysis) -> AnalysisModel` - Persist analysis state
- `delete_analysis(project_id, analysis_id)` - Remove analysis

Export Operations:

- `export_project_primary_output(project_id, format, output_path)`
- `export_project_secondary_output(project_id, analysis_id, format, output_path)`

#### Data Models

- `ProjectModel` - Project metadata, configuration, column mappings
- `AnalysisModel` - Analysis metadata, parameters, execution state
- `SettingsModel` - User preferences and application configuration
- `FileSelectionState` - File picker UI state
- `TableStats` - Data statistics and preview information

### View Layer (`components/`)

#### `ViewContext` class - `components/context.py`

UI state management and terminal context

- Manages terminal interface state and application context
- Coordinates between terminal UI and application logic

#### Core UI Functions

- `main_menu(ViewContext)` - Application entry point menu
- `splash()` - Application branding and welcome screen
- `new_project(ViewContext)` - Project creation workflow
- `select_project(ViewContext)` - Project selection interface
- `project_main(ViewContext)` - Project management menu
- `new_analysis(ViewContext)` - Analysis configuration workflow
- `select_analysis(ViewContext)` - Analysis selection interface
- `analysis_main(ViewContext)` - Analysis management menu
- `customize_analysis(ViewContext, AnalysisModel)` - Parameter customization
- `analysis_web_server(ViewContext, AnalysisModel)` - Web server management
- `export_outputs(ViewContext, ProjectModel)` - Export workflow

## Service Layer

### Data Import (`importing/`)

#### `Importer` base class - `importing/importer.py`

Base interface for data importers

- `ImporterSession` - Stateful import process management
- `SessionType` - Enum for import session types

#### Concrete Importers

- `CSVImporter` - `importing/csv.py` - CSV file import with encoding detection
- `ExcelImporter` - `importing/excel.py` - Excel file import with sheet selection

### Analyzer System (`analyzers/`)

#### Built-in Analyzers

**Primary Analyzers** (core data processing):

- `hashtags` - `analyzers/hashtags/main.py:main()` - Hashtag extraction and analysis
- `ngrams_base` - `analyzers/ngrams/ngrams_base/main.py:main()` - N-gram generation with enhanced progress reporting
  - Enhanced write functions: `_enhanced_write_message_ngrams()`, `_enhanced_write_ngram_definitions()`, `_enhanced_write_message_metadata()`
  - Streaming optimization: `_stream_unique_batch_accumulator()`, `_stream_unique_to_temp_file()`
  - Vectorized n-gram generation: `_generate_ngrams_vectorized()`, `_generate_ngrams_simple()`
- `temporal` - `analyzers/temporal/main.py:main()` - Time-based aggregation
- `time_coordination` - `analyzers/time_coordination/main.py:main()` - User coordination analysis

**Secondary Analyzers** (result transformation):

- `ngram_stats` - `analyzers/ngrams/ngram_stats/main.py:main()` - N-gram statistics calculation
  - Chunked processing: `_process_ngram_chunk()`, `_create_sample_full_report_row()`
- `hashtags_web/analysis.py:secondary_analyzer()` - Hashtag summary statistics

**Web Presenters** (interactive dashboards):

- `hashtags_web` - `analyzers/hashtags_web/factory.py:factory()` - Hashtag dashboard
- `ngram_web` - `analyzers/ngrams/ngram_web/factory.py:factory()` - N-gram exploration dashboard
  - Word matching: `create_word_matcher()`
- `temporal_barplot` - `analyzers/temporal_barplot/factory.py:factory()` - Temporal visualization

#### Performance Optimization Components

**Memory Management** (`analyzers/ngrams/memory_strategies.py`):

- `ExternalSortUniqueExtractor` - External sorting for memory-constrained n-gram processing
  - Disk-based unique extraction with configurable chunk sizes
  - Temporary file management and cleanup
  - Memory-aware processing with fallback strategies
- `extract_unique_external_sort()` - High-level function for external sorting operations

**Fallback Processors** (`analyzers/ngrams/fallback_processors.py`):

- `generate_ngrams_disk_based()` - Disk-based n-gram generation for large datasets
- `_generate_ngrams_minimal_memory()` - Minimal memory approach for constrained systems
- `stream_unique_memory_optimized()` - Memory-optimized streaming unique extraction

#### Analyzer Registration

- `analyzers.suite` - `analyzers/__init__.py` - Central registry of all analyzers

## Entry Points

### Main Application

- `mangotango.py` - Application bootstrap and initialization
  - `freeze_support()` - Multiprocessing setup
  - `enable_windows_ansi_support()` - Terminal color support
  - Storage initialization with app metadata
  - Component orchestration (splash, main_menu)

### Module Entry Point

- `python -m mangotango` - Standard execution command
- `python -m mangotango --noop` - No-operation mode for testing

## Integration Points

### External Libraries Integration

- **Polars**: Primary data processing engine
- **Dash**: Web dashboard framework integration
- **Shiny**: Modern web UI framework integration
- **TinyDB**: Lightweight JSON database
- **Inquirer**: Interactive terminal prompts

### File System Integration

- **Parquet**: Native data format for all analysis data
- **Workspace**: Project-based file organization
- **Exports**: Multi-format output generation (XLSX, CSV, Parquet)

### Web Framework Hooks

- `AnalysisWebServerContext` - Web server lifecycle management
- Dashboard factory pattern for creating web applications
- Background server process management

### Terminal Tools (`terminal_tools/`)

#### Enhanced Progress Reporting System

- `RichProgressManager` - `terminal_tools/progress.py` - Hierarchical progress manager with Rich integration
  - **Main step management**:
    - `add_step(step_id, title, total=None)` - Add progress steps
    - `start_step(step_id)`, `update_step(step_id, progress)`, `complete_step(step_id)` - Step lifecycle
    - `fail_step(step_id, error_msg=None)` - Error handling
  - **Hierarchical sub-step management**:
    - `add_substep(parent_step_id, substep_id, description, total=None)` - Add sub-steps
    - `start_substep(parent_step_id, substep_id)` - Start/activate sub-steps  
    - `update_substep(parent_step_id, substep_id, progress)` - Update sub-step progress
    - `complete_substep(parent_step_id, substep_id)` - Mark sub-steps complete
    - `fail_substep(parent_step_id, substep_id, error_msg=None)` - Sub-step error handling
  - **Internal methods**:
    - `_update_parent_progress(parent_step_id)` - Calculate parent progress from sub-steps
    - `_update_display()` - Rich terminal display with hierarchical visualization

- `ProgressReporter` - `terminal_tools/progress.py` - Basic multiprocess progress reporting
- `AdvancedProgressReporter` - `terminal_tools/progress.py` - tqdm-based progress with ETA calculation
- `ChecklistProgressManager` - Backward compatibility alias for `RichProgressManager`

#### Other Terminal Utilities

- `file_selector()` - `terminal_tools/prompts.py` - Interactive file selection
- `clear_terminal()` - `terminal_tools/utils.py` - Terminal screen clearing
- `enable_windows_ansi_support()` - `terminal_tools/utils.py` - Windows terminal color support

## Common Utilities

### Logging System (`app/logger.py`)

Application-wide structured JSON logging with configurable levels and automatic rotation.

**Core Functions:**

- `setup_logging(log_file_path: Path, level: int = logging.INFO)` - Configure application logging
- `get_logger(name: str) -> logging.Logger` - Get logger instance for module

**Features:**

- Dual handlers: console (ERROR+) and file (INFO+)
- JSON-formatted structured logs with timestamps and context
- Automatic log rotation (10MB files, 5 backups)
- CLI-configurable log levels via `--log-level` flag
- Log location: `~/.local/share/MangoTango/logs/mangotango.log`

**Usage Pattern:**

```python
from app.logger import get_logger
logger = get_logger(__name__)
logger.info("Message", extra={"context": "value"})
```

### Data Processing (`app/utils.py`)

- `parquet_row_count(path) -> int` - Efficient row counting for large files

### Storage Utilities (`storage/__init__.py`)

- `collect_dataframe_chunks(paths) -> polars.DataFrame` - Combine multiple parquet files
- `TableStats` - Data statistics and preview generation

### File Management (`storage/file_selector.py`)

- `FileSelectorStateManager` - File picker state persistence
- `AppFileSelectorStateManager` - Application-specific file selection

## Testing Infrastructure

### Test Utilities (`testing/`)

#### Test Data Management

- `TestData` - `testing/testdata.py` - Base class for test data handling
- `FileTestData` - File-based test data with path management
- `CsvTestData` - CSV file testing with configurable parsing (`CsvConfig`)
- `JsonTestData` - JSON file testing support
- `ExcelTestData` - Excel file testing with sheet selection
- `ParquetTestData` - Parquet file testing for analyzer outputs
- `PolarsTestData` - In-memory Polars DataFrame testing

#### Test Context Framework

- `TestPrimaryAnalyzerContext` - `testing/context.py` - Mock context for primary analyzer testing
- `TestSecondaryAnalyzerContext` - Mock context for secondary analyzer testing
- `TestInputColumnProvider` - Column mapping testing support
- `TestTableReader` - Mock data reader for testing
- `TestOutputWriter` - Mock output writer for testing
- `TestOutputReaderGroupContext` - Multi-output testing context

#### Test Execution Framework

- `test_primary_analyzer()` - `testing/testers.py` - Standardized primary analyzer testing
- `test_secondary_analyzer()` - Standardized secondary analyzer testing
- `compare_dfs()` - `testing/comparers.py` - DataFrame comparison utilities

#### Progress Reporting Tests

- `TestRichProgressManager` - `terminal_tools/test_progress.py` - Basic progress manager tests
- `TestRichProgressManagerHierarchical` - Comprehensive hierarchical progress testing
  - 18 test methods covering substep functionality, validation, error handling, performance
- `TestProgressReporter` - Basic progress reporter tests
- `TestAdvancedProgressReporter` - Advanced progress reporter with tqdm integration

#### Performance Testing Infrastructure

**Performance Testing Suite** (`testing/performance/`):

- `test_performance_benchmarks.py` - Core performance benchmarks for analyzer operations
- `test_enhanced_benchmarks.py` - Enhanced benchmarking with memory profiling
- `test_chunking_optimization.py` - Chunking strategy validation and performance tests
- `test_integration_validation.py` - Integration tests for performance optimizations
- `run_performance_tests.py` - Performance test runner with configurable parameters
- `run_enhanced_benchmarks.py` - Enhanced benchmark execution with detailed metrics

### Example Tests

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
