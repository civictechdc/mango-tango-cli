# Serena MCP Integration Guide

## Semantic Analysis Workflow

### Symbol Discovery

```python
# Recommended Sequence
symbols_overview = get_symbols_overview("target_directory")
target_symbol = find_symbol("TargetClass", include_body=False, depth=1)
symbol_references = find_referencing_symbols("TargetClass/method", "file.py")
```

### Memory System Usage

1. Use `list_memories()` to explore available knowledge
2. `read_memory()` for specific domain insights
3. `write_memory()` to preserve new project knowledge

## Tool Prioritization

### Symbolic Operations Priority

1. `get_symbols_overview()`
2. `find_symbol()`
3. `find_referencing_symbols()`
4. Read tools (last resort)

### Onboarding Workflow

- Verify onboarding: `check_onboarding_performed()`
- Initial setup: `onboarding()` tool

## Best Practices

- Prefer semantic analysis over file reading
- Use memory system for persistent insights
- Maintain context across interactions
- Always validate code structure before modifications
