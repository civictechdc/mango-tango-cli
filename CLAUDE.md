# Claude Code - Mango Tango CLI Integration

## Project Context

### Core Documentation

- **Repository Overview**: `.ai-context/README.md`
- **Architecture Deep Dive**: `.ai-context/architecture-overview.md`
- **Symbol Reference**: `.ai-context/symbol-reference.md`
- **Setup Guide**: `.ai-context/setup-guide.md`
- **Development Guide**: `docs/dev-guide.md`

### Quick Context Loading

```markdown
# Start with this for comprehensive context
`.ai-context/README.md`

# For architectural understanding
`.ai-context/architecture-overview.md`

# For precise symbol navigation
`.ai-context/symbol-reference.md`
```

## Knowledge Graph Integration

### Essential Knowledge Graph Usage

**Entity-Based Project Knowledge**:

```markdown
- Use `search_nodes(query)` to find entities by query
- Use `open_nodes([names])` to retrieve specific entities
- Use `read_graph()` for comprehensive project overview
- Use `create_entities([...])` to capture new insights
- Use `add_observations([...])` to enhance existing knowledge
- Use `create_relations([...])` to link related concepts
```

### Knowledge Structure

**Entity Types**:

- `Module` - Core application modules (app, storage, analyzers)
- `Analyzer` - Specific analyzer implementations
- `Component` - UI and terminal components
- `Service` - Shared services (tokenizer, logging)
- `Pattern` - Architectural patterns and conventions
- `Concept` - Domain concepts and abstractions
- `Workflow` - Development workflows and processes

**Relation Types**:

- `implements` - Entity implements interface/pattern
- `uses` - Entity depends on or uses another
- `part_of` - Entity is component of another
- `extends` - Entity extends/inherits from another
- `related_to` - General relationship

### When to Use Knowledge Graph

**Capture Knowledge When**:

- Discovering non-obvious architectural patterns
- Understanding complex dependencies
- Learning analyzer-specific implementation details
- Identifying gotchas or edge cases
- Documenting workflow improvements

**Retrieve Knowledge When**:

- Starting work on unfamiliar modules
- Understanding analyzer ecosystem
- Looking for similar implementations
- Debugging complex interactions
- Planning architectural changes

**When NOT to Use**:

- Reading specific known file paths (use Read)
- Simple code lookups (use Grep/Glob)
- When manual docs suffice

## Code Navigation Patterns

### Finding Code with Standard Tools

```markdown
# Find files by pattern
Glob: "**/*analyzer*.py"
Glob: "app/**/*.py"

# Find class definitions
Grep: "^class AnalyzerInterface" --type py

# Find function definitions
Grep: "^def main\(" --type py

# Find usage/references
Grep: "from app.logger import" --type py
Grep: "AnalysisContext" --type py

# Read specific files
Read: app/app.py
Read: analyzers/hashtags/main.py
```

### Code Exploration Workflow

```markdown
1. Glob to find relevant files
2. Grep to locate specific symbols
3. Read to understand implementation
4. Query knowledge graph for architectural context
```

## Development Guidelines

### Session Startup Checklist

1. ✅ Load `.ai-context/README.md for project overview`
2. ✅ Query knowledge graph for relevant domain knowledge
3. ✅ Use Grep/Glob for code exploration
4. ✅ Maintain context throughout development

### Code Development Standards

**Logging Integration:**

```python
from app.logger import get_logger
logger = get_logger(__name__)
logger.info("Operation started", extra={"context": "value"})
```

Use structured logging throughout development. See `docs/dev-guide.md#logging` for complete patterns.

### Task-Specific Patterns

**New Analyzer Development**:

```markdown
1. Glob: "analyzers/example/**/*.py"  # Find example analyzer
2. Read: analyzers/example/interface.py
3. search_nodes("analyzer architecture")  # Understand patterns
4. Read: analyzers/example/main.py
5. Use knowledge graph insights to implement
```

**Bug Investigation**:

```markdown
1. Grep: "problematic_function" --type py -n
2. Read file with function implementation
3. Grep: "problematic_function" (find all usages)
4. search_nodes("related pattern")  # Context
5. Use knowledge graph to trace execution flow
```

**Code Refactoring**:

```markdown
1. Grep: "target_symbol" --type py (find all references)
2. Read each file to understand usage
3. open_nodes(["RelatedPattern"])  # Understand constraints
4. Make changes with full context
```

## Knowledge Graph Usage

### Entity Structure Examples

**Analyzer Entity**:

