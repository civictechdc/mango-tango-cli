# Shiny Dashboards Guide

Web presenters can create interactive dashboards using Python Shiny for rich server-side interactivity. Shiny dashboards provide immediate reactivity, complex data processing capabilities, and seamless integration with the analyzer pipeline. Which in turn allows developers and data scientists the ability to quickly prototype new analyses.

## Overview

Shiny dashboards are server-rendered applications that provide:

- **Real-time interactivity**: Components update automatically when inputs change
- **Server-side processing**: Complex calculations run on the server with full Python ecosystem access
- **Widgets**: Built-in components for inputs, outputs, and visualizations
- **Session management**: Automatic handling of user sessions and state

## Basic Structure

Every Shiny web presenter follows this pattern:

```python
from shiny import reactive, render, ui
from shinywidgets import output_widget, render_widget
from analyzer_interface.context import WebPresenterContext, FactoryOutputContext, ShinyContext
import polars as pl
import plotly.express as px

def factory(context: WebPresenterContext) -> FactoryOutputContext:
    # Load analyzer data
    df = pl.read_parquet(context.base.table("your_output").parquet_path)
    
    # Define UI layout
    dashboard_ui = ui.card(
        ui.card_header("Your Dashboard Title"),
        ui.row(
            ui.column(4, 
                # Input controls
                ui.input_selectize("category", "Select Category", 
                                 choices=df["category"].unique().to_list()),
                ui.input_slider("threshold", "Threshold", 0, 100, 50)
            ),
            ui.column(8,
                # Output displays
                output_widget("main_plot", height="400px"),
                ui.output_text("summary_stats")
            )
        )
    )
    
    def server(input, output, session):
        @reactive.Calc
        def filtered_data():
            # Reactive data filtering
            return df.filter(
                (pl.col("category") == input.category()) &
                (pl.col("value") >= input.threshold())
            )
        
        @render_widget
        def main_plot():
            # Create interactive plot
            plot_df = filtered_data().to_pandas()
            fig = px.scatter(plot_df, x="x", y="y", color="category")
            return fig
        
        @render.text
        def summary_stats():
            data = filtered_data()
            return f"Showing {len(data)} items, avg value: {data['value'].mean():.2f}"
    
    return FactoryOutputContext(
        shiny=ShinyContext(
            server_handler=server,
            panel=nav_panel("Dashboard", dashboard_ui)
        )
    )
```

## User Interface Components

### Layout Components

Organize your dashboard with these layout elements:

```python
# Cards for grouped content
ui.card(
    ui.card_header("Section Title"),
    ui.card_body("Content goes here")
)

# Grid layouts
ui.row(
    ui.column(6, "Left column"),
    ui.column(6, "Right column")
)

# Navigation
ui.navset_tab(
    ui.nav_panel("Tab 1", "Content 1"),
    ui.nav_panel("Tab 2", "Content 2")
)

# Sidebars
ui.sidebar(
    "Sidebar content",
    open="open"  # or "closed"
)
```

### Input Controls

Collect user input with various widgets:

```python
# Text inputs
ui.input_text("text_id", "Label", value="default")
ui.input_text_area("textarea_id", "Description", rows=3)

# Numeric inputs
ui.input_numeric("number_id", "Number", value=10, min=0, max=100)
ui.input_slider("slider_id", "Range", 0, 100, value=[20, 80])

# Selection inputs
ui.input_select("select_id", "Choose one", choices=["A", "B", "C"])
ui.input_selectize("selectize_id", "Type to search", 
                   choices=data["column"].unique().to_list(),
                   multiple=True)

# Boolean inputs
ui.input_checkbox("check_id", "Enable feature", value=True)
ui.input_switch("switch_id", "Toggle mode")

# File uploads
ui.input_file("file_id", "Upload CSV", accept=".csv")

# Date/time inputs
ui.input_date("date_id", "Select date")
ui.input_date_range("daterange_id", "Date range")
```

### Output Components

Display results with these output components:

```python
# Text outputs
ui.output_text("text_id")        # Plain text
ui.output_text_verbatim("code_id")  # Monospace text
ui.output_ui("dynamic_ui")       # Dynamic UI elements

# Tables
ui.output_table("table_id")      # Basic table
ui.output_data_frame("df_id")    # Interactive data frame

# Plots
output_widget("plot_id")         # For plotly/bokeh widgets
ui.output_plot("matplotlib_id")  # For matplotlib plots

# Downloads
ui.download_button("download_id", "Download Data")
```

## Reactive Programming

