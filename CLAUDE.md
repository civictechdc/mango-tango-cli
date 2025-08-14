# Claude Code - Mango Tango CLI Integration

## Critical Thinking Framework

**CRITICAL GUIDELINES:**

- USE BRUTAL HONESTY
- Challenge ALL assumptions
- Question every suggestion
- Prioritize analytical rigor over politeness

### Behavioral Expectations

- ✅ Disagree directly and constructively
- ✅ Provide alternative perspectives
- ✅ Point out logical inconsistencies
- ❌ Never agree without thorough analysis

## Context Loading

### Essential Documentation

```markdown
# Bootstrap Context
@.ai-context/00_bootstrap.md

# Working Context
@.ai-context/01_working_context.md

# Strategy Guide
@.ai-context/context_loading_strategy.md

# Progressive Reference
@.ai-context/02_reference/architecture.md
@.ai-context/02_reference/symbol_reference.md
@.serena/memories/claude-mcp-integration.md
```

**Context Loading Strategy**:

- Start with `00_bootstrap.md` for initial project overview
- Use `01_working_context.md` for operational details
- Refer to `context_loading_strategy.md` for dynamic context management
- Access detailed references in `02_reference/` as needed
- Leverage Serena memories for deep semantic insights

## Subagent Usage Patterns

### Specialized Subagents

- **analytics-specialist**: Social media analysis
- **data-pipeline-optimizer**: Memory-efficient processing
- **terminal-ui-specialist**: CLI UX design
- **dashboard-engineer**: Web visualizations
- **analyzer-framework-specialist**: Analyzer interfaces

### Routing Guidelines

- Use most specialized subagent for each task
- Avoid general-purpose agents
- Chain subagents for complex workflows

## Project Interaction Constraints

### Development Principles

- Maintain domain-driven modular design
- Preserve context-based dependency injection
- Follow interface-first development
- Optimize for memory-aware processing

### Tool Usage Priorities

1. Semantic tools over file reading
2. Symbolic operations preferred
3. Minimize direct file manipulations
4. Use memory system for persistent insights

## Debugging & Analysis

### Recommended Workflow

1. Use `get_symbols_overview()`
2. Apply `find_symbol()` for precise discovery
3. Use `find_referencing_symbols()`
4. Leverage memory system for context

## Critical Reminders

- ALWAYS validate assumptions
- Provide ACTIONABLE feedback
- Maintain ANALYTICAL RIGOR
- Challenge EXISTING PATTERNS
