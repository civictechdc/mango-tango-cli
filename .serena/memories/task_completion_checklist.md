# Task Completion Checklist

## Before Committing Code

### 1. Code Formatting (Required)

```bash
isort .
black .
```

**Critical**: Pre-commit hooks will run these automatically, but manually running ensures no surprises.

### 2. Testing

```bash
# Run all tests
pytest

# Run specific analyzer tests if modified
pytest analyzers/[analyzer_name]/test_*.py
```

### 3. Code Quality Validation

- Ensure no new linting errors
- Check that type hints are present for new functions
- Verify imports are properly organized

## For New Analyzers

### 1. Required Files

- `interface.py` - Define analyzer interface with input/output schemas
- `main.py` - Implement analyzer logic
- `__init__.py` - Export analyzer module
- `test_*.py` - Add tests for the analyzer

### 2. Registration

- Add analyzer to `analyzers/__init__.py` suite
- Ensure interface follows AnalyzerInterface pattern

### 3. Testing

- Create test data in `test_data/` directory
- Test with sample data to ensure parquet output works
- Verify web presenter integration if applicable

## Git Workflow Checklist

### 1. Branch Management

- Always branch from `develop` (not `main`)
- Use descriptive branch names: `feature/name` or `bugfix/name`

### 2. Commit Requirements

- Clear commit messages describing the change
- Code must pass formatting checks (isort + black)
- All tests must pass

### 3. Pull Request

- Target `develop` branch
- Use the template file `.github/PULL_REQUEST_TEMPALTE.md`
- Include description of changes
- Wait for CI/CD checks to pass
- Address any review feedback

## CI/CD Requirements

All PRs must pass:

- Code formatting checks (isort + black)
- PyTest suite
- Build verification