Shiny's reactive system automatically updates outputs when inputs change:

### Reactive Calculations

Use `@reactive.Calc` for expensive computations that multiple outputs depend on:

```python
@reactive.Calc
def processed_data():
    # This only runs when dependencies change
    raw_data = load_data()
    return raw_data.filter(pl.col("active") == input.show_active())

@render_widget
def plot1():
    data = processed_data()  # Uses cached result
    return create_plot(data)

@render.text  
def summary():
    data = processed_data()  # Uses same cached result
    return f"Records: {len(data)}"
```

### Reactive Effects

Use `@reactive.Effect` for side effects like updating other inputs:

```python
@reactive.Effect
def update_choices():
    # Update selectize choices when category changes
    category = input.category()
    new_choices = df.filter(pl.col("category") == category)["subcategory"].unique()
    ui.update_selectize("subcategory", choices=new_choices.to_list())
```

### Event Handling

Respond to button clicks and other events:

```python
@reactive.Effect
@reactive.event(input.reset_button)
def reset_filters():
    ui.update_slider("threshold", value=50)
    ui.update_select("category", selected="All")
```

## Data Visualization

### Plotly Integration

Create interactive plots with plotly:

```python
from shinywidgets import output_widget, render_widget
import plotly.express as px
import plotly.graph_objects as go

@render_widget
def scatter_plot():
    df_plot = filtered_data().to_pandas()
    
    fig = px.scatter(
        df_plot, 
        x="x_value", 
        y="y_value",
        color="category",
        size="size_value",
        hover_data=["additional_info"],
        title="Interactive Scatter Plot"
    )
    
    # Customize layout
    fig.update_layout(
        height=500,
        showlegend=True,
        hovermode="closest"
    )
    
    return fig

@render_widget  
def time_series():
    df_ts = time_series_data().to_pandas()
    
    fig = go.Figure()
    
    for category in df_ts["category"].unique():
        category_data = df_ts[df_ts["category"] == category]
        fig.add_trace(go.Scatter(
            x=category_data["date"],
            y=category_data["value"],
            name=category,
            mode="lines+markers"
        ))
    
    fig.update_layout(
        title="Time Series Analysis",
        xaxis_title="Date",
        yaxis_title="Value"
    )
    
    return fig
```

### Custom Plots

Create custom visualizations with matplotlib or other libraries:

```python
from shiny import render
import matplotlib.pyplot as plt
import seaborn as sns

@render.plot
def correlation_heatmap():
    df_corr = correlation_data().to_pandas()
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        df_corr.corr(),
        annot=True,
        cmap="coolwarm",
        center=0,
        square=True
    )
    plt.title("Correlation Matrix")
    plt.tight_layout()
    return plt.gcf()
```

## Data Tables

Display and interact with tabular data:

### Basic Tables

```python
@render.table
def simple_table():
    return filtered_data().to_pandas()
```

### Interactive Data Frames

```python
from shiny.render import DataGrid, DataTable

@render.data_frame
def interactive_grid():
    df_display = filtered_data().to_pandas()
    
    return DataGrid(
        df_display,
        selection_mode="rows",  # or "none", "row", "rows", "col", "cols"
        filters=True,
        width="100%",
        height="400px"
    )

# Access selected rows
@reactive.Effect
def handle_selection():
    selected = interactive_grid.data_view(selected=True)
    if len(selected) > 0:
        # Process selected data
        pass
```

### Custom Table Styling

```python
@render.table
def styled_table():
    df = summary_stats().to_pandas()
    
    # Format numeric columns
    df["percentage"] = df["percentage"].map("{:.1%}".format)
    df["amount"] = df["amount"].map("${:,.0f}".format)
    
    return df
```

## Advanced Features

### Dynamic UI

Create UI elements that change based on user input:

```python
@render.ui
def dynamic_controls():
    analysis_type = input.analysis_type()
    
    if analysis_type == "correlation":
        return ui.div(
            ui.input_selectize("x_var", "X Variable", choices=numeric_columns),
            ui.input_selectize("y_var", "Y Variable", choices=numeric_columns)
        )
    
    if analysis_type == "distribution":
        return ui.div(
            ui.input_select("dist_var", "Variable", choices=all_columns),
            ui.input_numeric("bins", "Number of bins", value=30)
        )
    
    eturn ui.div("Select an analysis type")
```

### Progress Indicators

Show progress for long-running operations:

