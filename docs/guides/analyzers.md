# Analyzers Guide

Analyzers are the core data processing components of the platform. They follow a three-tier architecture that separates data processing, analysis, and presentation concerns.

## Architecture Overview

The analyzer system consists of three types of components:

1. **Primary Analyzer**: Performs the core data analysis and outputs structured results
2. **Secondary Analyzer**: Processes primary analyzer outputs for specific use cases or exports
3. **Web Presenter**: Creates interactive dashboards and visualizations

This separation allows for:

- Reusable analysis logic
- Multiple presentation formats for the same analysis
- Collaborative development where different contributors can focus on different layers

## Primary Analyzers

Primary analyzers perform the core data analysis. They read user input data, process it according to their algorithm, and output structured results in parquet format.

### Interface Definition

Every primary analyzer must define an interface that specifies:

- Input columns required from the user
- Parameters the analyzer accepts
- Output tables the analyzer produces

```python
from analyzer_interface import (
    AnalyzerInput,
    AnalyzerInterface, 
    AnalyzerOutput,
    AnalyzerParam,
    InputColumn,
    OutputColumn,
    IntegerParam
)

interface = AnalyzerInterface(
    id="example_analyzer",  # Must be globally unique
    version="0.1.0",
    name="Example Analyzer",
    short_description="Counts characters in messages",
    long_description="""
This analyzer demonstrates the basic structure by counting 
characters in each message and marking long messages.
    """,
    input=AnalyzerInput(
        columns=[
            InputColumn(
                name="message_id",
                human_readable_name="Unique Message ID", 
                data_type="identifier",
                description="The unique identifier of the message",
                name_hints=["post", "message", "tweet", "id"]
            ),
            InputColumn(
                name="message_text",
                human_readable_name="Message Text",
                data_type="text", 
                description="The text content of the message",
                name_hints=["message", "text", "content", "body"]
            )
        ]
    ),
    params=[
        AnalyzerParam(
            id="fudge_factor",
            human_readable_name="Character Count Adjustment",
            description="Adds to the character count for testing purposes",
            type=IntegerParam(min=-1000, max=1000),
            default=0
        )
    ],
    outputs=[
        AnalyzerOutput(
            id="character_count",
            name="Character Count Per Message", 
            internal=True,  # Not shown in export list
            columns=[
                OutputColumn(name="message_id", data_type="integer"),
                OutputColumn(name="character_count", data_type="integer")
            ]
        )
    ]
)
```

### Implementation

The main function receives a context object with access to input data and output paths:

```python
import polars as pl
from analyzer_interface.context import PrimaryAnalyzerContext
from terminal_tools import ProgressReporter

def main(context: PrimaryAnalyzerContext):
    # Read and preprocess input data
    input_reader = context.input()
    df_input = input_reader.preprocess(pl.read_parquet(input_reader.parquet_path))
    
    # Access parameters
    fudge_factor = context.params.get("fudge_factor")
    assert isinstance(fudge_factor, int), "Fudge factor must be an integer"
    
    # Perform analysis with progress reporting
    with ProgressReporter("Counting characters") as progress:
        df_count = df_input.select(
            pl.col("message_id"),
            pl.col("message_text")
            .str.len_chars()
            .add(fudge_factor)
            .alias("character_count")
        )
        progress.update(1.0)
    
    # Write output to specified path
    df_count.write_parquet(context.output("character_count").parquet_path)
```

### Declaration

Finally, create the analyzer declaration:

```python
from analyzer_interface import AnalyzerDeclaration
from .interface import interface
from .main import main

example_analyzer = AnalyzerDeclaration(
    interface=interface,
    main=main,
    is_distributed=False  # Set to True for production analyzers
)
```

## Secondary Analyzers

Secondary analyzers process the output of primary analyzers to create user-friendly exports or perform additional analysis.

### Interface Definition

Secondary analyzers specify their base primary analyzer and their own outputs:

```python
from analyzer_interface import AnalyzerOutput, OutputColumn, SecondaryAnalyzerInterface
from ..example_base.interface import interface as example_base

interface = SecondaryAnalyzerInterface(
    id="example_report",
    version="0.1.0", 
    name="Example Report",
    short_description="Adds 'is_long' flag to character count analysis",
    base_analyzer=example_base,  # Reference to primary analyzer
    outputs=[
        AnalyzerOutput(
            id="example_report",
            name="Example Report", 
            columns=[
                OutputColumn(name="message_id", data_type="integer"),
                OutputColumn(name="character_count", data_type="integer"),
                OutputColumn(name="is_long", data_type="boolean")  # New column
            ]
        )
    ]
)
```

### Implementation

Secondary analyzers read primary outputs and create enhanced results:

```python
import polars as pl
from analyzer_interface.context import SecondaryAnalyzerContext

def main(context: SecondaryAnalyzerContext):
    # Read primary analyzer output
    df_character_count = pl.read_parquet(
        context.base.table("character_count").parquet_path
    )
    
    # Add derived columns
    df_export = df_character_count.with_columns(
        pl.col("character_count").gt(100).alias("is_long")
    )
    
    # Access primary analyzer parameters if needed
    fudge_factor = context.base_params.get("fudge_factor")
    
    # Write enhanced output
    df_export.write_parquet(context.output("example_report").parquet_path)
```

## Web Presenters

Web presenters create interactive dashboards using either Dash or Shiny frameworks.

### Interface Definition

```python
from analyzer_interface import WebPresenterInterface
from ..example_base import interface as example_base
from ..example_report import interface as example_report

interface = WebPresenterInterface(
    id="example_web", 
    version="0.1.0",
    name="Message Length Histogram",
    short_description="Shows distribution of message lengths",
    base_analyzer=example_base,
    depends_on=[example_report]  # Secondary analyzers used
)
```

### Shiny Implementation

For more interactive dashboards:

```python
from shiny import reactive, render, ui
from shinywidgets import output_widget, render_widget
from analyzer_interface.context import WebPresenterContext, FactoryOutputContext, ShinyContext

def factory(context: WebPresenterContext) -> FactoryOutputContext:
    # Load data
    df = pl.read_parquet(context.base.table("character_count").parquet_path)
    
    # Define UI components
    analysis_panel = ui.card(
        ui.card_header("Character Count Analysis"),
        ui.input_checkbox("show_details", "Show detailed view", value=False),
        output_widget("histogram", height="400px")
    )
    
    def server(input, output, session):
        @render_widget
        def histogram():
            # Create interactive plot based on inputs
            show_details = input.show_details()
            # ... create plotly figure ...
            return fig
            
        @render.text
        def summary():
            return f"Total messages: {len(df)}"
    
    return FactoryOutputContext(
        shiny=ShinyContext(
            server_handler=server,
            panel=nav_panel("Dashboard", analysis_panel)
        )
    )
```

### API Factory for React Dashboards

Web presenters can also implement an `api_factory` function to provide structured data for React-based frontends through REST API endpoints:

```python
from ..utils.pop import pop_unnecessary_fields

def api_factory(context: WebPresenterContext, options: Optional[dict[str, Any]] = None):
    """
    Provides structured data for React dashboards via API endpoints.
    
    Args:
        context: WebPresenterContext with access to analyzer outputs
        options: Optional parameters from API requests (filters, etc.)
    
    Returns:
        Dict with presenter metadata and processed data arrays
    """
    # Extract API options/filters
    filter_value = options.get("matcher", "") if options else ""
    
    # Load data
    data_frame = pl.read_parquet(context.base.table("character_count").parquet_path)
    
    # Apply filters if provided
    if filter_value:
        # Apply filtering logic based on the filter_value
        data_frame = data_frame.filter(pl.col("message_text").str.contains(filter_value))
    
    # Build presenter model with metadata
    presenter_model = context.web_presenter.model_dump()
    
    # Add visualization configuration
    presenter_model["figure_type"] = "histogram"
    presenter_model["axis"] = {
        "x": {"label": "Message Character Count", "value": "message_character_count"},
        "y": {"label": "Number of Messages", "value": "number_of_messages"}
    }
    
    # Add data arrays for the frontend
    presenter_model["x"] = data_frame["character_count"].to_list()
    
    # Remove internal fields not needed by frontend
    return FactoryOutputContext(
	    api=pop_unnecessary_fields(presenter_model)
    )
```

#### Multi-Output API Factory

For analyzers with multiple outputs, return a dictionary with different data views:

