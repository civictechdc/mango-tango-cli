# Code Style and Conventions

## Formatting Tools

- **Black**: Code formatter (automatically configured)
- **isort**: Import sorter with black profile
- **Pre-commit hooks**: Automatically format code on commit

## Code Style Requirements

- Python 3.12 syntax and features
- Black-formatted code (line length, spacing, etc.)
- isort-organized imports with black profile
- Type hints using modern Python syntax (`list[str]` not `List[str]`)
- Pydantic models for data validation

## Project Conventions

### File Organization

- Modules organized by domain (app, components, analyzers, storage, importing)
- Each analyzer has its own subdirectory with interface.py, main.py, and optional web components
- Test files follow naming: `test_*.py` in same directory as code being tested
- Interface files define data schemas and parameters

### Naming Conventions

- Snake_case for functions, variables, modules
- PascalCase for classes
- UPPER_CASE for constants
- Descriptive names reflecting domain concepts

### Architecture Patterns

- Context pattern for dependency injection (AppContext, ViewContext, etc.)
- Interface pattern for analyzer definitions
- Factory pattern for web presenters
- Modular analyzer system with clear separation of concerns

### Import Patterns

- Relative imports within modules
- Clear separation between core, edge, and content domains
- Dependencies injected through context objects

### Data Handling

- Parquet files for data persistence
- Polars for data processing (preferred over pandas)
- TinyDB for lightweight metadata storage
- Type-safe data models using Pydantic

### Testing Patterns

- pytest framework
- Test data stored in test_data/ subdirectories
- Integration tests for analyzer workflows
- CI/CD runs formatting checks and tests on PRs
