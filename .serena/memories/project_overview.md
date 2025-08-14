# Project Overview: Mango Tango CLI

## Purpose

CIB 🥭 (Mango Tango CLI) is a Python terminal-based tool for performing data analysis and visualization, specifically designed for social media data analysis. It provides a modular and extensible architecture that allows developers to contribute new analysis modules while maintaining a consistent user experience.

## Core Problem

The tool addresses the common pain point of moving from private data analysis scripts to shareable tools. It prevents inconsistent UX across analyses, code duplication, and bugs by providing a clear separation between core application logic and analysis modules.

## Key Features

- **Terminal-based interface** for data analysis workflows with enhanced progress reporting
- **Modular analyzer system** (Primary, Secondary, Web Presenters)
- **Hierarchical progress reporting** eliminates silent processing periods
- **Streaming optimization** for memory-efficient large dataset processing
- Built-in data import/export capabilities
- Interactive web dashboards using Dash and Shiny
- Support for various data formats (CSV, Excel, Parquet)
- **Enhanced analyzers**: Hashtag analysis, n-gram analysis with advanced tokenization, temporal analysis
- **Comprehensive testing framework** with mock contexts and data management
- Multi-tenancy support

## Recent Enhancements

### Enhanced Progress Reporting System
- **Hierarchical progress**: Main steps with granular sub-steps
- **Real-time feedback** during long-running operations
- **Error isolation** to specific sub-steps for better debugging
- **Memory-aware progress calculation** adapts to dataset size

### N-gram Analyzer Improvements
- **Streaming optimization** for memory-efficient processing
- **Enhanced tokenization** with configurable parameters
- **Vectorized n-gram generation** with progress callbacks
- **Hierarchical organization** (ngrams_base → ngram_stats → ngram_web)

### Testing Infrastructure
- **Comprehensive testing framework** with standardized patterns
- **Mock context system** for isolated analyzer testing
- **Test data management** classes for various formats
- **DataFrame comparison utilities** for precise validation

## Tech Stack

- **Language**: Python 3.12
- **Data Processing**: Polars (primary), Pandas, PyArrow
- **Progress Reporting**: Rich library for hierarchical terminal display
- **Web Framework**: Dash, Shiny for Python
- **CLI**: Inquirer for interactive prompts
- **Data Storage**: TinyDB, Parquet files
- **Visualization**: Plotly
- **Export**: XlsxWriter for Excel output
- **Testing**: pytest with custom testing framework

## Architecture Domains

1. **Core Domain**: Application logic, Terminal Components (with enhanced progress), Storage IO
2. **Edge Domain**: Data import/export, Semantic Preprocessor, Testing framework
3. **Content Domain**: Analyzers (Primary/Secondary with streaming), Web Presenters

## Development Philosophy

- **User Experience First**: No silent processing periods, clear progress feedback
- **Memory Efficiency**: Streaming operations for large datasets
- **Modularity**: Clear separation between analysis and infrastructure
- **Testability**: Comprehensive testing with mock contexts
- **Extensibility**: Easy addition of new analyzers with standardized patterns