# Suggested Commands

## Development Environment

```bash
# Setup virtual environment (first time)
python -m venv venv

# Activate environment and install dependencies
./bootstrap.sh          # macOS/Linux
./bootstrap.ps1         # Windows PowerShell
```

## Running the Application

```bash
# Start the application
python -m cibmangotree

# Run with no-op flag (for testing)
python -m cibmangotree --noop
```

## Development Commands

```bash
# Code formatting (must be run before commits)
isort .
black .

# Run both formatters together
isort . && black .

# Run tests
pytest

# Run specific test
pytest analyzers/hashtags/test_hashtags_analyzer.py

# Install development dependencies
pip install -r requirements-dev.txt

# Install production dependencies only
pip install -r requirements.txt
```

## Git Workflow

```bash
# Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "Description of changes"
git push origin feature/new-feature

# Create PR to develop branch (not main)
```

## Build Commands

```bash
# Build executable (from GitHub Actions)
pyinstaller pyinstaller.spec
```

## System Commands (macOS)

```bash
# Standard Unix commands work on macOS
ls, cd, find, grep, git

# Use these for file operations
find . -name "*.py" -type f
grep -r "pattern" --include="*.py" .
```
