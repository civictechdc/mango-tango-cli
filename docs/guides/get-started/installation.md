# Prerequisites

## Required Software

- **Python 3.12**: Required for all features to work correctly
- Node.JS (20.0.0 or above): Required for the React dashboards
  to work correctly
- **Git**: For version control and contributing
- **Terminal/Command Line**: Application runs in terminal interface

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

=== "Linux & Mac OS"

    ``` bash
    which <program_name_here (node|python|git)>
    ```

=== "Windows"

    ``` PowerShell
    where.exe <program_name_here (node|python|git)> 
    ```


# Setting up development environment

## 1. Clone Repository

```bash
git clone https://github.com/civictechdc/cib-mango-tree.git
cd cib-mango-tree
```

## 2. Install uv (Recommended)



!!! tip "Skip if you prefer traditional pip"
    If you don't want to use `uv`, you can skip this step and use the traditional pip method in the next section.

## 3. Create Virtual Environment & Install Dependencies

Choose your preferred method for setting up your development environment:

??? info "Installing uv"  
    
    `uv` is an extremely fast Python package manager (10-100x faster than pip) that simplifies virtual environment and dependency management.

    === "macOS/Linux"

        ```bash
        curl -LsSf https://astral.sh/uv/install.sh | sh
        ```

    === "Windows (PowerShell)"

        ```powershell
        powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
        ```

    === "Alternative (via pip)"

        ```bash
        pip install uv
        ```

=== "uv (recommended - faster)"

    ```bash
    # Create virtual environment
    uv venv

    #Activate virtual environment (macOS/Linux)
    source venv/bin/activate

    # OR: if using Windows and PowerShell
    # venv\Scripts\activate
    
    # Install dependencies
    uv pip install -r requirements-dev.txt  # also includes requirements.txt
    ```

=== "pip (traditional)"

    ```bash
    # Create virtual environment
    python -m venv venv
    
    # Activate virtual environment (macOS/Linux)
    source venv/bin/activate
    # OR: if using Windows and PowerShell
    # venv\Scripts\activate
    
    # Install dependencies
    pip install -r requirements-dev.txt
    ```

!!! note "Verify Python version"
    Ensure you're using Python 3.12.x:
    ```bash
    python --version  # Should show Python 3.12.x
    ```

## 4. Set Up Pre-commit Hooks

Pre-commit hooks automatically format your code with Black and isort before each commit.

```bash
# Install pre-commit hooks
pre-commit install
```

!!! tip "Manual formatting"
    You can also format code manually:
    ```bash
    isort .
    black .
    ```

## 5. Verify Installation

```bash
python -m cibmangotree --noop
```

Should output: 
```bash
No-op flag detected. Exiting successfully.
```
# Activating Virtual Environment

After completing the installation, the following commands can be used to activate
the virtual environment in order to work with the project.

=== "macOS/Linux (Bash)"

    ```bash
    source ./venv/bin/activate
    ```

=== "Windows (PowerShell)"

    ```powershell
    ./venv/Scripts/Activate.ps1
    ```


## Code Formatting

The project uses [Black](https://pypi.org/project/black/) for code style and formatting, [isort](https://pycqa.github.io/isort/index.html) for organization of import modules, and [pre-commit](https://pre-commit.com/) hooks for automatic formatting applied on every commit.

These tools are automatically installed as part of `requirements-dev.txt`. If you need to manually format code without committing, run:

```bash
isort .
black .
```

# Database and Storage

## Application Data Directory

The application automatically creates data directories:

=== "MacOS"
    `~/Library/Application Support/MangoTango/`

=== "Windows"
    `%APPDATA%/Civic Tech DC/MangoTango/`

=== "Linux"
    `~/.local/share/MangoTango/`

## Database Initialization

- **TinyDB**: Automatically initialized on first run
- **Project Files**: Created in user data directory
- **Parquet Files**: Used for all analysis data storage

No manual database setup required.

# Running the Application

## Basic Usage

```bash
# Start the application
python -m cibmangotree
```

## Development Mode

```bash
# Run with debugging/development flags
python -m cibmangotree --noop  # Test mode, exits immediately
```

## Development Mode for The React Dashboards

The following commands can be used to start the development vite server for the
react dashboards that are currently in development.

**npm**:

```bash
cd ./app/web_templates
npm run dev
```

**pnpm**:

```bash
cd ./app/web_templates
pnpm dev
```

# Build Setup (Optional)

## Executable Building

```bash
# Build standalone executable
pyinstaller pyinstaller.spec

# Output will be in dist/ directory
```

## Bundle Building for React Dashboard

**npm**:

```bash
npm run build
```

**pnpm**:

```bash
pnpm build
```

## Build Requirements

- Included in `requirements-dev.txt`
- Used primarily for release distribution
- Not required for development

# IDE Integration

## Recommended IDE Settings

**VS Code** (`.vscode/` configuration):

- Python interpreter: `./venv/bin/python`
- Black formatter integration
- isort integration
- pytest test discovery

**PyCharm**:

- Interpreter: Project virtual environment
- Code style: Black
- Import optimizer: isort

## Git Configuration

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
cd ./app/web_templates
npm install --legacy-peer-deps
```

## Other Common Issues

**Import Errors**:

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\Activate.ps1     # Windows

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

## Environment Variables

**Optional Configuration**:

- `MANGOTANGO_DATA_DIR` - Override default data directory
- `MANGOTANGO_LOG_LEVEL` - Set logging verbosity

# Next Steps

Once you have everything installed and running without any problems,
the next step is to check out the [Contributor Workflow](contributing.md)
