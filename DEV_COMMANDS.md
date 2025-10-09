# Development Commands Quick Reference

This document provides a quick reference for all common development commands using UV.

## Setup

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/civictechdc/mango-tango-cli.git
cd mango-tango-cli

# Bootstrap environment (installs UV and dependencies)
./bootstrap.sh              # macOS/Linux
./bootstrap.ps1             # Windows PowerShell
```

### Manual UV Installation

```bash
# Install UV manually (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh       # macOS/Linux
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows
```

## Running the Application

```bash
# Run the application
uv run cibmangotree

# Run with no-op flag (verify installation)
uv run cibmangotree --noop

# Run with specific Python version
uv run --python 3.12 cibmangotree
```

## Testing

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific package tests
uv run pytest packages/analyzers/hashtags/
uv run pytest packages/core/

# Run specific test file
uv run pytest packages/analyzers/hashtags/tests/test_main.py

# Run with coverage
uv run pytest --cov=cibmangotree

# Run with coverage report
uv run pytest --cov=cibmangotree --cov-report=html
uv run pytest --cov=cibmangotree --cov-report=term-missing

# Run tests matching a pattern
uv run pytest -k "test_hashtag"

# Stop on first failure
uv run pytest -x

# Show local variables in tracebacks
uv run pytest -l
```

## Code Quality

### Formatting

```bash
# Format all code (Black)
uv run black .

# Format specific directory
uv run black packages/analyzers/hashtags/

# Check formatting without changing files
uv run black --check .

# Show diff of what would change
uv run black --diff .
```

### Import Sorting

```bash
# Sort all imports (isort)
uv run isort .

# Sort imports in specific directory
uv run isort packages/analyzers/hashtags/

# Check import order without changing files
uv run isort --check .

# Show diff of what would change
uv run isort --diff .
```

### Combined Formatting

```bash
# Format code and sort imports (CI workflow)
uv run isort . && uv run black .

# Check both without changing files
uv run isort --check . && uv run black --check .
```

## Package Management

### Dependencies

```bash
# Install/sync all dependencies
uv sync

# Install with all optional extras
uv sync --all-extras

# Install specific extra groups
uv sync --extra dev
uv sync --extra docs

# Update all dependencies
uv sync --upgrade

# Add a new dependency to workspace root
uv add <package>

# Add dev dependency
uv add --dev <package>

# Add dependency to specific package
uv add --package cibmangotree <package>
uv add --package cibmangotree-analyzers-hashtags <package>

# Remove a dependency
uv remove <package>
```

### Package Information

```bash
# Show dependency tree
uv tree

# Show installed packages
uv pip list

# Show outdated packages
uv pip list --outdated

# Show package info
uv pip show <package>
```

## Building

### PyInstaller Executable

```bash
# Build executable for current platform
uv run pyinstaller pyinstaller.spec

# Build with verbose output
uv run pyinstaller pyinstaller.spec --log-level DEBUG

# Clean build (remove build/dist first)
rm -rf build/ dist/
uv run pyinstaller pyinstaller.spec
```

### Test Built Executable

```bash
# After building, test the executable
./dist/cibmangotree --noop         # macOS/Linux
.\dist\cibmangotree.exe --noop     # Windows
```

## Git Workflow

### Feature Development

```bash
# Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# Make changes, then commit
git add .
git commit -m "feat: your feature description"

# Push and create PR
git push origin feature/your-feature-name
```

### Before Committing

```bash
# Ensure code is formatted
uv run black .
uv run isort .

# Run tests
uv run pytest

# Check everything passes
uv run isort --check . && uv run black --check . && uv run pytest
```

## Development Workflows

### New Analyzer Development

```bash
# 1. Explore example analyzer
cd packages/analyzers/example/
cat README.md

# 2. Copy example structure
cp -r packages/analyzers/example packages/analyzers/myanalyzer

# 3. Update pyproject.toml for new analyzer
# Edit packages/analyzers/myanalyzer/pyproject.toml

# 4. Add to workspace root pyproject.toml
# Edit pyproject.toml - add to [tool.uv.workspace.members]

# 5. Sync workspace
uv sync

# 6. Implement analyzer
# Edit packages/analyzers/myanalyzer/src/...

# 7. Run tests
uv run pytest packages/analyzers/myanalyzer/
```

### Debug a Failing Test

```bash
# Run test with verbose output and show locals
uv run pytest packages/analyzers/hashtags/tests/test_main.py -vl

# Run test with debugger (pdb)
uv run pytest packages/analyzers/hashtags/tests/test_main.py --pdb

# Run test and drop to debugger on first failure
uv run pytest packages/analyzers/hashtags/tests/test_main.py -x --pdb
```

### Update Dependencies

```bash
# Update all packages to latest versions
uv sync --upgrade

# Update specific package
uv add <package>@latest

# See what would be upgraded
uv sync --upgrade --dry-run
```

## Troubleshooting

### Common Issues

```bash
# Clear UV cache
uv cache clean

# Reinstall all dependencies
rm -rf .venv/
uv sync

# Check Python version
uv run python --version

# Verify installation
uv run python -c "import cibmangotree; print(cibmangotree.__version__)"

# Show UV version
uv --version
```

### Environment Info

```bash
# Show UV environment
uv venv list

# Show Python path
uv run which python

# Show installed package versions
uv run python -c "import cibmangotree; print(cibmangotree.__version__)"
uv run python -c "import polars; print(polars.__version__)"
```

## CI/CD

### GitHub Actions Workflows

The repository includes several GitHub Actions workflows that use UV:

- **Tests** (`.github/workflows/test.yml`) - Runs pytest on PRs
- **Code Quality** (`.github/workflows/code_quality.yml`) - Checks formatting
- **Build** (`.github/workflows/build_exe.yml`) - Builds executables
- **Release** (`.github/workflows/release.yml`) - Creates releases

All workflows automatically:
1. Install UV
2. Sync dependencies with `uv sync`
3. Run commands with `uv run`

### Local CI Simulation

```bash
# Simulate CI checks locally
uv sync
uv run isort --check .
uv run black --check .
uv run pytest
uv run pyinstaller pyinstaller.spec
```

## Quick Start Checklist

For new developers:

```bash
# 1. Clone and setup
git clone https://github.com/civictechdc/mango-tango-cli.git
cd mango-tango-cli
./bootstrap.sh  # or ./bootstrap.ps1 on Windows

# 2. Verify installation
uv run cibmangotree --noop

# 3. Create feature branch
git checkout develop
git pull origin develop
git checkout -b feature/my-feature

# 4. Make changes and test
# ... edit code ...
uv run black .
uv run isort .
uv run pytest

# 5. Commit and push
git add .
git commit -m "feat: my feature"
git push origin feature/my-feature
```

## Additional Resources

- **Development Guide**: `docs/dev-guide.md`
- **Contributing**: `CONTRIBUTING.md`
- **AI Context**: `.ai-context/README.md`
- **Claude Integration**: `CLAUDE.md`
- **UV Documentation**: https://docs.astral.sh/uv/