```markdown
{
  name: "HashtagAnalyzer",
  entityType: "Analyzer",
  observations: [
    "Primary analyzer for hashtag extraction and analysis",
    "Located in analyzers/hashtags/main.py",
    "Uses regex patterns to extract hashtags from text columns",
    "Outputs: hashtag frequency, co-occurrence, temporal patterns",
    "Gotcha: Handles Unicode hashtags correctly via preprocessing"
  ]
}
```

**Pattern Entity**:

```markdown
{
  name: "AnalyzerInterface",
  entityType: "Pattern",
  observations: [
    "Declarative interface definition for all analyzers",
    "Defines inputs (columns + semantic types), outputs, parameters",
    "Three stages: Primary → Secondary → Web Presenter",
    "Context pattern used for dependency injection",
    "See .ai-context/architecture-overview.md for details"
  ]
}
```

**Service Entity**:

```markdown
{
  name: "TokenizerService",
  entityType: "Service",
  observations: [
    "Located in services/tokenizer/",
    "AbstractTokenizer base, BasicTokenizer implementation",
    "Handles scriptio continua (CJK, Thai, Lao, Myanmar, Khmer)",
    "Space-separated tokenization (Latin, Arabic)",
    "Social media entity preservation (URLs, @mentions, #hashtags)",
    "Thread-safe, stateless API with optional streaming"
  ]
}
```

### Relation Examples

```markdown
create_relations([
  {from: "HashtagAnalyzer", to: "AnalyzerInterface", relationType: "implements"},
  {from: "NGramAnalyzer", to: "TokenizerService", relationType: "uses"},
  {from: "TokenizerService", to: "Service", relationType: "part_of"},
  {from: "DashPresenter", to: "WebPresenterPattern", relationType: "implements"}
])
```

### Common Query Patterns

```markdown
# Find analyzer-related knowledge
search_nodes("analyzer architecture")

# Get tokenizer service details
open_nodes(["TokenizerService", "BasicTokenizer"])

# Understand context pattern
search_nodes("context dependency injection")

# Find all analyzers
search_nodes("analyzer")  # Filter by entityType: Analyzer

# Explore web presenter patterns
search_nodes("dash shiny web presenter")
```

### Capturing New Knowledge

```markdown
# After discovering architectural patterns
create_entities([{
  name: "ProgressTrackingPattern",
  entityType: "Pattern",
  observations: [
    "Used in AnalysisContext for long-running operations",
    "Callback-based with AnalysisRunProgressEvent",
    "Supports both terminal and web UI progress reporting"
  ]
}])

# Link related concepts
create_relations([{
  from: "ProgressTrackingPattern",
  to: "AnalysisContext",
  relationType: "part_of"
}])
```

## Context Management

### Efficient Context Loading

```markdown
# Core context (always load)
`.ai-context/README.md`

# Task-specific context
`.ai-context/symbol-reference.md`      # For code navigation
`.ai-context/architecture-overview.md` # For system design
`.ai-context/setup-guide.md`          # For environment issues

# Deep domain knowledge
search_nodes("analyzer architecture")  # For analyzer work
search_nodes("code style conventions") # For style questions
search_nodes("tokenizer patterns")     # For text processing
```

### Code Navigation Examples

```markdown
# Find app entry point
Grep: "^def main" --path mangotango.py

# Explore analyzer system
Glob: "analyzers/**/__init__.py"
Read: analyzers/__init__.py

# Understand storage layer
Grep: "^class Storage" --type py
Read: storage/__init__.py

# Trace UI components
Glob: "components/**/*.py"
Grep: "^def main_menu" --type py
```

### Context Switching Strategy

```markdown
1. Start with manual docs for overview
2. Use knowledge graph for domain-specific deep dives
3. Use Grep/Glob for precise code navigation
4. Reference symbol guide for quick lookups
```

## Reference Links

### Documentation Structure

- **AI Context**: `.ai-context/` - Token-efficient documentation
- **Development**: `docs/dev-guide.md` - Comprehensive development guide
- **Knowledge Graph**: Entity-based semantic project knowledge

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

## Documentation Integration Strategy

### Knowledge Graph + Manual Documentation Bridge

- **Manual docs** (`.ai-context/`) provide structured overviews
- **Knowledge graph** provides deep semantic insights and relationships
- **Both systems** complement each other for comprehensive understanding
- **Symbol reference** links to actual code locations for navigation

### Context Hybrid Approach

This approach ensures both human-readable documentation and AI-powered semantic understanding through the knowledge graph for maximum development efficiency.
