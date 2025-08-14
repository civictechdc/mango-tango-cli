# Mango Tango CLI - Bootstrap Context

## Project Identity

Mango Tango CLI is a modular, terminal-based social media analytics platform designed for flexible, context-aware data exploration. It enables researchers and analysts to perform deep, adaptive analysis of social media datasets through a plugin-based analyzer architecture for coordinated inauthentic behavior (CIB) in datasets of online activity.

## Tech Stack Essentials

- Language: Python 3.12
- Data Processing: Polars, Parquet
- UI: Inquirer, Rich
- Core Libraries: Dash, Shiny, Plotly

## Architectural Pattern

Dependency injection through context objects enables loose coupling between application layers, allowing seamless extension and testing of analysis modules with minimal interdependencies.

## Primary Entry Points

- `mangotango.py`: Application bootstrap
- `main_menu()`: Interactive terminal workflow
- Analyzer suite: Pluggable, declarative analysis modules

## Behavioral Requirement

CRITICAL: Apply brutal honesty - challenge assumptions, question designs, and provide direct, analytical feedback without reservation.
