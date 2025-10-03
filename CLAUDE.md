# Claude Code - Mango Tango CLI Integration

## Project Context

### Core Documentation

- **Repository Overview**: @.ai-context/README.md
- **Architecture Deep Dive**: @.ai-context/architecture-overview.md
- **Symbol Reference**: @.ai-context/symbol-reference.md
- **Setup Guide**: @.ai-context/setup-guide.md
- **Development Guide**: @docs/dev-guide.md

### Quick Context Loading

```markdown
# Start with this for comprehensive context
@.ai-context/README.md

# For architectural understanding
@.ai-context/architecture-overview.md

# For precise symbol navigation
@.ai-context/symbol-reference.md
```

## Serena MCP Integration

### Essential Serena Usage

**Symbol-Level Development**:

```markdown
- Use `get_symbols_overview` for high-level code structure
- Use `find_symbol` for specific class/function discovery
- Use `find_referencing_symbols` for dependency analysis
- Prefer symbolic operations over reading entire files
```

**Memory System**:

```markdown
- Use `list_memories` to see available project knowledge
- Use `read_memory` for specific domain knowledge
- Use `write_memory` for new insights worth preserving
```

### Serena Semantic Analysis

**When to Use Semantic Tools**:

- Understanding code architecture and relationships
- Finding specific functions, classes, or components
- Tracing dependencies and references
- Getting project overviews without reading full files

**When NOT to Use**:

- Reading specific known file paths (use Read tool)
- Simple file operations (use standard tools)
- When you already have the full file content

## Tool Usage Patterns

### Symbol Discovery Workflow

```markdown
1. get_symbols_overview("target_directory")
2. find_symbol("TargetClass", include_body=False, depth=1)
3. find_symbol("TargetClass/method", include_body=True)
4. find_referencing_symbols("TargetClass/method", "file.py")
```

### Analysis Integration Workflow

```markdown
1. find_symbol("AnalyzerInterface") # Find base interface
2. get_symbols_overview("analyzers/") # See all analyzers
3. find_symbol("specific_analyzer/main") # Get implementation
4. find_referencing_symbols() # See usage patterns
```

### Context-Aware Development

```python
# Always understand the context pattern first
find_symbol("AnalysisContext", include_body=True)
find_symbol("ViewContext", include_body=True)
find_symbol("AppContext", include_body=True)
```

## Development Guidelines

### Session Startup Checklist

1. ✅ **Call `initial_instructions`**
2. ✅ Load @.ai-context/README.md for project overview
3. ✅ Check `.serena/memories/` for deep insights if needed
4. ✅ Use semantic tools for code exploration
5. ✅ Maintain context throughout development

### Code Development Standards

**Logging Integration:**

```python
from app.logger import get_logger
logger = get_logger(__name__)
logger.info("Operation started", extra={"context": "value"})
```

Use structured logging throughout development for debugging and monitoring. See @docs/dev-guide.md#logging for complete usage patterns.

### Task-Specific Patterns

**New Analyzer Development**:

```markdown
1. get_symbols_overview("analyzers/example/")
2. find_symbol("AnalyzerInterface", include_body=True)
3. read_memory("analyzer_architecture")
4. Use symbolic tools to create new analyzer
```

**Bug Investigation**:

```markdown
1. find_symbol("problematic_function", include_body=True)
2. find_referencing_symbols("problematic_function", "file.py")
3. Use semantic analysis to trace execution flow
```

**Code Refactoring**:

```markdown
1. find_referencing_symbols("target_symbol", "file.py")
2. get_symbols_overview() to understand impact
3. Use replace_symbol_body for precise changes
```

### Memory System Usage

**Available Memories**:

- `project_overview` - High-level project understanding
- `code_structure` - Module organization and responsibilities
- `analyzer_architecture` - Analyzer system deep dive
- `suggested_commands` - Development and testing commands
- `code_style_conventions` - Style guides and patterns
- `task_completion_checklist` - Pre-commit requirements

**Memory Loading Pattern**:

```markdown
# Load relevant memory for current task
read_memory("analyzer_architecture")  # For analyzer work
read_memory("suggested_commands")     # For development setup
read_memory("task_completion_checklist") # Before committing
```

## Context Management

### Efficient Context Loading

```markdown
# Core context (always load)
@.ai-context/README.md

# Task-specific context
@.ai-context/symbol-reference.md      # For code navigation
@.ai-context/architecture-overview.md # For system design
@.ai-context/setup-guide.md          # For environment issues

# Deep domain knowledge
@.serena/memories/analyzer_architecture.md # For analyzer work
@.serena/memories/code_style_conventions.md # For style questions
```

### Symbol Navigation Examples

```markdown
# Find app entry point
find_symbol("main", relative_path="mangotango.py")

# Explore analyzer system
get_symbols_overview("analyzers/")
find_symbol("suite", relative_path="analyzers/__init__.py")

# Understand storage layer
find_symbol("Storage", relative_path="storage/__init__.py", depth=1)

# Trace UI components
get_symbols_overview("components/")
find_symbol("main_menu", include_body=True)
```

## Reference Links

### Documentation Structure

- **AI Context**: `.ai-context/` - Token-efficient documentation
- **Development**: `docs/dev-guide.md` - Comprehensive development guide
- **Serena Memories**: `.serena/memories/` - Semantic project knowledge

### Key Architecture References

- **Entry Point**: `mangotango.py` - Application bootstrap
- **Core App**: `app/app.py:App` - Main application controller
- **Storage**: `storage/__init__.py:Storage` - Data persistence
- **UI Components**: `components/main_menu.py:main_menu()` - Terminal interface
- **Analyzer Suite**: `analyzers/__init__.py:suite` - Analysis registry

### Integration Points

- **Data Import**: `importing/` - CSV/Excel to Parquet conversion
- **Analysis Pipeline**: Primary → Secondary → Web presentation
- **Web Dashboards**: Dash and Shiny framework integration
- **Export System**: Multi-format output generation

## Memory System Integration

### Serena + Manual Documentation Bridge

- **Manual docs** (`.ai-context/`) provide structured overviews
- **Serena memories** (`.serena/memories/`) provide deep semantic insights
- **Both systems** complement each other for comprehensive understanding
- **Symbol reference** links to actual code locations for navigation

### Context Switching Strategy

```markdown
1. Start with manual docs for overview
2. Use Serena memories for domain-specific deep dives
3. Use semantic tools for precise code navigation
4. Reference symbol guide for quick lookups
```

**Note**: This hybrid approach ensures both human-readable documentation and AI-powered semantic understanding are available for maximum development efficiency.
