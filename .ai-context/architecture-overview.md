# Architecture Overview

## High-Level Component Diagram

```mermaid
flowchart TD
    User[User] --> Terminal[Terminal Interface]
    Terminal --> App[Application Layer]
    App --> Storage[Storage Layer]

    App --> Importers[Data Importers]
    App --> Preprocessing[Semantic Preprocessor]
    App --> Analyzers[Analyzer System]

    Importers --> Parquet[(Parquet Files)]
    Preprocessing --> Parquet
    Analyzers --> Parquet

    Analyzers --> Primary[Primary Analyzers]
    Analyzers --> Secondary[Secondary Analyzers]
    Analyzers --> WebPresenters[Web Presenters]

    WebPresenters --> Dash[Dash Apps]
    WebPresenters --> Shiny[Shiny Apps]

    Storage --> TinyDB[(TinyDB)]
    Storage --> FileSystem[(File System)]
```

## Core Abstractions

### Application Layer (`app/`)

Central orchestration and workspace management

Key Classes:

- `App` - Main application controller, orchestrates all operations
- `AppContext` - Dependency injection container for application-wide services
- `ProjectContext` - Project-specific operations and column mapping
- `AnalysisContext` - Analysis execution environment and progress tracking
- `AnalysisOutputContext` - Handles analysis result management
- `AnalysisWebServerContext` - Web server lifecycle management
- `SettingsContext` - Configuration and user preferences

### View Layer (`components/`)

Terminal UI components using inquirer

Key Components:

- `ViewContext` - UI state management and terminal context
- `main_menu()` - Application entry point menu
- `splash()` - Application branding and welcome
- Menu flows: project selection, analysis creation, parameter customization
- Server management: web server lifecycle, export workflows

### Model Layer (`storage/`)

Data persistence and state management

Key Classes:

- `Storage` - Main storage controller, manages projects and analyses
- `ProjectModel` - Project metadata and configuration
- `AnalysisModel` - Analysis metadata, parameters, and state
- `SettingsModel` - User preferences and application settings
- `FileSelectionState` - File picker state management
- `TableStats` - Data statistics and preview information

## Data Flow Architecture

### Import → Analysis → Export Pipeline

```mermaid
sequenceDiagram
    participant User
    participant Terminal
    participant App
    participant Importer
    participant Preprocessor
    participant Analyzer
    participant WebServer

    User->>Terminal: Select data file
    Terminal->>App: Create project
    App->>Importer: Import CSV/Excel
    Importer->>App: Parquet file path
    App->>Preprocessor: Apply column semantics
    Preprocessor->>App: Processed data path
    User->>Terminal: Configure analysis
    Terminal->>App: Run analysis
    App->>Analyzer: Execute with context
    Analyzer->>App: Analysis results
    App->>WebServer: Start dashboard
    WebServer->>User: Interactive visualization
```

### Context-Based Dependency Injection

Each layer receives context objects containing exactly what it needs:

```python
# Analyzer Context Pattern
class AnalysisContext:
    input_path: Path           # Input parquet file
    output_path: Path          # Where to write results
    preprocessing: Callable    # Column mapping function
    progress_callback: Callable # Progress reporting
    parameters: dict           # User-configured parameters

class AnalysisWebServerContext:
    primary_output_path: Path
    secondary_output_paths: list[Path]
    dash_app: dash.Dash        # For dashboard creation
    server_config: dict
```

## Core Domain Patterns

### Analyzer Interface System

Declarative analysis definition

```python
# interface.py
interface = AnalyzerInterface(
    input=AnalyzerInput(
        columns=[
            AnalyzerInputColumn(
                name="author_id",
                semantic_type=ColumnSemantic.USER_ID,
                required=True
            )
        ]
    ),
    outputs=[
        AnalyzerOutput(
            name="hashtag_analysis",
            columns=[...],
            internal=False  # User-consumable
        )
    ],
    params=[
        AnalyzerParam(
            name="time_window",
            param_type=ParamType.TIME_BINNING,
            default="1D"
        )
    ]
)
```

### Three-Stage Analysis Pipeline

1. **Primary Analyzers** - Raw data processing
   - Input: Preprocessed parquet files
   - Output: Normalized analysis results
   - Examples: hashtag extraction, n-gram generation, temporal aggregation

2. **Secondary Analyzers** - Result transformation
   - Input: Primary analyzer outputs
   - Output: User-friendly reports and summaries
   - Examples: statistics calculation, trend analysis

3. **Web Presenters** - Interactive visualization
   - Input: Primary + secondary outputs
   - Output: Dash/Shiny web applications
   - Examples: interactive charts, data exploration interfaces

## Integration Points

### External Data Sources

- **CSV Importer**: Handles delimiter detection, encoding issues
- **Excel Importer**: Multi-sheet support, data type inference
- **File System**: Project directory structure, workspace management

### Web Framework Integration

- **Dash Integration**: Plotly-based interactive dashboards
- **Shiny Integration**: Modern Python web UI framework
- **Server Management**: Background process handling, port management

### Export Capabilities

- **XLSX Export**: Formatted Excel files with multiple sheets
- **CSV Export**: Standard comma-separated values
- **Parquet Export**: Native format for data interchange

## Key Architectural Decisions

### Parquet-Centric Data Flow

- All analysis data stored as Parquet files
- Enables efficient columnar operations with Polars
- Provides schema validation and compression
- Facilitates data sharing between analysis stages

### Context Pattern for Decoupling

- Eliminates direct dependencies between layers
- Enables testing with mock contexts
- Allows analyzer development without application knowledge
- Supports different execution environments (CLI, web, testing)

### Domain-Driven Module Organization

- Clear boundaries between core, edge, and content domains
- Enables independent development of analyzers
- Supports plugin-like extensibility
- Facilitates maintenance and testing

### Semantic Type System

- Guides users in column selection for analyses
- Enables automatic data validation and preprocessing
- Supports analyzer input requirements
- Provides consistent UX across different data sources
