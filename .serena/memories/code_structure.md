# Code Structure

## Entry Point

- `mangotango.py` - Main entry point, bootstraps the application with Storage, App, and terminal components

## Core Modules

### App (`app/`)

- `app.py` - Main App class with workspace capabilities
- `app_context.py` - AppContext class for dependency injection
- `project_context.py` - ProjectContext for project-specific operations
- `analysis_context.py` - AnalysisContext and AnalysisRunProgressEvent for analysis execution
- `analysis_output_context.py` - Context for handling analysis outputs
- `analysis_webserver_context.py` - Context for web server operations
- `settings_context.py` - SettingsContext for configuration management
- `utils.py` - Utility functions including `parquet_row_count()` and enhanced tokenization
- `test_utils.py` - Tests for utility functions

### Components (`components/`)

Terminal UI components using inquirer for interactive flows:

- `main_menu.py` - Main application menu
- `splash.py` - Application splash screen
- `new_project.py` - Project creation flow
- `select_project.py` - Project selection interface
- `project_main.py` - Project main menu
- `new_analysis.py` - Analysis creation flow
- `select_analysis.py` - Analysis selection interface
- `analysis_main.py` - Analysis main menu
- `analysis_params.py` - Parameter customization interface
- `analysis_web_server.py` - Web server management
- `export_outputs.py` - Output export functionality
- `context.py` - ViewContext class for UI state

### Storage (`storage/`)

- `__init__.py` - Storage class, models (ProjectModel, AnalysisModel, etc.)
- `file_selector.py` - File selection state management

### Terminal Tools (`terminal_tools/`)

Enhanced terminal utilities and **sophisticated progress reporting system**:

- `progress.py` - **Hierarchical progress reporting system**
  - See `progress_reporting_architecture` memory for detailed documentation
  - `ProgressManager` - Main progress manager with sub-step support
  - `ProgressReporter` - Basic multiprocess progress reporting
  - `AdvancedProgressReporter` - tqdm-based progress with ETA
- `prompts.py` - Interactive terminal prompts and file selection
- `utils.py` - Terminal utilities (clear, ANSI support, etc.)
- `test_progress.py` - Comprehensive tests for progress reporting (68+ tests)

### Analyzers (`analyzers/`)

**Reorganized modular analysis system:**

#### Core Analyzers

- `__init__.py` - Main analyzer suite registration
- `example/` - Example analyzer implementation
- `hashtags/` - Hashtag analysis (primary analyzer)
- `hashtags_web/` - Hashtag web dashboard (web presenter)
- `temporal/` - Temporal analysis (primary analyzer)
- `temporal_barplot/` - Temporal visualization (web presenter)
- `time_coordination/` - Time coordination analysis

#### N-gram Analysis Hierarchy

- `ngrams/` - **Hierarchically organized n-gram analysis system**
  - `ngrams_base/` - **Primary analyzer with enhanced progress reporting**
    - `main.py` - Enhanced with streaming optimization and hierarchical progress
    - `interface.py` - Input/output schema definitions
    - **Progress Integration**: Uses ProgressManager with hierarchical sub-steps for write operations
  - `ngram_stats/` - **Secondary analyzer**
    - `main.py` - Statistics calculation with chunked processing
    - `interface.py` - Statistics interface definition
  - `ngram_web/` - **Web presenter**
    - `factory.py` - Dashboard creation with word matching
    - `interface.py` - Web interface definition
  - `test_data/` - **Test files co-located with analyzers**
  - `test_ngrams_base.py` - **Comprehensive primary analyzer tests**
  - `test_ngram_stats.py` - **Secondary analyzer tests**

### Testing Framework (`testing/`)

**Comprehensive testing infrastructure:**

- `testdata.py` - **Test data management classes**
  - `TestData`, `FileTestData`, `CsvTestData`, `JsonTestData`
  - `ExcelTestData`, `ParquetTestData`, `PolarsTestData`
- `context.py` - **Mock context framework**
  - `TestPrimaryAnalyzerContext`, `TestSecondaryAnalyzerContext`
  - `TestInputColumnProvider`, `TestTableReader`, `TestOutputWriter`
- `testers.py` - **Standardized test execution**
  - `test_primary_analyzer()`, `test_secondary_analyzer()`
- `comparers.py` - **DataFrame comparison utilities**
  - `compare_dfs()` for precise test validation

### Importing (`importing/`)

- `importer.py` - Base Importer and ImporterSession classes
- `csv.py` - CSV import implementation
- `excel.py` - Excel import implementation

## Key Architectural Patterns

### Domain Separation

- **Core**: App, Components, Storage, Terminal Tools
- **Edge**: Importers, Testing framework
- **Content**: Analyzers (primary, secondary, web presenters)

### Hierarchical Organization

- **N-gram analyzers** organized into logical hierarchy
- **Testing framework** provides comprehensive mock contexts
- **Progress reporting** supports nested sub-steps (see `progress_reporting_architecture` memory)

### Enhanced Features

- **Streaming optimization** for large dataset processing
- **Hierarchical progress reporting** eliminates silent processing periods
- **Comprehensive testing** with standardized frameworks
- **Memory-efficient operations** with chunked processing

## Related Memories

- `progress_reporting_architecture` - Detailed documentation of the hierarchical progress reporting system
- `analyzer_architecture` - Deep dive into analyzer system design
- `project_overview` - High-level project understanding
