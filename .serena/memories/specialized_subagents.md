# Specialized Subagent System

## Overview

The Mango Tango CLI project employs a specialized subagent system designed to handle domain-specific development tasks with deep expertise. This system replaces generic global agents with focused specialists that understand both the project architecture and their technology domains.

## Agent Specializations

### 1. Analytics Specialist Agent

**Domain Expertise**: Data science, statistical analysis, algorithm optimization

**Technology Stack**:

- **Primary**: Polars, Pandas, PyArrow, NumPy
- **Analysis**: Statistical modeling, n-gram analysis, hashtag extraction
- **Performance**: Memory optimization, chunking strategies, vectorized operations
- **Testing**: pytest-benchmark, performance validation

**Typical Use Cases**:

- Implementing new primary analyzers
- Optimizing existing analysis algorithms
- Memory-aware processing strategies
- Statistical validation and testing
- Data transformation and aggregation

**Project Integration**:

- **Content Domain**: Primary analyzer development (`analyzers/*/main.py`)
- **Performance Layer**: Memory strategies, fallback processors
- **Testing**: Analysis validation and benchmarking

**Key Responsibilities**:

- Algorithm efficiency optimization
- Large dataset processing strategies
- Statistical method implementation
- Performance bottleneck identification
- Data quality validation

### 2. Data Pipeline Optimizer Agent

**Domain Expertise**: Data engineering, ETL processes, storage optimization

**Technology Stack**:

- **Storage**: Parquet, TinyDB, file system management
- **Processing**: Streaming, chunking, batch operations
- **Formats**: CSV, Excel, JSON import/export
- **Optimization**: Memory management, disk I/O, caching

**Typical Use Cases**:

- Import/export pipeline optimization
- Storage layer enhancements
- Data format conversions
- Preprocessing pipeline design
- Performance monitoring and tuning

**Project Integration**:

- **Edge Domain**: Importers (`importing/`), semantic preprocessing
- **Storage Layer**: Data persistence (`storage/`)
- **Core Domain**: Workspace management, file operations

**Key Responsibilities**:

- Data pipeline architecture
- Import/export optimization
- Storage format decisions
- Memory pressure management
- Data integrity validation

### 3. Terminal UI Specialist Agent

**Domain Expertise**: CLI design, user experience, terminal interfaces

**Technology Stack**:

- **CLI**: Inquirer, Rich, terminal formatting
- **UX**: Interactive prompts, progress reporting, error handling
- **Display**: Progress bars, status indicators, hierarchical feedback
- **Platform**: Cross-platform terminal compatibility

**Typical Use Cases**:

- Terminal interface improvements
- Progress reporting enhancements
- User flow optimization
- CLI accessibility features
- Interactive component development

**Project Integration**:

- **Core Domain**: Terminal components (`components/`)
- **Infrastructure**: Progress reporting (`terminal_tools/`)
- **User Experience**: Menu flows, input validation

**Key Responsibilities**:

- User interface design
- Progress reporting architecture
- Terminal accessibility
- User flow optimization
- Error message clarity

### 4. Dashboard Engineer Agent

**Domain Expertise**: Web visualization, interactive dashboards, frontend development

**Technology Stack**:

- **Frameworks**: Dash, Shiny for Python, Plotly
- **Visualization**: Interactive charts, data exploration interfaces
- **Web**: HTML/CSS generation, responsive design
- **Integration**: Server lifecycle, background processes

**Typical Use Cases**:

- Web presenter development
- Interactive dashboard creation
- Visualization optimization
- Dashboard server management
- User interaction design

**Project Integration**:

- **Content Domain**: Web presenters (`analyzers/*/factory.py`)
- **Application Layer**: Web server context management
- **Analysis Pipeline**: Dashboard integration with analysis outputs

**Key Responsibilities**:

- Interactive visualization design
- Dashboard performance optimization
- Web framework integration
- User interaction patterns
- Server lifecycle management

