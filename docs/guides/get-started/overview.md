
CIB Mango Tree is a Python-based, open source toolkit for detecting coordinated inauthentic behavior (CIB) in social media datasets. It is designed for researchers, data journalists, fact-checkers, and watchdogs working to identify manipulation and inauthentic activity online.

Through an interactive terminal interface, users can import datasets, check data quality, create analysis projects, and explore results in interactive dashboards without having to writing code. This makes peer-reviewed CIB analysis methods accessible to users with little to no programming experience.

!["Application welcome screen and logo in the terminal"](../../img/cibmt_splash_logo.png)
/// caption
The welcome screen of the application
///

## Tech Stack

CIB Mango Tree relies on the following packages and data science tooling from the Python ecosystem:  

| Domain | Technologies |
|----------|--------------|
| Core | Python 3.12, Inquirer (TUI), TinyDB (metadata), Starlette & Uvicorn (web-server) |
| Data | Polars/Pandas, PyArrow, Parquet files |
| Web | Dash, Shiny for Python, Plotly |
| Dev Tools | Black, isort, pytest, PyInstaller |
