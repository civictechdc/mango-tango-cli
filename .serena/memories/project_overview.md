# Project Overview: Mango Tango CLI

## Purpose

CIB 🥭 (Mango Tango CLI) is a Python terminal-based tool for performing data analysis and visualization, specifically designed for social media data analysis. It provides a modular and extensible architecture that allows developers to contribute new analysis modules while maintaining a consistent user experience.

## Core Problem

The tool addresses the common pain point of moving from private data analysis scripts to shareable tools. It prevents inconsistent UX across analyses, code duplication, and bugs by providing a clear separation between core application logic and analysis modules.

## Key Features

- Terminal-based interface for data analysis workflows
- Modular analyzer system (Primary, Secondary, Web Presenters)
- Built-in data import/export capabilities
- Interactive web dashboards using Dash and Shiny
- Support for various data formats (CSV, Excel, Parquet)
- Hashtag analysis, n-gram analysis, temporal analysis
- Multi-tenancy support

## Tech Stack

- **Language**: Python 3.12
- **Data Processing**: Polars, Pandas, PyArrow
- **Web Framework**: Dash, Shiny for Python
- **CLI**: Inquirer for interactive prompts
- **Data Storage**: TinyDB, Parquet files
- **Visualization**: Plotly
- **Export**: XlsxWriter for Excel output

## Architecture Domains

1. **Core Domain**: Application logic, Terminal Components, Storage IO
2. **Edge Domain**: Data import/export, Semantic Preprocessor
3. **Content Domain**: Analyzers (Primary/Secondary), Web Presenters
