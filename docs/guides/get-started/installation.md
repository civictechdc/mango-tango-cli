# Prerequisites

## Required software

You will need the following software installed in order to get started with setting up development environment:  

| Software  |  Needed for  |
| --- | --- |
| Python 3.12 | Required for all features to work correctly |
| Git | Required for version control and contributing |
| command line/terminal | Application runs in terminal |

!!! note "Installing Python/Git"  
    If you haven't installed git and/or python yet refer to the
    following links for instructions:

    - [Git installation](https://git-scm.com/install/)
    - [Python installation](https://www.python.org/downloads/)

## System requirements

- Operating System: Windows (PowerShell), macOS, Linux
- Memory: 4GB+ RAM (for processing large datasets)
- Storage: 1GB+ free space (for project data and virtual environment)

## Checking dependencies

If you're not sure which packages you already have installed on your system, the
following commands can be used to figure what packages you already installed:

=== "Linux & Mac OS"

    ``` bash
    which <program_name_here (python|git)>
    ```

=== "Windows"

    ``` PowerShell
    where.exe <program_name_here (python|git)> 
    ```


# Setting up development environment

## 1. Clone repository

First clone the remote repository:  

```bash
git clone https://github.com/civictechdc/cib-mango-tree.git  # creates cib-mango-tree folder in the current directory
cd cib-mango-tree  # navigate to the folder with cloned repository
```

## 3. Create virtual environment & install dependencies

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

## 4. Set up pre-commit hooks

[Pre-commit](https://pre-commit.com/) hooks (in `pre-commit-config.yaml`) automatically format your code with [Black](https://pypi.org/project/black/) and [isort](https://pycqa.github.io/isort/index.html) before each commit.

In the root of the cloned repository install pre-commit:  
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

## 5. Verify installation

```bash
python -m cibmangotree --noop
```

If all went well, you should see: 
```bash
No-op flag detected. Exiting successfully.
```

# Starting the Application

## Basic Usage

Once you have activated the environment and installed dependecies, invoke the `cibmangotree.py` script from project root:  
```bash
# Start the application
python -m cibmangotree
```

# Project storage

## Application Data Directory

The application automatically creates data directories:

=== "MacOS"
    `~/Library/Application Support/MangoTango/`

=== "Windows"
    `%APPDATA%/Civic Tech DC/MangoTango/`

=== "Linux"
    `~/.local/share/MangoTango/`

## Database Initialization

| Storage component | Function |
| --- | --- |
| TinyDB | Automatically initialized on first run |
| Project Files |  Created in user data directory |
| Parquet Files | Used for all analysis data storage |

No manual database setup required.


# Executable Building

```bash
# Build standalone executable
pyinstaller pyinstaller.spec
```

Output (`cibmangotree.app` or `cimangotree.exe`) will be in `dist` directory.

## Build Requirements

- Included in `requirements-dev.txt`
- Used primarily for release distribution
- Not required for development

# Troubleshooting

## Common Dependency Issues

One common issue when installing the dependencies for python is the installation
failing due to compatibility issues with the python package `pyarrow`. The compatibility
issues are due to a version mismatch between pyarrow and python itself.
To resolve this issue, you must be on version 3.12 for python.
Refer to [commands above](#3-create-virtual-environment-install-dependencies) to switch to the correct version.


# Next Steps

Once you have everything installed and running without any problems,
the next step is to check out the [GitHub Contributor Workflow](../contributing/github_workflow.md) for contributing changes.