### 5. Analyzer Framework Specialist Agent

**Domain Expertise**: Framework design, plugin architecture, extensibility

**Technology Stack**:

- **Architecture**: Interface patterns, context injection, modular design
- **Validation**: Pydantic models, schema validation
- **Integration**: Plugin registration, analyzer discovery
- **Testing**: Framework testing patterns, mock contexts

**Typical Use Cases**:

- Analyzer interface design
- Framework extensibility improvements
- Context system enhancements
- Plugin architecture development
- Integration pattern standardization

**Project Integration**:

- **Content Domain**: Analyzer system (`analyzers/__init__.py`)
- **Core Domain**: Context patterns (`app/*_context.py`)
- **Testing**: Framework testing utilities (`testing/`)

**Key Responsibilities**:

- Analyzer interface evolution
- Context system design
- Framework extensibility
- Integration pattern enforcement
- Testing framework development

## Agent Collaboration Patterns

### Multi-Domain Task Examples

#### New Analyzer Development

1. **Analyzer Framework Specialist**: Design interface and context requirements
2. **Analytics Specialist**: Implement core algorithm and optimization
3. **Terminal UI Specialist**: Add progress reporting and user feedback
4. **Dashboard Engineer**: Create interactive visualization
5. **Data Pipeline Optimizer**: Optimize data flow and storage

#### Performance Optimization Initiative

1. **Data Pipeline Optimizer**: Analyze data flow bottlenecks
2. **Analytics Specialist**: Optimize algorithm implementations
3. **Terminal UI Specialist**: Enhance progress reporting for transparency
4. **Framework Specialist**: Update context system for performance metrics

#### User Experience Enhancement

1. **Terminal UI Specialist**: Lead interface design improvements
2. **Dashboard Engineer**: Enhance web interface consistency
3. **Framework Specialist**: Standardize interaction patterns
4. **Data Pipeline Optimizer**: Optimize response times

### Handoff Protocols

#### From Analytics Specialist to Dashboard Engineer

- **Deliverable**: Optimized analysis outputs with documented schema
- **Context**: Performance characteristics, data volume expectations
- **Requirements**: Visualization-ready data formats

#### From Framework Specialist to Analytics Specialist

- **Deliverable**: Interface requirements and context specifications
- **Context**: Integration patterns, validation requirements
- **Requirements**: Implementation guidelines and constraints

#### From Data Pipeline to Terminal UI

- **Deliverable**: Performance metrics and operation timings
- **Context**: User feedback requirements for long operations
- **Requirements**: Progress reporting integration points

## Technology Integration Matrix

### Core Domain Integration

| Agent | Application Layer | Terminal Components | Storage IO |
|-------|------------------|-------------------|------------|
| **Analytics Specialist** | Context usage | Progress integration | Data format optimization |
| **Data Pipeline Optimizer** | Storage orchestration | File selection UX | Direct storage implementation |
| **Terminal UI Specialist** | User flow coordination | Primary responsibility | Status reporting |
| **Dashboard Engineer** | Web server context | Terminal-web handoff | Output data consumption |
| **Framework Specialist** | Context architecture | Interface standards | Model validation |

### Technology Stack Ownership

#### Primary Ownership

- **Polars/Pandas**: Analytics Specialist
- **Dash/Plotly**: Dashboard Engineer
- **Inquirer/Rich**: Terminal UI Specialist
- **Parquet/TinyDB**: Data Pipeline Optimizer
- **Pydantic/Interfaces**: Framework Specialist

#### Secondary Knowledge

- **Performance Optimization**: All agents (domain-specific)
- **Testing**: All agents (domain-specific patterns)
- **Context System**: Framework Specialist (primary), others (usage)
- **Progress Reporting**: Terminal UI Specialist (primary), others (integration)

## Decision Framework

### When to Engage Specific Agents

#### Analytics Specialist

