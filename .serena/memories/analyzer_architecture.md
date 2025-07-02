# Analyzer Architecture

## Overview

The analyzer system is the core content domain of Mango Tango CLI, designed for modularity and extensibility.

## Analyzer Types

### Primary Analyzers

- **Purpose**: Core data processing and analysis
- **Input**: Raw imported data (CSV/Excel → Parquet)
- **Output**: Normalized, non-duplicated analysis results
- **Context**: Receives input file path, preprocessing method, output path
- **Examples**: hashtags, ngrams, temporal, time_coordination

### Secondary Analyzers

- **Purpose**: Transform primary outputs into user-friendly formats
- **Input**: Primary analyzer outputs
- **Output**: User-consumable tables/reports
- **Context**: Receives primary output path, provides secondary output path
- **Examples**: ngram_stats (processes ngrams output)

### Web Presenters

- **Purpose**: Interactive dashboards and visualizations
- **Input**: Primary + Secondary analyzer outputs
- **Framework**: Dash or Shiny for Python
- **Context**: Receives all relevant output paths + Dash/Shiny app object
- **Examples**: hashtags_web, ngram_web, temporal_barplot

## Interface Pattern

Each analyzer defines an interface in `interface.py`:

```python
interface = AnalyzerInterface(
    input=AnalyzerInput(...),  # Define required columns/semantics
    params=[...],              # User-configurable parameters
    outputs=[...],             # Output table schemas
    kind="primary"             # or "secondary"/"web"
)
```

## Context Pattern

All analyzers receive context objects providing:

- File paths (input/output)
- Preprocessing methods
- Application hooks (for web presenters)
- Configuration parameters

## Data Flow

1. **Import**: CSV/Excel → Parquet via importers
2. **Preprocess**: Semantic preprocessing applies column mappings
3. **Primary**: Raw data → structured analysis results
4. **Secondary**: Primary results → user-friendly outputs
5. **Web**: All outputs → interactive dashboards
6. **Export**: Results → user-selected formats (XLSX, CSV, etc.)

## Key Components

- `analyzer_interface/` - Base interface definitions
- `analyzers/suite` - Registry of all available analyzers
- Context objects for dependency injection
- Parquet-based data persistence between stages
