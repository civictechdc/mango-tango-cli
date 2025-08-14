# Working Context - Development Patterns

## Core Architecture Pattern

### Context-Based Dependency Injection

The application uses context objects for loose coupling between layers:

```python
# Analysis execution pattern
class AnalysisContext:
    input_path: Path           # Input parquet file
    output_path: Path          # Where to write results
    preprocessing: Callable    # Column mapping function
    progress_callback: Callable # Progress reporting
    parameters: dict           # User-configured parameters
```

### Three-Layer Domain Model

1. **Core Domain**: Application logic, UI components, storage
2. **Edge Domain**: Data import/export, preprocessing
3. **Content Domain**: Analyzers, web presenters

## Essential Development Workflows

### Analyzer Development Pattern

```python
# Declare interface first
interface = AnalyzerInterface(
    input=AnalyzerInput(columns=[...]),
    outputs=[AnalyzerOutput(...)],
    params=[AnalyzerParam(...)]
)

# Implement with context
def main(context: AnalysisContext) -> None:
    df = pl.read_parquet(context.input_path)
    # Process data...
    df.write_parquet(context.output_path)
```

### Tool Usage Strategy

**Serena Semantic Operations** (symbol-level development):

- `get_symbols_overview()` for file structure
- `find_symbol()` for specific classes/functions
- `find_referencing_symbols()` for dependency tracing
- `replace_symbol_body()` for precise edits

**Standard Operations** (known paths):

- `Read` for specific file content
- `Edit`/`MultiEdit` for file modifications
- `Bash` for testing and validation

### Data Processing Pattern

**Parquet-Centric Flow**:

1. Import (CSV/Excel) → Parquet files
2. Primary Analysis → Normalized results
3. Secondary Analysis → User-friendly reports
4. Web Presentation → Interactive dashboards

**Memory Management**:

```python
from app.utils import MemoryManager
memory_mgr = MemoryManager()  # Auto-detects system capabilities
```

## Common Patterns

### Logging Integration

```python
from app.logger import get_logger
logger = get_logger(__name__)
logger.info("Operation started", extra={"context": "value"})
```

### Progress Reporting

```python
# Modern Textual-based progress
progress_manager.add_step("processing", "Processing data", total=1000)
progress_manager.start_step("processing")
progress_manager.update_step("processing", 500)
progress_manager.complete_step("processing")
```

### Testing Approach

```python
from testing.context import TestPrimaryAnalyzerContext
from testing.testers import test_primary_analyzer

# Standardized analyzer testing
test_primary_analyzer(
    analyzer_module=your_analyzer,
    test_context=TestPrimaryAnalyzerContext(...)
)
```

## Key File Locations

### Entry Points

- `mangotango.py` - Application bootstrap
- `components/main_menu.py:main_menu()` - UI entry point
- `analyzers/__init__.py:suite` - Analyzer registry

### Core Classes

- `app/app.py:App` - Application controller
- `storage/__init__.py:Storage` - Data persistence
- `app/app_context.py:AppContext` - Dependency container

### Development References

- See `02_reference/` for detailed symbol information
- See `@docs/dev-guide.md` for comprehensive development guide
- See `@.serena/memories/` for deep domain knowledge
