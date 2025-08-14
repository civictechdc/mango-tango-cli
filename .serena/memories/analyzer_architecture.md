# Analyzer Architecture

## Overview

The analyzer system is the core content domain of Mango Tango CLI, designed for modularity and extensibility. Recent enhancements include hierarchical progress reporting and streaming optimization for large datasets.

## Analyzer Types

### Primary Analyzers

- **Purpose**: Core data processing and analysis
- **Input**: Raw imported data (CSV/Excel → Parquet)
- **Output**: Normalized, non-duplicated analysis results
- **Context**: Receives input file path, preprocessing method, output path, **progress manager**
- **Examples**:
  - `hashtags` - Hashtag extraction and analysis
  - `ngrams_base` - N-gram generation with enhanced progress reporting and streaming optimization
  - `temporal` - Time-based aggregation
  - `time_coordination` - User coordination analysis

### Secondary Analyzers

- **Purpose**: Transform primary outputs into user-friendly formats
- **Input**: Primary analyzer outputs
- **Output**: User-consumable tables/reports
- **Context**: Receives primary output path, provides secondary output path
- **Examples**:
  - `ngram_stats` - N-gram statistics with chunked processing
  - `hashtags_web/analysis.py:secondary_analyzer()` - Hashtag summary statistics

### Web Presenters

- **Purpose**: Interactive dashboards and visualizations
- **Input**: Primary + Secondary analyzer outputs
- **Framework**: Dash or Shiny for Python
- **Context**: Receives all relevant output paths + Dash/Shiny app object
- **Examples**:
  - `hashtags_web` - Hashtag dashboard
  - `ngram_web` - N-gram exploration dashboard with word matching
  - `temporal_barplot` - Temporal visualization

## Enhanced Progress Reporting

### Hierarchical Progress System

Analyzers now support streamlined progress reporting through `ProgressManager`:

- **Main steps**: High-level analysis phases (preprocess, tokenize, generate, write)
- **Progress tracking**: Clean, efficient real-time feedback
- **Textual-native design**: Direct, performant progress updates
- **Error handling**: Immediate visibility into operation status

### N-gram Analyzer Enhancements

The `ngrams_base` analyzer features enhanced final-stage progress reporting:

- **Enhanced write functions**: Break down write operations into 4 observable sub-steps each
- **Streaming optimization**: Memory-efficient processing for large datasets
- **Vectorized generation**: Optimized n-gram creation with progress callbacks
- **Automatic scaling**: Progress granularity adapts to dataset size

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
- **Progress manager** (for hierarchical progress reporting)
- Application hooks (for web presenters)
- Configuration parameters

## Data Flow

1. **Import**: CSV/Excel → Parquet via importers
2. **Preprocess**: Semantic preprocessing applies column mappings **(with progress)**
3. **Primary**: Raw data → structured analysis results **(with hierarchical progress)**
4. **Secondary**: Primary results → user-friendly outputs
5. **Web**: All outputs → interactive dashboards
6. **Export**: Results → user-selected formats (XLSX, CSV, etc.)

## Directory Structure

### N-gram Analyzer Hierarchy

```bash
analyzers/ngrams/
├── ngrams_base/         # Primary analyzer
│   ├── main.py         # Enhanced with progress reporting
│   └── interface.py    # Input/output definitions
├── ngram_stats/        # Secondary analyzer
│   ├── main.py         # Statistics calculation
│   └── interface.py    # Interface definition
├── ngram_web/          # Web presenter
│   ├── factory.py      # Dashboard creation
│   └── interface.py    # Web interface
└── test_data/          # Test files co-located
```

## Key Components

- `analyzer_interface/` - Base interface definitions
- `analyzers/suite` - Registry of all available analyzers
- `terminal_tools/progress.py` - Hierarchical progress reporting system
- Context objects for dependency injection
- Parquet-based data persistence between stages
- `testing/` framework for comprehensive analyzer testing

## Recent Architectural Enhancements

- **Hierarchical Progress**: Eliminates silent processing periods during final stages
- **Streaming Optimization**: Memory-efficient processing for large datasets
- **Enhanced Testing**: Comprehensive testing framework with mock contexts
- **Modular Organization**: N-gram analyzers reorganized into hierarchical structure
