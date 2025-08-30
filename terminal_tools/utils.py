import os
import subprocess
import sys

import polars as pl
from rich.console import Console
from rich.style import Style
from rich.table import Table


def clear_terminal():
    """Clears the terminal"""
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def wait_for_key(prompt: bool = False):
    """Waits for the user to press any key

    Args:
        prompt (bool, optional): If true, a default text
        `Press any key to continue` will be shown. Defaults to False.
    """
    if prompt:
        print("Press any key to continue...", end="", flush=True)
    _wait_for_key()


if os.name == "nt":
    import msvcrt

    def _wait_for_key():
        return msvcrt.getch()

else:
    import termios
    import tty

    def _wait_for_key():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


def enable_windows_ansi_support():
    """
    Set up the Windows terminal to support ANSI escape codes, which will be needed
    for colored text, line clearing, and other terminal features.
    """
    if os.name == "nt":
        # Enable ANSI escape code support for Windows
        # On Windows, calling os.system('') with an empty string doesn't
        # run any actual command. However, there's an undocumented side
        # effect: it forces the Windows terminal to initialize or refresh
        # its state, enabling certain features like the processing of ANSI
        # escape codes, which might not otherwise be active.
        os.system("")


def clear_printed_lines(count: int):
    """
    Clear the last `count` lines of the terminal. Useful for repainting
    terminal output.

    Args:
        count (int): The number of lines to clear
    """
    for _ in range(count + 1):
        sys.stdout.write("\033[2K")  # Clear the current line
        sys.stdout.write("\033[F")  # Move cursor up one line
    sys.stdout.write("\033[2K\r")  # Clear the last line and move to start
    sys.stdout.flush()


def draw_box(text: str, *, padding_spaces: int = 5, padding_lines: int = 1) -> str:
    """
    Draw a box around the given text, which will be centered in the box.

    Args:
        text (str): The text to be drawn, may be multiline.
          ANSI formatting and emojis are not supported, as they mess with
          both the character count calculation and the monospace font.

        padding_spaces (int, optional): Extra spaces on either side of the longest line. Defaults to 5.
        padding_lines (int, optional): Extra lines above and below the text. Defaults to 1.

    Returns:
        str: The text surrounded by a box.
    """
    lines = text.split("\n")
    width = max(len(line) for line in lines) + padding_spaces * 2

    box = ""
    box += "┌" + "─" * width + "┐\n"
    for _ in range(padding_lines):
        box += "│" + " " * width + "│\n"
    for line in lines:
        padding = " " * padding_spaces
        box += "│" + padding + line.center(width - 2 * padding_spaces) + padding + "│\n"
    for _ in range(padding_lines):
        box += "│" + " " * width + "│\n"
    box += "└" + "─" * width + "┘\n"
    return box


def open_directory_explorer(path: str):
    if os.name == "nt":
        # Windows platform
        subprocess.run(["explorer", os.path.normpath(path)])
    elif os.name == "posix":
        if sys.platform == "darwin":
            # macOS
            subprocess.run(["open", path])
        elif sys.platform == "linux":
            if is_wsl():
                # WSL2 environment
                windows_path = subprocess.run(
                    ["wslpath", "-w", path], capture_output=True, text=True
                ).stdout.strip()
                subprocess.run(["explorer.exe", windows_path])
            else:
                # Native Linux
                subprocess.run(["xdg-open", path])
        else:
            raise OSError(f"Unsupported POSIX platform: {sys.platform}")
    else:
        raise OSError(f"Unsupported operating system: {os.name}")


def is_wsl() -> bool:
    """Check if the environment is WSL2."""
    try:
        with open("/proc/version", "r") as f:
            return "microsoft" in f.read().lower()
    except FileNotFoundError:
        return False


def print_ascii_table(
    rows: list[list[str]], *, header: list[str], min_widths: list[int] = []
):
    # Determine the max number of columns
    max_columns = max([len(header), *(len(row) for row in rows)])

    # Make the data/header/min widths all the same column count
    def fill_row(row: list[str]):
        return [*row, *([""] * (max_columns - len(row)))]

    rows = list(fill_row(row) for row in rows)
    header = fill_row(header)
    min_widths = [*min_widths, *([0] * (max_columns - len(min_widths)))]

    # Determine the width of each column by finding the longest item in each column
    col_widths = [
        max([*(len(str(item)) for item in col), min_widths[i]])
        for i, col in enumerate(zip(*[header, *rows]))
    ]

    # Print the header
    header_row = (
        "│ "
        + " ┆ ".join(f"{header[i]:<{col_widths[i]}}" for i, _ in enumerate(header))
        + " │"
    )

    def border_row(left: str, middle: str, right: str, char: str = "─"):
        return left + middle.join(char * w for w in col_widths) + right

    # top border
    print(border_row("┌─", "─┬─", "─┐"))

    print(header_row)

    # separator
    print(border_row("╞═", "═╪═", "═╡", "═"))

    # Print each row of data
    for row in rows:
        print(
            "│ "
            + " ┆ ".join(
                f"{str(row[i]):<{col_widths[i]}}" for i, _ in enumerate(header)
            )
            + " │"
        )

    # bottom border
    print(border_row("└─", "─┴─", "─┘"))