```python
def api_factory(context: WebPresenterContext, options: Optional[dict[str, Any]] = None):
    filter_value = options.get("matcher", "") if options else ""
    
    # Load different data sources
    df_stats = pl.read_parquet(
        context.dependency(ngram_stats).table(OUTPUT_NGRAM_STATS).parquet_path
    )
    df_full = pl.read_parquet(
        context.dependency(ngram_stats).table(OUTPUT_NGRAM_FULL).parquet_path
    )
    
    # Apply filtering to both datasets
    if filter_value:
        matcher = create_word_matcher(filter_value, pl.col(COL_NGRAM_WORDS))
        if matcher is not None:
            df_stats = df_stats.filter(matcher)
            df_full = df_full.filter(matcher)
    
    # Create separate presenter models for each output
    stats_model = context.web_presenter.model_dump()
    full_model = context.web_presenter.model_dump()
    
    # Configure stats view
    stats_model.update({
        "figure_type": "scatter",
        "explanation": {
            "total_repetition": "N-grams to the right are repeated by more users...",
            "amplification_factor": "N-grams higher up are repeated more times..."
        },
        "axis": {
            "x": {"label": "User Count", "value": "user_count"},
            "y": {"label": "Total Repetition", "value": "total_repetition"}
        },
        "x": df_stats[COL_NGRAM_DISTINCT_POSTER_COUNT].to_list(),
        "y": {
            "total_repetition": df_stats[COL_NGRAM_TOTAL_REPS].to_list(),
            "amplification_factor": (
                df_stats[COL_NGRAM_TOTAL_REPS] / 
                df_stats[COL_NGRAM_DISTINCT_POSTER_COUNT]
            ).to_list()
        },
        "ngrams": df_stats[COL_NGRAM_WORDS].to_list()
    })
    
    # Configure full data view  
    full_model.update({
        "figure_type": "scatter",
        "ids": df_full[COL_NGRAM_ID].to_list(),
        "timestamps": df_full[COL_MESSAGE_TIMESTAMP].to_list(),
        "messages": df_full[COL_MESSAGE_TEXT].to_list(),
        "users": df_full[COL_AUTHOR_ID].to_list(),
        # ... additional fields for detailed view
    })
    
    return FactoryOutputContext(
	    api={
	        "default_output": OUTPUT_NGRAM_STATS,
	        OUTPUT_NGRAM_STATS: pop_unnecessary_fields(stats_model),
	        OUTPUT_NGRAM_FULL: pop_unnecessary_fields(full_model)
	    }
    )
```

#### API Endpoints

The API factory data is automatically exposed through REST endpoints:

- `GET /api/presenters` - List all presenter data
- `GET /api/presenters/{id}` - Get specific presenter data
- `GET /api/presenters/{id}/download/{format}` - Download data as CSV/JSON/Excel

Query parameters:

- `output` - Specify which output to return (for multi-output presenters)
- `filter_field` & `filter_value` - Apply filtering
- `matcher` - Text matching filter (passed to api_factory options)

Example API usage:

```bash
# Get basic presenter data
curl "/api/presenters/ngram_repetition_by_poster"

# Get filtered data
curl "/api/presenters/ngram_repetition_by_poster?filter_value=climate&matcher=climate"

# Get specific output
curl "/api/presenters/ngram_repetition_by_poster?output=ngram_full"

# Download as CSV
curl "/api/presenters/ngram_repetition_by_poster/download/csv"
```

## Testing Analyzers

### Testing Primary Analyzers

```python
from testing import CsvTestData, test_primary_analyzer
from .interface import interface
from .main import main

def test_example_analyzer():
    test_primary_analyzer(
        interface=interface,
        main=main,
        input=CsvTestData(
            "test_input.csv",
            semantics={"message_id": identifier}
        ),
        params={"fudge_factor": 10},
        outputs={
            "character_count": CsvTestData("expected_output.csv")
        }
    )
```

### Testing Secondary Analyzers

```python
from testing import test_secondary_analyzer, ParquetTestData

def test_example_report():
    test_secondary_analyzer(
        interface=interface,
        main=main,
        primary_params={"fudge_factor": 10},
        primary_outputs={
            "character_count": ParquetTestData("primary_output.parquet")
        },
        expected_outputs={
            "example_report": ParquetTestData("expected_report.parquet")
        }
    )
```

## Best Practices

### Data Processing

- Always call `input_reader.preprocess()` on input data in primary analyzers
- Use `ProgressReporter` for long-running operations
- Handle missing or null data gracefully
- Use appropriate data types (avoid defaulting to small integer types)

### Interface Design

- Choose descriptive, globally unique IDs
- Provide comprehensive `name_hints` for better column matching
- Mark internal outputs that users shouldn't see directly
- Include helpful parameter descriptions and validation

### Performance

- Use lazy evaluation with Polars when possible
- Process data in chunks for large datasets
- Consider memory usage when designing algorithms
- Use appropriate file formats (parquet for structured data)

### Error Handling

- Validate parameters and input data
- Provide meaningful error messages
- Handle edge cases (empty datasets, missing columns)
- Use assertions for internal consistency checks

## Adding to the Suite

Register all analyzers in `analyzers/__init__.py`:

```python
from analyzer_interface import AnalyzerSuite
from .example.example_base import example_base
from .example.example_report import example_report  
from .example.example_web import example_web

suite = AnalyzerSuite(
    all_analyzers=[
        example_base,
        example_report, 
        example_web,
        # ... other analyzers
    ]
)
```

This creates a complete analysis pipeline that users can run through the application interface, from data input through interactive visualization.

# Next Steps

Once you finish reading this it would be a good idea to review the sections for each domain. Might also be a good idea to review the sections that discuss implementing  [Shiny](https://shiny.posit.co/py/), and [React](https://react.dev) dashboards.

- [Core Domain](./domains/core-domain.md)
- [Edge Domain](./domains/edge-domain.md)
- [Content Domain](./domains/content-domain.md)
- [Shiny Dashboards](./dashboards/shiny.md)
- [React Dashboards](./dashboards/react.md)
