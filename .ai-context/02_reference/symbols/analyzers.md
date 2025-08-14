# Analyzer System Symbols

## Built-in Analyzers

### Primary Analyzers (core data processing)

- `hashtags` - `analyzers/hashtags/main.py:main()` - Hashtag extraction and analysis
- `ngrams_base` - `analyzers/ngrams/ngrams_base/main.py:main()` - N-gram generation with enhanced progress reporting
  - Enhanced write functions: `_enhanced_write_message_ngrams()`, `_enhanced_write_ngram_definitions()`, `_enhanced_write_message_metadata()`
  - Streaming optimization: `_stream_unique_batch_accumulator()`, `_stream_unique_to_temp_file()`
  - Vectorized n-gram generation: `_generate_ngrams_vectorized()`, `_generate_ngrams_simple()`
- `temporal` - `analyzers/temporal/main.py:main()` - Time-based aggregation
- `time_coordination` - `analyzers/time_coordination/main.py:main()` - User coordination analysis

### Secondary Analyzers (result transformation)

- `ngram_stats` - `analyzers/ngrams/ngram_stats/main.py:main()` - N-gram statistics calculation
  - Chunked processing: `_process_ngram_chunk()`, `_create_sample_full_report_row()`
- `hashtags_web/analysis.py:secondary_analyzer()` - Hashtag summary statistics

### Web Presenters (interactive dashboards)

- `hashtags_web` - `analyzers/hashtags_web/factory.py:factory()` - Hashtag dashboard
- `ngram_web` - `analyzers/ngrams/ngram_web/factory.py:factory()` - N-gram exploration dashboard
  - Word matching: `create_word_matcher()`
- `temporal_barplot` - `analyzers/temporal_barplot/factory.py:factory()` - Temporal visualization

## Performance Optimization Components

### Memory Management (`analyzers/ngrams/memory_strategies.py`)

- `ExternalSortUniqueExtractor` - External sorting for memory-constrained n-gram processing
  - Disk-based unique extraction with configurable chunk sizes
  - Temporary file management and cleanup
  - Memory-aware processing with fallback strategies
- `extract_unique_external_sort()` - High-level function for external sorting operations

### Fallback Processors (`analyzers/ngrams/fallback_processors.py`)

- `generate_ngrams_disk_based()` - Disk-based n-gram generation for large datasets
- `_generate_ngrams_minimal_memory()` - Minimal memory approach for constrained systems
- `stream_unique_memory_optimized()` - Memory-optimized streaming unique extraction

## Analyzer Registration

- `analyzers.suite` - `analyzers/__init__.py` - Central registry of all analyzers

## Data Import (`importing/`)

### `Importer` base class - `importing/importer.py`

Base interface for data importers

- `ImporterSession` - Stateful import process management
- `SessionType` - Enum for import session types

### Concrete Importers

- `CSVImporter` - `importing/csv.py` - CSV file import with encoding detection
- `ExcelImporter` - `importing/excel.py` - Excel file import with sheet selection

## Entry Points

### Main Application

- `mangotango.py` - Application bootstrap and initialization
  - `freeze_support()` - Multiprocessing setup
  - `enable_windows_ansi_support()` - Terminal color support
  - Storage initialization with app metadata
  - Component orchestration (splash, main_menu)

### Module Entry Point

- `python -m mangotango` - Standard execution command
- `python -m mangotango --noop` - No-operation mode for testing

## Integration Points

### External Libraries Integration

- **Polars**: Primary data processing engine
- **Dash**: Web dashboard framework integration
- **Shiny**: Modern web UI framework integration
- **TinyDB**: Lightweight JSON database
- **Inquirer**: Interactive terminal prompts

### File System Integration

- **Parquet**: Native data format for all analysis data
- **Workspace**: Project-based file organization
- **Exports**: Multi-format output generation (XLSX, CSV, Parquet)

### Web Framework Hooks

- `AnalysisWebServerContext` - Web server lifecycle management
- Dashboard factory pattern for creating web applications
- Background server process management
