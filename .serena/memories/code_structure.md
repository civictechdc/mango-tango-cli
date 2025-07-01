# Code Structure

## Entry Point

- `mangotango.py` - Main entry point, bootstraps the application with Storage, App, and terminal components

## Core Modules

### App (`app/`)

- `app.py` - Main App class with workspace capabilities
- `app_context.py` - AppContext class for dependency injection
- `project_context.py` - ProjectContext for project-specific operations
- `analysis_context.py` - AnalysisContext and AnalysisRunProgressEvent for analysis execution
- `analysis_output_context.py` - Context for handling analysis outputs
- `analysis_webserver_context.py` - Context for web server operations
- `settings_context.py` - SettingsContext for configuration management

### Components (`components/`)

Terminal UI components using inquirer for interactive flows:

- `main_menu.py` - Main application menu
- `splash.py` - Application splash screen
- `new_project.py` - Project creation flow
- `select_project.py` - Project selection interface
- `project_main.py` - Project main menu
- `new_analysis.py` - Analysis creation flow
- `select_analysis.py` - Analysis selection interface
- `analysis_main.py` - Analysis main menu
- `analysis_params.py` - Parameter customization interface
- `analysis_web_server.py` - Web server management
- `export_outputs.py` - Output export functionality
- `context.py` - ViewContext class for UI state

### Storage (`storage/`)

- `__init__.py` - Storage class, models (ProjectModel, AnalysisModel, etc.)
- `file_selector.py` - File selection state management

### Analyzers (`analyzers/`)

Modular analysis system:

- `__init__.py` - Main analyzer suite registration
- `example/` - Example analyzer implementation
- `hashtags/` - Hashtag analysis (primary analyzer)
- `hashtags_web/` - Hashtag web dashboard (web presenter)
- `ngrams/` - N-gram analysis (primary analyzer)
- `ngram_stats/` - N-gram statistics (secondary analyzer)
- `ngram_web/` - N-gram web dashboard (web presenter)
- `temporal/` - Temporal analysis (primary analyzer)
- `temporal_barplot/` - Temporal visualization (web presenter)
- `time_coordination/` - Time coordination analysis

### Importing (`importing/`)

- `importer.py` - Base Importer and ImporterSession classes
- `csv.py` - CSV import implementation
- `excel.py` - Excel import implementation
