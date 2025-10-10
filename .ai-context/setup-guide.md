# Setup Guide

## Prerequisites

### Required Software

- **Python 3.12** - Required for all features to work correctly
- **Git** - For version control and contributing
- **Terminal/Command Line** - Application runs in terminal interface
- **UV** - Python package manager (installed automatically by bootstrap scripts)

### System Requirements

- **Operating System**: Windows (PowerShell), macOS, Linux
- **Memory**: 4GB+ RAM (for processing large datasets)
- **Storage**: 1GB+ free space (for project data and virtual environment)

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/CIB-Mango-Tree/mango-tango-cli.git
cd mango-tango-cli
```

### 2. Bootstrap Development Environment

The bootstrap script installs UV (if not present) and sets up the entire development environment automatically.

**macOS/Linux**:

```bash
./bootstrap.sh
```

**Windows (PowerShell)**:

```powershell
./bootstrap.ps1
```

The bootstrap script will:

- Install UV package manager (if not already installed)
- Create and manage `.venv/` virtual environment automatically
- Install all workspace dependencies via `uv sync --all-extras`
- Verify installation by importing the application

### 3. Verify Installation

```bash
uv run cibmangotree --noop
```

Should output: "No-op flag detected. Exiting successfully."

## Development Environment Setup

### UV Workflow

This project uses **UV** as the primary package manager. UV automatically manages the virtual environment and dependencies.

**Key UV Commands**:

```bash
# Install/sync all dependencies
uv sync

# Install with extras (docs, dev, etc.)
uv sync --all-extras

# Run the application
uv run cibmangotree

# Run tests
uv run pytest

# Format code
uv run black .
uv run isort .

# Build executable
uv run pyinstaller pyinstaller.spec
```

**Virtual Environment Management**:

- UV creates and manages `.venv/` automatically
- No need to manually activate the virtual environment when using `uv run`
- For manual activation (if needed):
  - macOS/Linux: `source .venv/bin/activate`
  - Windows: `.venv\Scripts\activate`

### Dependencies Overview

All dependencies are defined in `pyproject.toml` files within the monorepo workspace.

**Workspace Structure** (`pyproject.toml`):

```toml
[tool.uv.workspace]
members = [
    "packages/core",              # cibmangotree - main application
    "packages/testing",           # cibmangotree-testing - testing utilities
    "packages/tokenizers/basic",  # cibmangotree-tokenizer-basic
    "packages/analyzers/example", # cibmangotree-analyzers-example
    "packages/analyzers/hashtags",
    "packages/analyzers/ngrams",
    "packages/analyzers/temporal",
    "packages/analyzers/time_coordination",
]
```

**Development Dependencies**:

```toml
[dependency-groups]
dev = [
    "black>=24.10.0",
    "isort>=5.13.2",
    "pytest>=8.3.4",
    "pytest-benchmark>=5.1.0",
    "pyinstaller>=6.14.1",
    "pyarrow-stubs>=17.13",
]
```

**Production Dependencies**: Defined in individual package `pyproject.toml` files:

- `polars` - Primary data processing
- `pydantic` - Data validation and models
- `inquirer` - Interactive terminal prompts
- `tinydb` - Lightweight JSON database
- `dash` - Web dashboard framework
- `shiny` - Modern web UI framework
- `plotly` - Data visualization
- `XlsxWriter` - Excel export functionality

### Code Formatting Setup

The project uses automatic code formatting:

- **Black**: Code style and formatting
- **isort**: Import organization
- **UV**: Runs formatters via `uv run`

**Manual formatting**:

```bash
uv run isort .
uv run black .
```

### Project Structure

After installation, your project structure should be:

```bash
mango-tango-cli/
├── .venv/                   # UV-managed virtual environment
├── packages/                # Monorepo workspace packages
│   ├── core/               # cibmangotree - main application
│   │   └── src/cibmangotree/
│   │       ├── app/        # Application logic & terminal UI
│   │       ├── storage/    # Data persistence layer
│   │       ├── components/ # Terminal UI components
│   │       └── analyzers.py # Analyzer discovery & registry
│   ├── testing/            # cibmangotree-testing - testing utilities
│   ├── tokenizers/         # Tokenizer implementations
│   │   └── basic/          # cibmangotree-tokenizer-basic
│   └── analyzers/          # Analysis modules (plugins)
│       ├── example/        # cibmangotree-analyzers-example
│       ├── hashtags/       # cibmangotree-analyzers-hashtags
│       ├── ngrams/         # cibmangotree-analyzers-ngrams
│       ├── temporal/       # cibmangotree-analyzers-temporal
│       └── time_coordination/ # cibmangotree-analyzers-time-coordination
├── docs/                    # Documentation
├── .ai-context/            # AI assistant context
├── pyproject.toml          # Workspace configuration & tool settings
├── uv.lock                 # UV lock file (dependency resolution)
├── bootstrap.sh            # macOS/Linux setup script
└── bootstrap.ps1           # Windows setup script
```

## Database and Storage Setup

### Application Data Directory

The application automatically creates data directories:

- **macOS**: `~/Library/Application Support/MangoTango/`
- **Windows**: `%APPDATA%/Civic Tech DC/MangoTango/`
- **Linux**: `~/.local/share/MangoTango/`

### Database Initialization

- **TinyDB**: Automatically initialized on first run
- **Project Files**: Created in user data directory
- **Parquet Files**: Used for all analysis data storage

No manual database setup required.

## Running the Application

### Basic Usage

```bash
# Start the application (UV manages venv automatically)
uv run cibmangotree
```

### Development Mode

```bash
# Run with debugging/development flags
uv run cibmangotree --noop  # Test mode, exits immediately
```

### Manual Virtual Environment Activation (Optional)

If you prefer to activate the virtual environment manually:

```bash
# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Then run without 'uv run' prefix
cibmangotree
pytest
black .
```

## Testing Setup

### Run Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest packages/analyzers/hashtags/tests/test_hashtags_analyzer.py

# Run with verbose output
uv run pytest -v

# Run specific test function
uv run pytest packages/analyzers/hashtags/tests/test_hashtags_analyzer.py::test_gini

# Stop on first failure
uv run pytest -x

# Run tests matching a pattern
uv run pytest -k "hashtag"
```

