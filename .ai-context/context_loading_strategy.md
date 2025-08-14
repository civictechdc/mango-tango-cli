# Context Loading Strategy - Progressive Disclosure

## Overview

This directory implements a progressive disclosure model to minimize initial context load while preserving comprehensive project information. The strategy emphasizes **just-in-time information access** using both manual documentation and Serena's semantic analysis capabilities.

## Core Philosophy

**Progressive Disclosure**: Start minimal, expand contextually based on task requirements.
**Hybrid Intelligence**: Combine token-efficient manual docs with AI-powered semantic analysis.
**Task-Driven Loading**: Match information depth to task complexity and scope.

## Layer 0: Bootstrap Context (<400 tokens)

**File**: `00_bootstrap.md`

Essential startup information for immediate orientation:

- Project identity and purpose
- Core tech stack
- Primary architectural pattern
- Entry points
- Behavioral requirements

**When to load**:

- ✅ **Always**: First interaction with the project
- ✅ **New contributor onboarding**
- ✅ **Context reset after long breaks**
- ✅ **Quick questions or clarifications**

## Layer 1: Working Context (<1,200 tokens)

**File**: `01_working_context.md`

Core development patterns and workflows:

- Context-based dependency injection pattern
- Three-layer domain model
- Essential development workflows
- Tool usage strategies
- Common coding patterns
- Key file locations

**When to load**:

- ✅ **Active development sessions**
- ✅ **Code review preparation**
- ✅ **Bug investigation**
- ✅ **Feature implementation**
- ✅ **Architecture discussions**

## Layer 2: Reference Documentation (On-demand)

**Directory**: `02_reference/`

Detailed information organized by topic:

### Architecture Deep Dive

- `architecture_deep_dive.md` - Comprehensive system architecture
- Complete data flow diagrams
- Performance optimization details
- Integration patterns

### Symbol References

- `symbols/core_domain.md` - Application, storage, and view layer symbols
- `symbols/analyzers.md` - Analyzer system and performance components
- `symbols/testing.md` - Testing infrastructure and utilities

### Advanced Topics

- `advanced/setup-guide.md` - Development environment setup
- Additional specialized guides as needed

**When to load**:

- ✅ **Complex refactoring**: Load architecture deep dive
- ✅ **New analyzer development**: Load analyzer symbols
- ✅ **Test framework work**: Load testing symbols
- ✅ **Performance optimization**: Load architecture + analyzer symbols
- ✅ **Environment issues**: Load setup guide

## Serena Semantic Analysis Integration

### Queryable Knowledge Base

The `.serena/memories/` directory contains AI-processed project insights that complement manual documentation:

**Available Memories**:

- `analyzer_architecture` - Deep dive into analyzer system design
- `progress_reporting_architecture` - Progress management implementation
- `performance_optimization_patterns` - Memory management and chunking strategies
- `code_structure` - Module organization and responsibilities
- `suggested_commands` - Development and testing workflows
- `code_style_conventions` - Project coding standards
- `task_completion_checklist` - Pre-commit validation steps

### Semantic Tools for Just-in-Time Access

**Symbol Discovery**:

```markdown
# Find specific functions/classes
find_symbol("ProgressManager", include_body=True, depth=1)
find_symbol("AnalysisContext/progress_callback", include_body=True)

# Get high-level code overview
get_symbols_overview("analyzers/ngrams/")
get_symbols_overview("terminal_tools/")
```

**Dependency Analysis**:

```markdown
# Trace code relationships
find_referencing_symbols("ProgressManager", "terminal_tools/progress.py")
find_referencing_symbols("AnalysisContext", "app/analysis_context.py")
```

**Pattern Search**:

```markdown
# Find usage patterns
search_for_pattern("progress_callback", restrict_search_to_code_files=True)
search_for_pattern("logger\.info", restrict_search_to_code_files=True)
```

### Memory System Usage

**Domain-Specific Knowledge Access**:

```markdown
# Load relevant memory for current task
read_memory("analyzer_architecture")         # For analyzer development
read_memory("progress_reporting_architecture") # For progress integration
read_memory("performance_optimization_patterns") # For performance work
read_memory("suggested_commands")             # For development setup
```

**Memory + Manual Doc Coordination**:

1. **Start with manual docs** for structured overview
2. **Query memories** for domain-specific deep dives
3. **Use semantic tools** for precise code navigation
4. **Reference symbols** for implementation details

## Task-Specific Loading Patterns

### Quick Questions (<5 minutes)

```markdown
✅ Layer 0 only: 00_bootstrap.md
✅ Serena semantic search for specific answers
❌ Avoid: Layer 1/2 loading for simple queries

Example:
- "What's the main entry point?" → 00_bootstrap.md
- "How do I run tests?" → search_for_pattern("pytest")
```

### New Contributor Onboarding (30-60 minutes)

