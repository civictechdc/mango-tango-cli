# Core Domain Symbols

> **Note**: This reference is generated from semantic code analysis and reflects the actual codebase structure.

## Application Layer (`app/`)

### `App` class - `app/app.py:10`

Main application controller and workspace orchestrator

- `context: AppContext` - Dependency injection container
- `list_projects() -> list[ProjectModel]` - Retrieve all projects
- `create_project(name, input_file) -> ProjectModel` - Initialize new project
- `file_selector_state() -> AppFileSelectorStateManager` - File picker state

### `AppContext` class - `app/app_context.py`

Application-wide dependency injection container

- Provides storage, analyzer suite, and core services
- Used throughout the application for accessing shared resources

### `ProjectContext` class - `app/project_context.py`

Project-specific operations and column semantic mapping

- Handles data preprocessing and column type resolution
- Maps user data columns to analyzer requirements
- `UserInputColumn` - Column metadata with semantic types

### `AnalysisContext` class - `app/analysis_context.py`

Analysis execution environment

- `AnalysisRunProgressEvent` - Progress tracking for long-running analyses
- Provides file paths, preprocessing functions, and progress callbacks

## Storage Layer (`storage/`)

### `Storage` class - `storage/__init__.py:60`

Main data persistence and workspace management

**Project Management**:

- `init_project(name, input_path) -> ProjectModel` - Create new project
- `list_projects() -> list[ProjectModel]` - List all projects
- `get_project(project_id) -> ProjectModel` - Retrieve project by ID
- `delete_project(project_id)` - Remove project and data
- `rename_project(project_id, new_name)` - Update project name

**Data Operations**:

- `load_project_input(project_id) -> polars.DataFrame` - Load project data
- `get_project_input_stats(project_id) -> TableStats` - Data preview/stats
- `save_project_primary_outputs(project_id, outputs)` - Store analysis results
- `save_project_secondary_outputs(project_id, outputs)` - Store processed results

**Analysis Management**:

- `init_analysis(project_id, interface, name, params) -> AnalysisModel`
- `list_project_analyses(project_id) -> list[AnalysisModel]`
- `save_analysis(analysis) -> AnalysisModel` - Persist analysis state
- `delete_analysis(project_id, analysis_id)` - Remove analysis

**Export Operations**:

- `export_project_primary_output(project_id, format, output_path)`
- `export_project_secondary_output(project_id, analysis_id, format, output_path)`

### Data Models

- `ProjectModel` - Project metadata, configuration, column mappings
- `AnalysisModel` - Analysis metadata, parameters, execution state
- `SettingsModel` - User preferences and application configuration
- `FileSelectionState` - File picker UI state
- `TableStats` - Data statistics and preview information

## View Layer (`components/`)

### `ViewContext` class - `components/context.py`

UI state management and terminal context

- Manages terminal interface state and application context
- Coordinates between terminal UI and application logic

### Core UI Functions

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

## Common Utilities

### Logging System (`app/logger.py`)

Application-wide structured JSON logging with configurable levels and automatic rotation.

**Core Functions**:

- `setup_logging(log_file_path: Path, level: int = logging.INFO)` - Configure application logging
- `get_logger(name: str) -> logging.Logger` - Get logger instance for module

**Features**:

- Dual handlers: console (ERROR+) and file (INFO+)
- JSON-formatted structured logs with timestamps and context
- Automatic log rotation (10MB files, 5 backups)
- CLI-configurable log levels via `--log-level` flag
- Log location: `~/.local/share/MangoTango/logs/mangotango.log`

### Memory Management (`app/utils.py`)

- `MemoryManager` - Memory-aware processing with auto-detection
  - **Auto-detection**: `MemoryManager()` - Detects system RAM and sets optimal limits
  - **Manual override**: `MemoryManager(max_memory_gb=8.0)` - Custom memory limits
  - **System-specific allocation**: 20-40% of total RAM based on system capacity
  - **Pressure monitoring**: `check_memory_pressure()` - Real-time memory usage tracking
  - **Adaptive scaling**: Dynamic chunk size adjustment based on memory availability

### Data Processing (`app/utils.py`)

- `parquet_row_count(path) -> int` - Efficient row counting for large files

### Storage Utilities (`storage/__init__.py`)

- `collect_dataframe_chunks(paths) -> polars.DataFrame` - Combine multiple parquet files
- `TableStats` - Data statistics and preview generation

### File Management (`storage/file_selector.py`)

- `FileSelectorStateManager` - File picker state persistence
- `AppFileSelectorStateManager` - Application-specific file selection