```python
from shiny import ui

@reactive.Effect
@reactive.event(input.run_analysis)
def run_long_analysis():
    with ui.Progress(min=0, max=100) as progress:
        progress.set(message="Loading data", value=0)
        data = load_large_dataset()
        
        progress.set(message="Processing", value=50)
        results = process_data(data)
        
        progress.set(message="Finalizing", value=90)
        save_results(results)
        
        progress.set(value=100)
    
    ui.notification_show("Analysis complete!", type="success")
```

## Integration with Analyzers

### Accessing Analyzer Data

```python
def factory(context: WebPresenterContext) -> FactoryOutputContext:
    # Access primary analyzer outputs
    main_data = pl.read_parquet(
        context.base.table("main_analysis").parquet_path
    )
    
    # Access secondary analyzer outputs
    summary_data = pl.read_parquet(
        context.dependency(summary_analyzer).table("summary").parquet_path
    )
    
    # Access parameters used in analysis
    threshold = context.base_params.get("threshold", 0.5)
    
    # Build dashboard with this data
    # ...
```

### Parameter Integration

Use analyzer parameters in your dashboard:

```python
def server(input, output, session):
    # Get analyzer parameters
    analyzer_threshold = context.base_params.get("threshold", 0.5)
    
    @render.text
    def analysis_info():
        return f"Analysis run with threshold: {analyzer_threshold}"
    
    @render_widget
    def threshold_comparison():
        # Compare user input with analyzer parameter
        user_threshold = input.user_threshold()
        df_comparison = main_data.with_columns([
            (pl.col("value") > analyzer_threshold).alias("analyzer_flag"),
            (pl.col("value") > user_threshold).alias("user_flag")
        ])
        
        return create_comparison_plot(df_comparison)
```

## Performance Optimization

### Efficient Data Processing

```python
@reactive.Calc
def base_data():
    # Load once and cache
    return pl.read_parquet(data_path)

@reactive.Calc  
def filtered_data():
    # Efficient filtering with Polars
    filters = []
    
    if input.category() != "All":
        filters.append(pl.col("category") == input.category())
    
    if input.date_range() is not None:
        start, end = input.date_range()
        filters.append(pl.col("date").is_between(start, end))
    
    if filters:
        return base_data().filter(pl.all_horizontal(filters))
        
    else:
        return base_data()
```

### Lazy Evaluation

```python
@reactive.Calc
def expensive_calculation():
    # Only runs when dependencies change
    data = filtered_data()
    
    # Use lazy evaluation
    result = (
        data
        .group_by("category")
        .agg([
            pl.col("value").mean().alias("avg_value"),
            pl.col("value").std().alias("std_value"),
            pl.col("value").count().alias("count")
        ])
        .sort("avg_value", descending=True)
    )
    
    return result
```

## Testing Shiny Dashboards

### Unit Testing Components

```python
import pytest
from shiny.testing import ShinyAppProc
from your_presenter import factory

def test_dashboard_loads():
    """Test that dashboard loads without errors"""
    app = factory(mock_context)
    
    # Test UI renders
    assert app.shiny.panel is not None
    
    # Test server function exists
    assert callable(app.shiny.server_handler)

def test_data_filtering():
    """Test reactive data filtering"""
    with ShinyAppProc(factory(mock_context)) as proc:
        # Set input values
        proc.set_inputs(category="TypeA", threshold=50)
        
        # Check outputs update correctly
        output = proc.get_output("summary_stats")
        assert "TypeA" in output
```

### Integration Testing

```python
def test_with_real_data():
    """Test dashboard with actual analyzer output"""
    # Run analyzer to generate test data
    context = create_test_context(test_data_path)
    
    # Test dashboard with real data
    app = factory(context)
    
    # Verify data loads correctly
    assert app.shiny.panel is not None
```

## Deployment Considerations

### Resource Management

- Use `@reactive.Calc` for expensive operations to enable caching
- Implement pagination for large datasets
- Consider data sampling for very large visualizations
- Use lazy loading for secondary data

### Error Handling

```python
@render_widget
def safe_plot():
    try:
        data = filtered_data()
        if len(data) == 0:
            return empty_plot_message()
        
        return create_plot(data)
    
    except Exception as e:
        ui.notification_show(f"Plot error: {str(e)}", type="error")
        return error_plot()
```

### Session Management

```python
def server(input, output, session):
    # Clean up resources when session ends
    @reactive.Effect
    def cleanup():
        session.on_ended(lambda: cleanup_user_data())
```

## Example: Complete Dashboard

Here's a complete example of a Shiny dashboard for analyzing message sentiment:

