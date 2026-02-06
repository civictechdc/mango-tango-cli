
CIB Mango Tree is a Python-based interactive toolkit for social media data
analysis and visualization. The terminal application allows the user to navigate in a terminal (terminal user interface), select and import a dataset (tabular data), check data quality, create a project, select an analysis, and explore the analysis results in an interactive dashboard.
It is aimed at users with little to now coding experience. 

!["Application welcome screen and logo in the terminal"](../../img/cibmt_splash_logo.png)
/// caption
The welcome screen of the application
///

## Purpose & domain

- Analysis of social media datasets (tabular data) and interactive exploration of results
- Modular architecture: Clear separation between data import/export,
  analysis, and presentation
- Interactive workflows: Terminal-based user interface with brower-based dashboard capabilities
- Extensible design: Plugin-like analyzer system for expansion

## Tech Stack

- Core: Python 3.12, Inquirer (TUI), TinyDB (metadata), Starlette & Uvicorn (web-server)
- Data: Polars/Pandas, PyArrow, Parquet files
- Web: Dash, Shiny for Python, Plotly
- Dev Tools: Black, isort, pytest, PyInstaller
