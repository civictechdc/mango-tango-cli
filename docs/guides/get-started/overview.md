# Mango Tango CLI

## Repository Overview

**Mango Tango CLI** is a Python terminal-based tool for social media data
analysis and visualization. It provides a modular, extensible architecture
that separates core application logic from analysis modules, ensuring
consistent UX while allowing easy contribution of new analyzers.
The following documentation in this section is meant to provide a
general overview of how the codebase for the project is structured,
and to provide some context on patterns used throughout the project.

### Purpose & Domain

- **Social Media Analytics**: Hashtag analysis, n-gram analysis, temporal
  patterns, user coordination
- **Modular Architecture**: Clear separation between data import/export,
  analysis, and presentation
- **Interactive Workflows**: Terminal-based UI with web dashboard capabilities
- **Extensible Design**: Plugin-like analyzer system for easy expansion

### Tech Stack

- **Core**: Python 3.12, Inquirer (CLI), TinyDB (metadata), Starlette & Uvicorn (web-server)
- **Data**: Polars/Pandas, PyArrow, Parquet files
- **Web**: Dash, Shiny for Python, Plotly, React
- **Dev Tools**: Black, isort, pytest, PyInstaller