```python
from shiny import reactive, render, ui
from shinywidgets import output_widget, render_widget
import plotly.express as px
import polars as pl

def factory(context: WebPresenterContext) -> FactoryOutputContext:
    # Load data
    df_sentiment = pl.read_parquet(
        context.base.table("sentiment_analysis").parquet_path
    )
    
    # Get unique values for inputs
    date_range = (df_sentiment["date"].min(), df_sentiment["date"].max())
    categories = ["All"] + df_sentiment["category"].unique().to_list()
    
    # UI Layout
    dashboard = ui.page_sidebar(
        ui.sidebar(
            ui.h3("Analysis Controls"),
            ui.input_date_range(
                "date_filter", 
                "Date Range",
                start=date_range[0],
                end=date_range[1]
            ),
            ui.input_selectize(
                "category_filter",
                "Categories", 
                choices=categories,
                selected="All",
                multiple=True
            ),
            ui.input_slider(
                "sentiment_threshold",
                "Sentiment Threshold",
                -1, 1, 0, step=0.1
            ),
            ui.hr(),
            ui.input_action_button("reset", "Reset Filters"),
            ui.download_button("download", "Download Data")
        ),
        
        ui.div(
            ui.h2("Sentiment Analysis Dashboard"),
            
            ui.row(
                ui.column(6, ui.value_box(
                    title="Total Messages",
                    value=ui.output_text("total_count"),
                    theme="primary"
                )),
                ui.column(6, ui.value_box(
                    title="Avg Sentiment", 
                    value=ui.output_text("avg_sentiment"),
                    theme="success"
                ))
            ),
            
            ui.navset_tab(
                ui.nav_panel(
                    "Time Series",
                    output_widget("timeseries_plot", height="500px")
                ),
                ui.nav_panel(
                    "Distribution", 
                    output_widget("distribution_plot", height="500px")
                ),
                ui.nav_panel(
                    "Data Table",
                    ui.output_data_frame("data_table")
                )
            )
        )
    )
    
    def server(input, output, session):
        @reactive.Calc
        def filtered_data():
            data = df_sentiment
            
            # Date filtering
            if input.date_filter() is not None:
                start, end = input.date_filter()
                data = data.filter(pl.col("date").is_between(start, end))
            
            # Category filtering
            if "All" not in input.category_filter():
                data = data.filter(pl.col("category").is_in(input.category_filter()))
            
            # Sentiment filtering
            data = data.filter(pl.col("sentiment") >= input.sentiment_threshold())
            
            return data
        
        @render.text
        def total_count():
            return f"{len(filtered_data()):,}"
        
        @render.text
        def avg_sentiment():
            avg = filtered_data()["sentiment"].mean()
            return f"{avg:.3f}"
        
        @render_widget
        def timeseries_plot():
            df_plot = (
                filtered_data()
                .group_by("date")
                .agg(pl.col("sentiment").mean().alias("avg_sentiment"))
                .sort("date")
                .to_pandas()
            )
            
            fig = px.line(
                df_plot, 
                x="date", 
                y="avg_sentiment",
                title="Sentiment Over Time"
            )
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            return fig
        
        @render_widget
        def distribution_plot():
            df_plot = filtered_data().to_pandas()
            
            fig = px.histogram(
                df_plot,
                x="sentiment", 
                color="category",
                title="Sentiment Distribution",
                nbins=50
            )
            return fig
        
        @render.data_frame
        def data_table():
            return filtered_data().to_pandas()
        
        @reactive.Effect
        @reactive.event(input.reset)
        def reset_filters():
            ui.update_date_range("date_filter", start=date_range[0], end=date_range[1])
            ui.update_selectize("category_filter", selected="All")
            ui.update_slider("sentiment_threshold", value=0)
        
        @render.download(filename="sentiment_data.csv")
        def download():
            return filtered_data().write_csv()
    
    return FactoryOutputContext(
        shiny=ShinyContext(
            server_handler=server,
            panel=nav_panel("Sentiment Analysis", dashboard)
        )
    )
```

This comprehensive guide covers all aspects of building Shiny dashboards for your analyzer platform. The reactive programming model, rich widget ecosystem, and seamless Python integration make Shiny an excellent choice for creating sophisticated data analysis interfaces.

# Next Steps

Once you finish reading section be a good idea to review the section that discuss implementing [React](https://react.dev) dashboards. Might also be a good idea to review the sections for each domain. 

- [Core Domain](../domains/core-domain.md)
- [Edge Domain](../domains/edge-domain.md)
- [Content Domain](../domains/content-domain.md)
- [React Dashboards](./react.md)