### Test Data

- Test data is co-located with analyzers in `tests/` directories
- Each analyzer includes its own test files and test data
- Tests use sample data to verify functionality

## Build Setup (Optional)

### Executable Building

```bash
# Build standalone executable
uv run pyinstaller pyinstaller.spec

# Output will be in dist/ directory
```

### Build Requirements

- Included in development dependencies
- Used primarily for release distribution
- Not required for development

## IDE Integration

### Recommended IDE Settings

**VS Code** (`.vscode/` configuration):

- Python interpreter: `./.venv/bin/python`
- Black formatter integration
- isort integration
- pytest test discovery

**PyCharm**:

- Interpreter: Project virtual environment (`.venv/`)
- Code style: Black
- Import optimizer: isort

### Git Configuration

**Git Flow**:

- Branch from `main` for new features
- Feature branches: `feature/name` or `username/issue-description`
- Bug fixes: `bugfix/name`

## Troubleshooting

### Common Issues

**Python Version Error**:

```bash
# Check Python version
python --version

# If not 3.12, install Python 3.12 and re-run bootstrap
# UV will detect the correct Python version
./bootstrap.sh  # macOS/Linux
./bootstrap.ps1 # Windows
```

**UV Not Found**:

```bash
# Install UV manually (if bootstrap script fails)
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell):
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Then run:
uv sync --all-extras
```

**Import Errors**:

```bash
# Re-sync dependencies
uv sync --all-extras

# If issues persist, remove .venv and re-bootstrap
rm -rf .venv
./bootstrap.sh  # macOS/Linux
./bootstrap.ps1 # Windows
```

**Formatting Errors in CI**:

```bash
# Run formatters locally before committing
uv run isort .
uv run black .
```

**Test Failures**:

```bash
# Ensure test data is present
ls packages/analyzers/*/tests/test_data/

# Check if specific analyzer tests pass
uv run pytest packages/analyzers/hashtags/ -v
```

### Environment Variables

**Optional Configuration**:

- `MANGOTANGO_DATA_DIR` - Override default data directory
- `MANGOTANGO_LOG_LEVEL` - Set logging verbosity

### Performance Optimization

**Large Dataset Handling**:

- Increase system memory allocation
- Use Parquet files for efficient data processing
- Monitor disk space in data directory

**Development Performance**:

- Use `uv run pytest -x` to stop on first failure
- Use `uv run pytest -k pattern` to run specific test patterns
- Use `uv run pytest --lf` to re-run last failed tests

## UV Workspace Deep Dive

### Understanding UV Workspaces

UV manages this project as a **monorepo workspace** with multiple packages:

- **Workspace root**: `pyproject.toml` defines workspace members
- **Package members**: Each package has its own `pyproject.toml`
- **Shared dependencies**: Defined at workspace root
- **Lock file**: `uv.lock` ensures reproducible builds

### Adding New Packages

To add a new analyzer or package to the workspace:

1. Create package directory: `packages/analyzers/my-analyzer/`
2. Add `pyproject.toml` with package metadata
3. Add to workspace members in root `pyproject.toml`:

   ```toml
   [tool.uv.workspace]
   members = [
       # ... existing members
       "packages/analyzers/my-analyzer",
   ]
   ```

4. Run `uv sync` to update workspace

### Dependency Management

**Add production dependency to a package**:

```bash
# Navigate to package directory
cd packages/analyzers/hashtags/

# Add dependency
uv add polars
```

**Add development dependency to workspace**:

Edit root `pyproject.toml`:

```toml
[dependency-groups]
dev = [
    "black>=24.10.0",
    "your-new-dev-tool>=1.0.0",
]
```

Then run: `uv sync`

### UV Lock File

- `uv.lock` contains exact versions of all dependencies
- Committed to version control for reproducibility
- Updated automatically when dependencies change
- Ensures consistent environments across all developers

## Quick Reference

### Essential Commands

```bash
# Setup
./bootstrap.sh              # Initial setup (macOS/Linux)
./bootstrap.ps1             # Initial setup (Windows)

# Development
uv run cibmangotree         # Run application
uv run pytest               # Run tests
uv run black .              # Format code
uv run isort .              # Organize imports

# Dependency management
uv sync                     # Sync dependencies
uv sync --all-extras        # Sync with all extras (dev, docs)
uv add package-name         # Add dependency to package

# Building
uv run pyinstaller pyinstaller.spec  # Build executable
```

### Directory Navigation

```bash
# Core application
packages/core/src/cibmangotree/

# Analyzers
packages/analyzers/hashtags/
packages/analyzers/ngrams/
packages/analyzers/temporal/

# Testing utilities
packages/testing/

# Tokenizers
packages/tokenizers/basic/

# Documentation
docs/
.ai-context/
```

### Getting Help

- **Development Guide**: `docs/dev-guide.md`
- **AI Context**: `.ai-context/README.md`
- **Architecture**: `.ai-context/architecture-overview.md`
- **UV Documentation**: <https://github.com/astral-sh/uv>
