# Setup Guide

## Prerequisites

### Required Software

- **Python 3.12** - Required for all features to work correctly
- **Git** - For version control and contributing
- **Terminal/Command Line** - Application runs in terminal interface

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

### 2. Create Virtual Environment

```bash
python -m venv venv
```

**Verify Python version**:

```bash
python --version  # Should show Python 3.12.x
```

### 3. Bootstrap Development Environment

**macOS/Linux**:

```bash
./bootstrap.sh
```

**Windows (PowerShell)**:

```powershell
./bootstrap.ps1
```

The bootstrap script will:

- Activate the virtual environment
- Install all dependencies from `requirements-dev.txt`
- Set up pre-commit hooks for code formatting

### 4. Verify Installation

```bash
python -m cibmangotree --noop
```

Should output: "No-op flag detected. Exiting successfully."

## Development Environment Setup

### Dependencies Overview

**Production Dependencies** (`requirements.txt`):

- `polars==1.9.0` - Primary data processing
- `pydantic==2.9.1` - Data validation and models
- `inquirer==3.4.0` - Interactive terminal prompts
- `tinydb==4.8.0` - Lightweight JSON database
- `dash==2.18.1` - Web dashboard framework
- `shiny==1.4.0` - Modern web UI framework
- `plotly==5.24.1` - Data visualization
- `XlsxWriter==3.2.0` - Excel export functionality

**Development Dependencies** (`requirements-dev.txt`):

- `black==24.10.0` - Code formatter
- `isort==5.13.2` - Import organizer
- `pytest==8.3.4` - Testing framework
- `pyinstaller==6.14.1` - Executable building

### Code Formatting Setup

The project uses automatic code formatting:

- **Black**: Code style and formatting
- **isort**: Import organization
- **Pre-commit hooks**: Automatic formatting on commit

**Manual formatting**:

```bash
isort .
black .
```

### Project Structure Setup

After installation, your project structure should be:

```bash
mango-tango-cli/
├── venv/                    # Virtual environment
├── .serena/                 # Serena semantic analysis
│   └── memories/           # Project knowledge base
├── docs/                    # Documentation
│   ├── ai-context/         # AI assistant context
│   └── dev-guide.md        # Development guide
├── app/                     # Application layer
├── analyzers/              # Analysis modules
├── components/             # Terminal UI components
├── storage/                # Data persistence
├── importing/              # Data import modules
├── requirements*.txt       # Dependencies
└── cibmangotree.py         # Main entry point
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
# Activate virtual environment (if not already active)
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Start the application
python -m cibmangotree
```

### Development Mode

```bash
# Run with debugging/development flags
python -m cibmangotree --noop  # Test mode, exits immediately
```

## Testing Setup

### Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest analyzers/hashtags/test_hashtags_analyzer.py

# Run with verbose output
pytest -v

# Run specific test function
pytest analyzers/hashtags/test_hashtags_analyzer.py::test_gini
```

### Test Data

- Test data is co-located with analyzers in `test_data/` directories
- Each analyzer should include its own test files
- Tests use sample data to verify functionality

## Build Setup (Optional)

### Executable Building

```bash
# Build standalone executable
pyinstaller pyinstaller.spec

# Output will be in dist/ directory
```

### Build Requirements

- Included in `requirements-dev.txt`
- Used primarily for release distribution
- Not required for development

## IDE Integration

### Recommended IDE Settings

**VS Code** (`.vscode/` configuration):

- Python interpreter: `./venv/bin/python`
- Black formatter integration
- isort integration
- pytest test discovery

**PyCharm**:

- Interpreter: Project virtual environment
- Code style: Black
- Import optimizer: isort

### Git Configuration

**Pre-commit Hooks**:

```bash
# Hooks are set up automatically by bootstrap script
# Manual setup if needed:
pip install pre-commit
pre-commit install
```

**Git Flow**:

- Branch from `develop` (not `main`)
- Feature branches: `feature/name`
- Bug fixes: `bugfix/name`

## Troubleshooting

### Common Issues

**Python Version Error**:

```bash
# Check Python version
python --version

# If not 3.12, install Python 3.12 and recreate venv
python3.12 -m venv venv
```

**Import Errors**:

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements-dev.txt
```

**Formatting Errors in CI**:

```bash
# Run formatters locally before committing
isort .
black .
```

**Test Failures**:

```bash
# Ensure test data is present
ls analyzers/*/test_data/

# Check if specific analyzer tests pass
pytest analyzers/hashtags/ -v
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

- Use `pytest -x` to stop on first failure
- Use `pytest -k pattern` to run specific test patterns