- Algorithm implementation or optimization
- Performance issues with data processing
- Statistical analysis requirements
- Memory usage optimization
- Large dataset handling

#### Data Pipeline Optimizer

- Import/export functionality changes
- Storage layer modifications
- Data format decisions
- Pipeline performance issues
- File system integration

#### Terminal UI Specialist

- User interface improvements
- Progress reporting enhancements
- User experience issues
- CLI accessibility concerns
- Interactive component needs

#### Dashboard Engineer

- Web visualization development
- Interactive dashboard creation
- Dashboard performance issues
- Visualization framework integration
- User interaction design

#### Framework Specialist

- Analyzer interface changes
- Context system modifications
- Plugin architecture evolution
- Integration pattern standardization
- Testing framework updates

### Complex Task Delegation Strategy

#### High-Level Process

1. **Primary Agent Identification**: Determine which agent owns the core domain
2. **Supporting Agent Assessment**: Identify agents needed for cross-cutting concerns
3. **Coordination Planning**: Establish handoff points and shared deliverables
4. **Integration Validation**: Ensure all agents understand project architecture integration

#### Example: New Analysis Type Development

**Phase 1: Requirements and Architecture**

- **Lead**: Framework Specialist
- **Supporting**: Analytics Specialist (algorithm requirements)
- **Deliverable**: Interface specification and context requirements

**Phase 2: Core Implementation**

- **Lead**: Analytics Specialist
- **Supporting**: Data Pipeline Optimizer (performance optimization)
- **Deliverable**: Optimized analyzer implementation

**Phase 3: User Interface Integration**

- **Lead**: Terminal UI Specialist
- **Supporting**: Framework Specialist (interface compliance)
- **Deliverable**: Progress reporting and user flow integration

**Phase 4: Visualization Development**

- **Lead**: Dashboard Engineer
- **Supporting**: Analytics Specialist (data format consultation)
- **Deliverable**: Interactive dashboard implementation

**Phase 5: Integration Testing**

- **Coordination**: All agents
- **Focus**: End-to-end validation and performance verification

## Best Practices

### Agent Selection Guidelines

1. **Start with the primary domain owner** for the core task
2. **Identify cross-cutting concerns** early in planning
3. **Establish clear handoff criteria** between agents
4. **Maintain architectural consistency** across agent contributions
5. **Validate integration points** before task completion

### Communication Patterns

1. **Domain Expertise Sharing**: Each agent documents their domain-specific decisions
2. **Integration Requirements**: Clear specification of interaction points
3. **Performance Constraints**: Shared understanding of system limitations
4. **Testing Strategies**: Coordinated approach to validation

### Quality Assurance

1. **Domain-Specific Review**: Each agent validates their domain aspects
2. **Integration Testing**: Cross-agent collaboration on system testing
3. **Performance Validation**: Shared responsibility for performance characteristics
4. **Documentation Standards**: Consistent documentation across agent contributions

## Future Evolution

### Agent Specialization Refinement

As the project evolves, agent specializations may be refined based on:

- **Technology Stack Changes**: New frameworks or tools
- **Architecture Evolution**: Changes in core/edge/content domains
- **Performance Requirements**: New optimization needs
- **User Experience Insights**: Enhanced UX requirements

### New Agent Considerations

Potential future agents based on project growth:

- **Security Specialist**: For security-focused features
- **API Integration Specialist**: For external service integration
- **Mobile/Web Frontend Specialist**: For cross-platform expansion
- **Machine Learning Specialist**: For advanced analytics features

### Integration Pattern Evolution

The specialized agent system should evolve with:

- **Improved handoff protocols** based on experience
- **Enhanced collaboration patterns** for complex tasks
- **Refined decision frameworks** for agent selection
- **Better integration testing** strategies

This specialized subagent system ensures that domain expertise is properly leveraged while maintaining architectural consistency and project integration standards.