console = Console()


def print_data_frame(data_frame, title: str, apply_color: str, caption: str = None):
    # Mapping Polars data types to Rich colors (medium brightness)
    # see: https://rich.readthedocs.io/en/stable/appendix/colors.html
    POLARS_TYPE_COLORS = {
        # String types
        pl.String: "dodger_blue2",
        pl.Categorical: "light_blue3",
        # Numeric types
        pl.Int8: "green3",
        pl.Int16: "green3",
        pl.Int32: "green3",
        pl.Int64: "green3",
        pl.UInt8: "dark_green",
        pl.UInt16: "dark_green",
        pl.UInt32: "dark_green",
        pl.UInt64: "dark_green",
        pl.Float32: "orange3",
        pl.Float64: "orange3",
        # Temporal types
        pl.Date: "medium_purple2",
        pl.Datetime: "medium_purple3",
        pl.Time: "purple3",
        pl.Duration: "orchid3",
        # Boolean
        pl.Boolean: "gold3",
        # Complex types
        pl.List: "dark_cyan",
        pl.Struct: "cyan3",
        pl.Array: "steel_blue3",
        # Binary/Other
        pl.Binary: "grey62",
        pl.Null: "grey50",
        pl.Object: "deep_pink3",
        pl.Unknown: "indian_red3",
    }

    # Color cycle for column/row-wise coloring
    CYCLE_COLORS = [
        "orange3",
        "dodger_blue1",
        "dark_cyan",
        "medium_purple1",
        "deep_pink4",
        "gold1",
        "grey66",
        "steel_blue1",
    ]

    # Get colors based on column data types
    def get_column_color(dtype):
        # Handle parameterized types like Datetime(time_unit, time_zone)
        if hasattr(dtype, "base_type"):
            base_type = dtype.base_type()
            if base_type in POLARS_TYPE_COLORS:
                return POLARS_TYPE_COLORS[base_type]

        # Direct type mapping
        dtype_class = type(dtype)
        if dtype_class in POLARS_TYPE_COLORS:
            return POLARS_TYPE_COLORS[dtype_class]

        # Check if it's a subclass of known types
        for polars_type, color in POLARS_TYPE_COLORS.items():
            if isinstance(dtype, polars_type):
                return color

        # Fallback to index-based coloring
        return CYCLE_COLORS[hash(str(dtype)) % len(CYCLE_COLORS)]

    # Capture original data types BEFORE string conversion
    original_dtypes = {
        col: data_frame.select(col).dtypes[0] for col in data_frame.columns
    }

    # Convert non-string columns to strings for display
    data_frame = data_frame.with_columns(pl.exclude(pl.String).cast(str))

    def get_column_display_width(col, original_dtype):
        """Calculate appropriate display width for a column based on content"""

        if original_dtype in [pl.String, pl.Categorical]:
            # Sample first few values to estimate content length
            sample_values = data_frame.select(col).head(10).to_series()
            max_sample_length = max(
                (len(str(val)) for val in sample_values if val is not None), default=0
            )

            if max_sample_length > 30:  # Long text content
                return 50
            elif max_sample_length > 15:  # Medium text content
                return 30

        return 25  # Standard width for non-text or short text

    table = Table(title=title, caption=caption)

    # Add columns with appropriate coloring and width limits
    for i, col in enumerate(data_frame.columns):
        original_dtype = original_dtypes[col]
        col_width = get_column_display_width(col, original_dtype)

        if apply_color == "column-wise":
            # Cycle through colors for each column
            col_color = CYCLE_COLORS[i % len(CYCLE_COLORS)]
            table.add_column(
                col,
                style=col_color,
                max_width=col_width,
                overflow="ellipsis",
                no_wrap=True,
            )
        elif apply_color == "column_data_type":
            # Color based on ORIGINAL data type (before string conversion)
            col_color = get_column_color(original_dtype)
            table.add_column(
                col,
                style=col_color,
                max_width=col_width,
                overflow="ellipsis",
                no_wrap=True,
            )
        elif apply_color is None:
            # No coloring at all - omit style parameter entirely
            table.add_column(
                col,
                max_width=col_width,
                overflow="ellipsis",
                no_wrap=True,
            )
        else:
            # No column coloring - omit style parameter entirely
            table.add_column(
                col,
                max_width=col_width,
                overflow="ellipsis",
                no_wrap=True,
            )

    # Add rows with appropriate coloring based on mode
    if apply_color == "row-wise":
        # Cycle through colors for each row
        for i, row in enumerate(data_frame.iter_rows()):
            row_color = CYCLE_COLORS[i % len(CYCLE_COLORS)]
            table.add_row(*row, style=row_color)
    elif apply_color is None:
        # No row coloring at all
        for row in data_frame.iter_rows():
            table.add_row(*row)
    else:
        # No row coloring (column coloring only)
        for row in data_frame.iter_rows():
            table.add_row(*row)

    console.print(table)


