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
- `ngrams` - `analyzers/ngrams/main.py:main()` - N-gram generation and tokenization
- `temporal` - `analyzers/temporal/main.py:main()` - Time-based aggregation
- `time_coordination` - `analyzers/time_coordination/main.py:main()` - User coordination analysis

**Secondary Analyzers** (result transformation):

- `ngram_stats` - `analyzers/ngram_stats/main.py:main()` - N-gram statistics calculation
- `hashtags_web/analysis.py:secondary_analyzer()` - Hashtag summary statistics

**Web Presenters** (interactive dashboards):

- `hashtags_web` - `analyzers/hashtags_web/factory.py:factory()` - Hashtag dashboard
- `ngram_web` - `analyzers/ngram_web/factory.py:factory()` - N-gram exploration dashboard
- `temporal_barplot` - `analyzers/temporal_barplot/factory.py:factory()` - Temporal visualization

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

- Primary analyzer testing framework
- Secondary analyzer testing framework
- Test data management utilities

### Example Tests

- `analyzers/hashtags/test_hashtags_analyzer.py` - Hashtag analyzer tests
- `analyzers/example/test_example_base.py` - Example analyzer tests
- Test data directories co-located with analyzers

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
