# Prerequisites

## Required Software

- **Python 3.12** - Required for all features to work correctly
- **UV** - Modern Python package manager (automatically installed by bootstrap script)
- Node.JS (20.0.0 or above) - Required for the React dashboards
  to work correctly
- **Git** - For version control and contributing
- **Terminal/Command Line** - Application runs in terminal interface

## System Requirements

- **Operating System**: Windows (PowerShell), macOS, Linux
- **Memory**: 4GB+ RAM (for processing large datasets)
- **Storage**: 1GB+ free space (for project data and virtual environment)

## Resources

If you haven't installed git, node.js, and/or python yet refer to the
following links for instructions on downloading and installing said packages:

- [https://codefinity.com/blog/A-step-by-step-guide-to-Git-installation](https://codefinity.com/blog/A-step-by-step-guide-to-Git-installation)
- [https://nodejs.org/en/download](https://nodejs.org/en/download)
- [https://realpython.com/installing-python/](https://realpython.com/installing-python/)

## Checking Dependencies

If you're not sure which packages you already have installed on your system, the
following commands can be used to figure what packages you already installed:

### Linux & Mac OS

```bash
which <program_name_here (node|python|git)>
```

### Windows

```PowerShell
where.exe <program_name_here (node|python|git)>
```

# Installation

## 1. Clone Repository

```bash
git clone https://github.com/CIB-Mango-Tree/mango-tango-cli.git
cd mango-tango-cli
```

## 2. Bootstrap Development Environment

**Mac OS/Linux (Bash)**:

```bash
./bootstrap.sh
```

**Windows (PowerShell)**:

```powershell
./bootstrap.ps1
```

The bootstrap script will:

- Install UV package manager (if not already installed)
- Create `.venv/` virtual environment using UV
- Install all workspace dependencies via `uv sync`
- Set up pre-commit hooks for code formatting

**Manual UV Setup** (if needed):

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# or
pip install uv

# Sync dependencies
uv sync
```

## 3. Verify Installation

```bash
uv run cibmangotree --noop
```

Should output: "No-op flag detected. Exiting successfully."

# Activating Virtual Environment

UV automatically manages the virtual environment. When you use `uv run`, it
activates the `.venv/` environment automatically.

**Manual Activation** (if needed):

**Mac OS/Linux (Bash)**:

```bash
source .venv/bin/activate
```

**PowerShell (Windows)**:

```PowerShell
.venv/Scripts/Activate.ps1
```

**Note**: With UV, you typically don't need to manually activate the environment.
Use `uv run <command>` instead.

# Development Environment Setup

## Dependencies Overview

Dependencies are managed by UV using `pyproject.toml` in a workspace configuration.
Run `uv sync` to install all dependencies across all packages.

**Core Production Dependencies**:

- `polars>=1.9.0` - Primary data processing
- `pydantic>=2.9.1` - Data validation and models
- `inquirer>=3.4.0` - Interactive terminal prompts
- `tinydb>=4.8.0` - Lightweight JSON database
- `dash>=2.18.1` - Web dashboard framework
- `shiny>=1.4.0` - Modern web UI framework
- `plotly>=5.24.1` - Data visualization
- `XlsxWriter>=3.2.0` - Excel export functionality

**Development Dependencies**:

- `black>=24.10.0` - Code formatter
- `isort>=5.13.2` - Import organizer
- `pytest>=8.3.4` - Testing framework
- `pyinstaller>=6.14.1` - Executable building

**React Dashboard Dependencies** (packages/core/src/cibmangotree/app/web_templates/package.json):

- typescript: 5.7.3
- vite: 6.3.5
- react: 19.0.0
- @deck.gl: 9.1.11
- @visx: 3.12.0
- @glideapps/glide-data-grid: 6.0.3
- @radix-ui: (Varies based on component being used)
- zustand: 5.0.3
- tailwindcss: 4.0.6
- lucide-react: 0.475.0

**Managing Dependencies**:

```bash
# Install/sync all workspace dependencies
uv sync

# Add a new dependency to core package
uv add polars --package cibmangotree

# Add a development dependency
uv add --dev pytest

# Update all dependencies
uv sync --upgrade
```

## Code Formatting Setup

The project uses automatic code formatting:

- **Black**: Code style and formatting
- **isort**: Import organization
- **Pre-commit hooks**: Automatic formatting on commit

**Manual formatting**:

```bash
uv run isort .
uv run black .
```

## Project Structure Setup

After installation, your project structure should be:

```bash
mango-tango-cli/
├── .venv/                   # UV-managed virtual environment
├── .ai-context/             # AI assistant context documentation
├── docs/                    # Documentation
│   ├── guides/             # User guides
│   └── dev-guide.md        # Development guide
├── packages/               # UV workspace packages
│   ├── core/               # cibmangotree - Main application
│   │   └── src/cibmangotree/
│   │       ├── app/        # Application layer
│   │       ├── components/ # Terminal UI components
│   │       └── storage/    # Data persistence
│   ├── importing/          # cibmangotree-importing - Data I/O
│   ├── services/           # cibmangotree-services - Shared services
│   ├── testing/            # cibmangotree-testing - Testing utilities
│   └── analyzers/          # Analysis modules (plugins)
│       ├── hashtags/       # Hashtag analysis
│       ├── ngrams/         # N-gram analysis
│       ├── temporal/       # Temporal patterns
│       └── example/        # Example analyzer template
├── pyproject.toml          # UV workspace configuration
└── uv.lock                 # UV lockfile
```

# Database and Storage Setup

## Application Data Directory

The application automatically creates data directories:

- **macOS**: `~/Library/Application Support/MangoTango/`
- **Windows**: `%APPDATA%/Civic Tech DC/MangoTango/`
- **Linux**: `~/.local/share/MangoTango/`

## Database Initialization

- **TinyDB**: Automatically initialized on first run
- **Project Files**: Created in user data directory
- **Parquet Files**: Used for all analysis data storage

No manual database setup required.

# Running the Application

## Basic Usage

```bash
# Start the application
uv run cibmangotree
```

## Development Mode

```bash
# Run with debugging/development flags
uv run cibmangotree --noop  # Test mode, exits immediately
```

## Development Mode for The React Dashboards

The following commands can be used to start the development vite server for the
react dashboards that are currently in development.

**npm**:

```bash
cd packages/core/src/cibmangotree/app/web_templates
npm run dev
```

**pnpm**:

```bash
cd packages/core/src/cibmangotree/app/web_templates
pnpm dev
```

## Testing Setup

## Run Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest packages/analyzers/hashtags/tests/test_hashtags_analyzer.py

# Run with verbose output
uv run pytest -v

# Run specific test function
uv run pytest packages/analyzers/hashtags/tests/test_hashtags_analyzer.py::test_gini
```

## Test Data

- Test data is co-located with analyzers in `test_data/` directories
- Each analyzer package includes its own test files
- Tests use sample data to verify functionality
- Example: `packages/analyzers/hashtags/test_data/`

# Build Setup (Optional)

## Executable Building

```bash
# Build standalone executable
uv run pyinstaller pyinstaller.spec

# Output will be in dist/ directory
```

## Bundle Building for React Dashboard

**npm**:

```bash
cd packages/core/src/cibmangotree/app/web_templates
npm run build
```

**pnpm**:

```bash
cd packages/core/src/cibmangotree/app/web_templates
pnpm build
```

## Build Requirements

- Managed by UV through `pyproject.toml`
- Used primarily for release distribution
- Not required for development

# IDE Integration

## Recommended IDE Settings

**VS Code** (`.vscode/` configuration):

- Python interpreter: `./.venv/bin/python`
- Black formatter integration
- isort integration
- pytest test discovery
- UV extension (optional): Better UV integration

**PyCharm**:

- Interpreter: `.venv` virtual environment
- Code style: Black
- Import optimizer: isort
- External tools: Configure UV commands

## Git Configuration

**Pre-commit Hooks**:

```bash
# Hooks are set up automatically by bootstrap script
# Manual setup if needed:
uv add --dev pre-commit
# or if you need to install directly
uv run pip install pre-commit
pre-commit install
```

**Git Flow**:

- Branch from `develop` (not `main`)
- Feature branches: `feature/name`
- Bug fixes: `bugfix/name`

# Version Management

If you already have Python and Node.JS installed but are on different versions
from the versions outlined in the [requirements](#prerequisites) above you can switch
to the correct versions for both languages for the project using version managers.
The version manager for python is [pyenv](https://github.com/pyenv/pyenv).
Where the version manager that is recommended for Node is [nvm](https://github.com/nvm-sh/nvm).
Guides for installing both version managers are linked down below if you need
references to go off of.

- [https://www.freecodecamp.org/news/node-version-manager-nvm-install-guide/](https://www.freecodecamp.org/news/node-version-manager-nvm-install-guide/)
- [https://github.com/pyenv/pyenv?tab=readme-ov-file#installation](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation)
- [https://github.com/pyenv-win/pyenv-win?tab=readme-ov-file#installation](https://github.com/pyenv-win/pyenv-win?tab=readme-ov-file#installation)
  (If you're on windows and want to install pyenv)

Once you have both version managers installed the following commands can be used
to switch versions.

## pyenv

```shell
pyenv install 3.12
pyenv local 3.12
```

## nvm

```shell
nvm install v21.0.0
nvm use v21.0.0
```

# Troubleshooting

## Common Dependency Issues

One common issue when installing the dependencies for python is the installation
failing due to compatibility issues with the python package `pyarrow`. The compatibility
issues are due to a version mismatch between pyarrow and python itself.
To resolve this issue,you **MUST** be on version **3.12** for python.
Refer to [commands above](#pyenv) to switch to the correct version.

Similarly, the installation for node dependencies has been known to fail for
some developers due to a version mismatch caused by the underlying dependencies
for the package `@glideapps/glide-data-grid`. However, getting around this issue
is more straightforward with node packages. Running the installation command for
node with the flag `--legacy-peer-deps` is enough for the installation to work
if you run into this issue. The commands needed to run the installation manually
from the project root are as such.

```bash
cd packages/core/src/cibmangotree/app/web_templates
npm install --legacy-peer-deps
```

## Other Common Issues

**Import Errors**:

```bash
# Ensure dependencies are synced
uv sync

# Verify installation
uv run cibmangotree --noop

# Check UV environment
uv pip list
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
ls packages/analyzers/*/test_data/

# Check if specific analyzer tests pass
uv run pytest packages/analyzers/hashtags/ -v

# Verify all dependencies
uv sync
```

## Environment Variables

**Optional Configuration**:

- `MANGOTANGO_DATA_DIR` - Override default data directory
- `MANGOTANGO_LOG_LEVEL` - Set logging verbosity

# Next Steps

Once you have everything installed and running without any problems,
the next step is to check out the [Contributor Workflow](../contributing/contributing.md)