def print_data_frame_summary(
    data_frame, title: str, apply_color: str = "column_data_type", caption: str = None
):
    """Print a summary table for dataframes with many columns"""
    from preprocessing.series_semantic import infer_series_semantic

    MAX_ROW_CHAR = 25

    # Create summary data
    summary_data = []
    for col in data_frame.columns:
        dtype = data_frame.select(col).dtypes[0]

        # Get example value (first non-null if possible)
        example_series = data_frame.select(col).to_series()
        example_val = None
        for val in example_series:
            if val is not None:
                example_val = str(val)
                break
        if example_val is None:
            example_val = "null"

        # Truncate long examples
        if len(example_val) > MAX_ROW_CHAR:
            example_val = example_val[:MAX_ROW_CHAR] + "..."

        # Get semantic analysis type
        try:
            semantic = infer_series_semantic(data_frame.select(col).to_series())
            analysis_type = semantic.data_type if semantic else "unknown"
        except Exception:
            analysis_type = "unknown"

        summary_data.append([col, str(dtype), example_val, analysis_type])

    # Create summary dataframe
    summary_df = pl.DataFrame(
        {
            "Column Name": [row[0] for row in summary_data],
            "Data Type": [row[1] for row in summary_data],
            "Example Value": [row[2] for row in summary_data],
            "Inferred Analyzer Input Type": [row[3] for row in summary_data],
        }
    )

    # Print with specified coloring mode
    print_data_frame(summary_df, title, apply_color, caption)


def smart_print_data_frame(
    data_frame: pl.DataFrame,
    title: str,
    apply_color: str | None = "column_data_type",
    smart_print: bool = True,
    caption: str | None = None,
) -> None:
    """Smart dataframe printing with adaptive display based on terminal width.

    Automatically chooses between full table display and summary view based on terminal
    width and number of columns. Provides Rich-styled tables with configurable coloring.

    Args:
        data_frame: Polars DataFrame to display
        title: Title text to display above the table
        apply_color: Color mode for the table display:
            - "column_data_type": Colors columns based on their Polars data types
            - "column-wise": Cycles through colors for each column
            - "row-wise": Cycles through colors for each row
            - None: No coloring (plain black and white display)
        smart_print: Controls adaptive display behavior:
            - True: Uses summary view for wide tables (>8 cols or narrow terminal)
            - False: Always uses full table display regardless of width
        caption: Optional caption text displayed below the table

    Display Logic:
        - If smart_print=False: Always shows full table
        - If smart_print=True and (>8 columns OR estimated column width <12):
          Shows summary with column info, data types, and examples
        - Otherwise: Shows full table with all data

    Examples:
        >>> smart_print_data_frame(df, "My Data", apply_color=None)
        >>> smart_print_data_frame(df, "Analysis Results", caption="Processing complete")
        >>> smart_print_data_frame(df, "Wide Dataset", smart_print=False)
    """
    if not smart_print:
        # Always use full dataframe display when smart_print is disabled
        print_data_frame(data_frame, title, apply_color, caption)
        return

    # Smart adaptive logic
    terminal_width = console.size.width
    n_cols = len(data_frame.columns)

    # Calculate if columns will be too narrow for readability
    estimated_col_width = max(60, terminal_width - 4) // max(n_cols, 1)
    min_readable_width = 12  # Minimum width for readable columns

    # Use summary if too many columns or columns would be too narrow
    if n_cols > 8 or estimated_col_width < min_readable_width:
        print_data_frame_summary(
            data_frame,
            title + " (Dataset has a large nr. of columns, showing summary instead)",
            apply_color,
            caption,
        )
    else:
        print_data_frame(data_frame, title, apply_color, caption)


def print_dialog_section_title(print_str):
    mango_style = Style(color="#F3921E", bold=True)

    console.print(print_str, style=mango_style)