```markdown
✅ Layer 0 + 1: Complete foundation
✅ Reference: setup-guide.md for environment
✅ Memory: "project_overview" + "suggested_commands"
✅ Semantic: get_symbols_overview("app/") for structure

Progression:
1. Load 00_bootstrap.md (project identity)
2. Load 01_working_context.md (patterns)
3. read_memory("project_overview")
4. Reference 02_reference/advanced/setup-guide.md
5. read_memory("suggested_commands")
```

### Feature Development (2-8 hours)

```markdown
✅ Layer 0 + 1: Development foundation
✅ Memory: Domain-specific (analyzer_architecture, etc.)
✅ Semantic: find_symbol for specific components
✅ Reference: Relevant symbol sections on-demand

Example - New Analyzer:
1. Load 00_bootstrap.md + 01_working_context.md
2. read_memory("analyzer_architecture")
3. get_symbols_overview("analyzers/example/")
4. find_symbol("AnalyzerInterface", include_body=True)
5. Reference symbols/analyzers.md as needed
```

### Bug Investigation (1-4 hours)

```markdown
✅ Layer 0 + 1: Context foundation
✅ Semantic: find_symbol + find_referencing_symbols
✅ Memory: Related domain knowledge
✅ Reference: Symbol docs for affected components

Example - Progress Reporting Bug:
1. Load 00_bootstrap.md + 01_working_context.md
2. find_symbol("ProgressManager", include_body=True)
3. find_referencing_symbols("ProgressManager", "terminal_tools/progress.py")
4. read_memory("progress_reporting_architecture")
5. Reference symbols/core_domain.md if needed
```

### Architecture Refactoring (1-3 days)

```markdown
✅ Layer 0 + 1: Foundation
✅ Layer 2: architecture_deep_dive.md
✅ Memory: All relevant domain memories
✅ Semantic: Comprehensive symbol analysis
✅ Reference: All relevant symbol sections

Example - Performance Optimization:
1. Load 00_bootstrap.md + 01_working_context.md
2. Load 02_reference/architecture_deep_dive.md
3. read_memory("performance_optimization_patterns")
4. read_memory("analyzer_architecture")
5. get_symbols_overview("analyzers/ngrams/")
6. Reference symbols/analyzers.md for implementation
```

### Code Review (30-90 minutes)

```markdown
✅ Layer 0 + 1: Review context
✅ Semantic: find_symbol for changed components
✅ Memory: "code_style_conventions" + domain-specific
✅ Reference: Relevant symbol sections

Example:
1. Load 00_bootstrap.md + 01_working_context.md
2. read_memory("code_style_conventions")
3. find_symbol for changed classes/functions
4. find_referencing_symbols for impact analysis
5. Reference appropriate symbol docs
```

## Decision Trees for Context Loading

### Task Complexity Assessment

**Simple Tasks** (1-2 components, <1 hour):

```text
→ Layer 0 only
→ Semantic search for specific answers
→ Single memory if domain-specific

Examples: Quick questions, command lookup, single file edits
```

**Moderate Tasks** (3-5 components, 1-4 hours):

```text
→ Layer 0 + 1
→ Domain-specific memory
→ Targeted semantic analysis
→ Reference sections on-demand

Examples: Feature development, bug fixes, component integration
```

**Complex Tasks** (5+ components, 4+ hours):

```text
→ Layer 0 + 1 + relevant Layer 2
→ Multiple domain memories
→ Comprehensive semantic analysis
→ Full reference section usage

Examples: Architecture changes, major refactoring, new subsystems
```

### Information Access Strategy

**Progressive Expansion**:

```text
1. Start minimal (Layer 0)
2. Add working context (Layer 1) for development
3. Query specific information as needed:
   - Semantic tools for code navigation
   - Memories for domain knowledge
   - Reference docs for comprehensive details
4. Never front-load information "just in case"
```

**Context Switching**:

```text
- New task type → Reset to Layer 0, rebuild contextually
- Task scope expansion → Add appropriate layers/tools
- Deep dive needed → Use semantic tools + memories
- Architecture questions → Layer 2 + comprehensive semantic analysis
```

## Token Budget and Performance

### Token Allocation

- **Layer 0**: ~300 tokens (essential startup)
- **Layer 1**: ~900 tokens (working patterns)
- **Active manual context**: <1,200 tokens total
- **Layer 2**: On-demand (unlimited detail)
- **Semantic queries**: As needed (efficient point queries)
- **Memory access**: Targeted (200-800 tokens per memory)

### Performance Guidelines

**Efficient Context Loading**:

- Load manual docs in batches (Layer 0 + 1 together)
- Use semantic tools for point queries, not browsing
- Access memories when domain knowledge is needed
- Reference Layer 2 docs only for comprehensive understanding

**Avoid Anti-Patterns**:

- ❌ Loading all documentation upfront
- ❌ Reading entire files when searching for specific information
- ❌ Loading memories "just in case"
- ❌ Using semantic tools for information already in manual docs

## Integration Strategy

### Manual Docs + Semantic Analysis Coordination

**Manual Docs Provide**:

- Structured overviews and mental models
- Essential patterns and workflows
- Task-specific guidance
- Token-efficient information density

**Semantic Analysis Provides**:

