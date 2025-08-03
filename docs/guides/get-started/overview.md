# Mango Tango CLI

## Repository Overview

**Mango Tango CLI** is a Python terminal-based tool for social media data
analysis and visualization. It provides a modular, extensible architecture
that separates core application logic from analysis modules, ensuring
consistent UX while allowing easy contribution of new analyzers.
The following documentation in this section is meant to provide a
general overview of how the codebase for the project is structured,
and to provide some context on patterns used throughout the project.

### Purpose & Domain

- **Social Media Analytics**: Hashtag analysis, n-gram analysis, temporal
  patterns, user coordination
- **Modular Architecture**: Clear separation between data import/export,
  analysis, and presentation
- **Interactive Workflows**: Terminal-based UI with web dashboard capabilities
- **Extensible Design**: Plugin-like analyzer system for easy expansion

### Tech Stack

- **Core**: Python 3.12, Inquirer (CLI), TinyDB (metadata), Starlette & Uvicorn (web-server)
- **Data**: Polars/Pandas, PyArrow, Parquet files
- **Web**: Dash, Shiny for Python, Plotly, React
- **Dev Tools**: Black, isort, pytest, PyInstaller

## Semantic Code Structure

### Entry Points

- `mangotango.py` - Main application bootstrap
- `python -m mangotango` - Standard execution command

### Core Architecture (MVC-like)

- **Application Layer** (`app/`): Workspace logic, analysis orchestration
- **View Layer** (`components/`): Terminal UI components using inquirer
- **Model Layer** (`storage/`): Data persistence, project/analysis models

### Domain Separation

1. **Core Domain**: Application, Terminal Components, Storage IO
2. **Edge Domain**: Data import/export (`importing/`), preprocessing
3. **Content Domain**: Analyzers (`analyzers/`), web presenters

### Key Data Flow

1. Import (CSV/Excel) → Parquet → Semantic preprocessing
2. Primary Analysis → Secondary Analysis → Web Presentation
3. Export → User-selected formats (XLSX, CSV, etc.)

## Key Concepts

### Analyzer System

- **Primary Analyzers**: Core data processing (hashtags, ngrams, temporal)
- **Secondary Analyzers**: User-friendly output transformation
- **Web Presenters**: Interactive dashboards using Dash/Shiny/React
  (Also used for providing data to backend APIs)
- **Interface Pattern**: Declarative input/output schema definitions

### Context Pattern

Dependency injection through context objects:

- `AppContext`: Application-wide dependencies
- `ViewContext`: UI state and terminal context
- `AnalysisContext`: Analysis execution environment
- Analyzer contexts: File paths, preprocessing, app hooks

### Data Semantics

- Column semantic types guide user in analysis selection
- Preprocessing maps user data to expected analyzer inputs
- Type-safe data models using Pydantic

## Development Patterns

### Code Organization

- Domain-driven module structure
- Interface-first analyzer design  
- Context-based dependency injection
- Test co-location with implementation

### Key Conventions

- Black + isort formatting (enforced by pre-commit)
- Type hints throughout (modern Python syntax)
- Parquet for data persistence
- Pydantic models for validation

## Getting Started

### For Development

1. **Setup**: See [Setup Guide](./installation.md)
2. **Contribution Workflow**: See [The Contribution Workflow Guide](./contributing.md)
3. **Development Guide**: See [The Development Guide](./architecture.md)

### For AI Assistants

- **Claude Code users**: See [CLAUDE.md](https://github.com/civictechdc/mango-tango-cli/tree/develop/CLAUDE.md) (includes Serena integration)
- **Cursor users**: See [.cursorrules](https://github.com/civictechdc/mango-tango-cli/tree/develop/.cursorrules)
- **Deep semantic analysis**: Explore [.serena/memories/](https://github.com/civictechdc/mango-tango-cli/tree/develop/.serena/memories)

### Quick References

- **Commands**: [.serena/memories/suggested_commands.md](https://github.com/civictechdc/mango-tango-cli/tree/develop/.serena/memories/suggested_commands.md)
- **Style Guide**: [.serena/memories/code_style_conventions.md](https://github.com/civictechdc/mango-tango-cli/tree/develop/.serena/memories/code_style_conventions.md)
- **Task Checklist**: [.serena/memories/task_completion_checklist.md](https://github.com/civictechdc/mango-tango-cli/tree/develop/.serena/memories/task_completion_checklist.md)

## External Dependencies

### Data Processing

- `polars` - Primary data processing library
- `pandas` - Secondary support for Plotly integration
- `pyarrow` - Parquet file format support

### Web Framework

- `dash` - Interactive web dashboards
- `shiny` - Python Shiny for modern web UIs
- `plotly` - Visualization library
- `React` - Stylized Interactive Dashboards for the end-user
- `Starlette` - Web Framework for providing the dashboards and handling backend logic
- `Uvicorn` - ASGI web-server that handles running the Starlette backend

### CLI & Storage

- `inquirer` - Interactive terminal prompts
- `tinydb` - Lightweight JSON database
- `platformdirs` - Cross-platform data directories

### Development

- `black` - Code formatter
- `isort` - Import organizer
- `pytest` - Testing framework
- `pyinstaller` - Executable building

## Project Status

- **License**: PolyForm Noncommercial License 1.0.0
- **Author**: CIB Mango Tree / Civic Tech DC
- **Branch Strategy**: feature branches → develop → main
- **CI/CD**: GitHub Actions for testing, formatting, builds
