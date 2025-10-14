# Mango Tango CLI - AI Context Documentation

## Repository Overview

**Mango Tango CLI** is a Python terminal-based tool for social media data
analysis and visualization. It provides a modular, extensible architecture
that separates core application logic from analysis modules, ensuring
consistent UX while allowing easy contribution of new analyzers.

### Purpose & Domain

- **Social Media Analytics**: Hashtag analysis, n-gram analysis, temporal
  patterns, user coordination
- **Modular Architecture**: Clear separation between data import/export,
  analysis, and presentation
- **Interactive Workflows**: Terminal-based UI with web dashboard capabilities
- **Extensible Design**: Plugin-like analyzer system for easy expansion

### Tech Stack

- **Core**: Python 3.12, Inquirer (CLI), TinyDB (metadata)
- **Data**: Polars/Pandas, PyArrow, Parquet files
- **Text Processing**: Unicode tokenizer service with scriptio continua support (character-level for CJK/Thai/Southeast Asian scripts, word-level for Latin/Arabic scripts)
- **Web**: Dash, Shiny for Python, Plotly
- **Package Manager**: UV (modern Python package manager)
- **Dev Tools**: Black, isort, pytest, PyInstaller

### Project Structure

UV workspace monorepo with 8 packages:

```bash
packages/
├── core/                    # cibmangotree - Main application
├── importing/              # cibmangotree-importing - Data I/O
├── services/               # cibmangotree-services - Shared services
├── testing/                # cibmangotree-testing - Testing utilities
└── analyzers/              # Analysis modules (plugins)
    ├── hashtags/           # Hashtag analysis
    ├── ngrams/             # N-gram analysis
    ├── temporal/           # Temporal patterns
    └── example/            # Example analyzer template
```

## Semantic Code Structure

### Entry Points

- `packages/core/src/cibmangotree/__main__.py` - Main application bootstrap
- `uv run cibmangotree` - Standard execution command

### Core Architecture (MVC-like)

- **Application Layer** (`packages/core/src/cibmangotree/app/`): Workspace logic, analysis orchestration
- **View Layer** (`packages/core/src/cibmangotree/components/`): Terminal UI components using inquirer
- **Model Layer** (`packages/core/src/cibmangotree/storage/`): Data persistence, project/analysis models

### Domain Separation

1. **Core Domain**: Application, Terminal Components, Storage IO (`packages/core/`)
2. **Edge Domain**: Data import/export (`packages/importing/`), preprocessing
3. **Content Domain**: Analyzers (`packages/analyzers/`), web presenters

### Key Data Flow

1. Import (CSV/Excel) → Parquet → Semantic preprocessing
2. Primary Analysis → Secondary Analysis → Web Presentation
3. Export → User-selected formats (XLSX, CSV, etc.)

## Key Concepts

### Analyzer System

- **Primary Analyzers**: Core data processing (hashtags, ngrams, temporal)
- **Secondary Analyzers**: User-friendly output transformation
- **Web Presenters**: Interactive dashboards using Dash/Shiny
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

1. **Setup**: See @.ai-context/setup-guide.md
2. **Architecture**: See @.ai-context/architecture-overview.md
3. **Symbol Reference**: See @.ai-context/symbol-reference.md
4. **Development Guide**: See @docs/dev-guide.md

### For AI Assistants

- **Claude Code users**: See @CLAUDE.md
- **Cursor users**: See @.cursorrules

## External Dependencies

### Data Processing

- `polars` - Primary data processing library
- `pandas` - Secondary support for Plotly integration
- `pyarrow` - Parquet file format support

### Web Framework

- `dash` - Interactive web dashboards
- `shiny` - Python Shiny for modern web UIs
- `plotly` - Visualization library

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