- Precise code location and relationships
- Real-time codebase exploration
- Dependency analysis and impact assessment
- Pattern discovery across the codebase

**Memories Provide**:

- Domain-specific deep knowledge
- AI-processed insights and patterns
- Historical context and rationale
- Cross-cutting concerns documentation

### Practical Coordination Examples

**New Analyzer Development**:

```text
1. Manual: 00_bootstrap.md + 01_working_context.md (patterns)
2. Memory: read_memory("analyzer_architecture") (domain knowledge)
3. Semantic: get_symbols_overview("analyzers/example/") (structure)
4. Semantic: find_symbol("AnalyzerInterface", include_body=True) (interface)
5. Reference: symbols/analyzers.md (comprehensive symbols)
```

**Performance Investigation**:

```text
1. Manual: 00_bootstrap.md + 01_working_context.md (context)
2. Memory: read_memory("performance_optimization_patterns") (strategies)
3. Semantic: search_for_pattern("MemoryManager") (usage patterns)
4. Semantic: find_symbol("MemoryManager", include_body=True) (implementation)
5. Reference: architecture_deep_dive.md (comprehensive architecture)
```

## Benefits and Outcomes

### Cognitive Benefits

1. **Reduced cognitive load**: Start with essentials, expand contextually
2. **Faster startup**: Immediate orientation without information overload
3. **Targeted expertise**: Access deep knowledge when needed
4. **Context relevance**: Information matches current task scope
5. **Sustainable learning**: Progressive complexity building

### Technical Benefits

1. **Token efficiency**: Minimal baseline context load
2. **Query optimization**: Point access to specific information
3. **Scalable architecture**: Easy to add new information layers
4. **Hybrid intelligence**: Manual structure + AI semantic analysis
5. **Just-in-time knowledge**: Access information when needed

### Development Workflow Benefits

1. **Faster task initiation**: Quick orientation and startup
2. **Contextual depth**: Match information detail to task complexity
3. **Efficient context switching**: Reset and rebuild appropriately
4. **Preserved completeness**: All project knowledge remains accessible
5. **Adaptive learning**: Context strategy improves with experience

## Implementation Guidelines

### For AI Assistants

**Session Startup Checklist**:

```markdown
1. ✅ Always load Layer 0 (00_bootstrap.md) first
2. ✅ Assess task complexity and scope
3. ✅ Load Layer 1 (01_working_context.md) for development work
4. ✅ Use decision trees to determine additional context needs
5. ✅ Access semantic tools and memories just-in-time
6. ✅ Reference Layer 2 docs only when comprehensive detail needed
```

**Context Management**:

- Reset to Layer 0 when switching to unrelated tasks
- Build context progressively based on task requirements
- Use semantic queries for point information access
- Validate context relevance before expanding

**Tool Selection Strategy**:

- **Manual docs**: For mental models and patterns
- **Semantic tools**: For code navigation and relationships
- **Memories**: For domain expertise and deep knowledge
- **Reference docs**: For comprehensive implementation details

### For Human Developers

**Documentation Consumption**:

1. Start with bootstrap context for project orientation
2. Load working context for active development
3. Query semantic tools for specific code questions
4. Access memories for domain-specific knowledge
5. Reference detailed docs only when needed

**Context Loading Strategy**:

- Match information depth to task complexity
- Use progressive disclosure to manage cognitive load
- Leverage hybrid approach (manual + semantic + memories)
- Reset context when switching task domains

## Maintenance and Evolution

### Documentation Hygiene

**Layer 0 Maintenance**:

- Keep under 400 tokens
- Update only for fundamental project changes
- Focus on essential orientation information

**Layer 1 Maintenance**:

- Keep under 1,200 tokens total (with Layer 0)
- Update for core pattern changes
- Maintain focus on common development workflows

**Layer 2 Evolution**:

- Add new reference sections as needed
- Split large sections when they exceed usefulness
- Organize by logical topic boundaries

**Memory Integration**:

- Update memories when domain knowledge changes
- Add new memories for emerging patterns
- Archive obsolete memories

### Success Metrics

**Context Loading Efficiency**:

- Reduced time-to-first-productive-action
- Minimal irrelevant information loading
- High context relevance for active tasks

**Information Accessibility**:

- All project knowledge remains findable
- Semantic tools provide efficient code navigation
- Memories offer domain-specific insights
- Reference docs provide comprehensive detail

**Development Workflow**:

- Faster project onboarding
- Efficient context switching between tasks
- Reduced cognitive load during development
- Improved decision-making through targeted information access

## File Migration from Legacy Structure

**Completed Migrations**:

- `README.md` → Split between `00_bootstrap.md` and `01_working_context.md`
- `architecture-overview.md` → `02_reference/architecture_deep_dive.md`
- `symbol-reference.md` → Split into `02_reference/symbols/` sections
- `setup-guide.md` → `02_reference/advanced/setup-guide.md`

**Semantic Knowledge Integration**:

- Legacy docs content → Enhanced with `.serena/memories/` insights
- Symbol navigation → Augmented with semantic tool examples
- Task guidance → Expanded with decision trees and loading patterns
