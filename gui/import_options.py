"""
Import options dialog for modifying CSV/Excel import configuration.

Allows users to adjust import settings and retry preview with updated parameters.
"""

from traceback import format_exc
from typing import Callable

from nicegui import ui

from importing.csv import CsvImportSession
from importing.excel import ExcelImportSession


def present_separator(value: str) -> str:
    """Format separator/quote character for display."""
    mapping = {
        "\t": "Tab",
        " ": "Space",
        ",": ", (Comma)",
        ";": "; (Semicolon)",
        "'": "' (Single quote)",
        '"': '" (Double quote)',
        "|": "| (Pipe)",
    }
    return mapping.get(value, value)


class ImportOptionsDialog(ui.dialog):
    """
    Dialog for configuring CSV/Excel import options.

    Displays interactive controls for modifying import parameters
    and allows retrying the import with updated settings.
    """

    def __init__(
        self,
        import_session: CsvImportSession | ExcelImportSession,
        selected_file_path: str,
        on_retry: Callable[[CsvImportSession | ExcelImportSession], None],
    ):
        """
        Initialize the import options dialog.

        Args:
            import_session: Current import session with detected settings
            selected_file_path: Path to the file being imported
            on_retry: Callback function called when user clicks "Retry Import"
                     with the updated import session as parameter
        """
        super().__init__()

        self.import_session = import_session
        self.selected_file_path = selected_file_path
        self.on_retry = on_retry

        # Build dialog UI
        with self, ui.card().classes("w-full").style(
            "min-width: 600px; max-width: 800px"
        ):
            ui.label("Import Configuration").classes("text-h5 mb-4")

            if isinstance(import_session, CsvImportSession):
                self._build_csv_controls()
            elif isinstance(import_session, ExcelImportSession):
                self._build_excel_controls()

            # Action buttons
            with ui.row().classes("w-full justify-end gap-2 mt-6"):
                ui.button("Cancel", on_click=self.close).props("outline")
                ui.button(
                    "Retry Import",
                    icon="refresh",
                    on_click=self._handle_retry,
                    color="primary",
                )

    def _build_csv_controls(self):
        """Build CSV-specific configuration controls."""
        session = self.import_session

        ROW_LAYOUT = "w-full items-center gap-4 mb-4"

        # Row 1: Column Separator
        with ui.row().classes(ROW_LAYOUT):
            ui.label("Column separator:").classes("text-base font-bold").style(
                "min-width: 160px"
            )
            self.separator_toggle = ui.toggle(
                {
                    ",": "Comma (,)",
                    ";": "Semicolon (;)",
                    "|": "Pipe (|)",
                    "\t": "Tab",
                },
                value=session.separator,
            )

        # Row 2: Quote Character
        with ui.row().classes(ROW_LAYOUT):
            ui.label("Quote character:").classes("text-base font-bold").style(
                "min-width: 160px"
            )
            self.quote_toggle = ui.toggle(
                {
                    '"': 'Double quote (")',
                    "'": "Single quote (')",
                },
                value=session.quote_char,
            )

        # Row 3: Has Header
        with ui.row().classes(ROW_LAYOUT):
            with ui.label("Has header:").classes("text-base font-bold").style(
                "min-width: 160px"
            ):
                ui.tooltip("Whether the file has a header row with column names")
            self.header_toggle = ui.toggle(
                {True: "Yes", False: "No"},
                value=session.has_header,
            )

        # Row 4: Skip Rows
        with ui.row().classes(ROW_LAYOUT):
            ui.label("Skip rows:").classes("text-base font-bold").style(
                "min-width: 160px"
            )
            self.skip_rows_input = ui.number(
                label="Number of rows to skip at start",
                value=session.skip_rows,
                min=0,
                max=100,
                step=1,
                precision=0,
                validation={
                    "Must be non-negative": lambda v: v >= 0,
                    "Cannot exceed 100": lambda v: v <= 100,
                },
            ).classes("w-48")

    def _build_excel_controls(self):
        """Build Excel-specific configuration controls."""
        session = self.import_session

        ui.label("Excel Import Options").classes("text-sm text-gray-600 mb-2")
        ui.label(f"Sheet: {session.selected_sheet}").classes("text-base")

        # Future enhancement: Add sheet selector dropdown
        ui.label("(Sheet selection coming soon)").classes("text-sm text-gray-500 mt-2")

    async def _handle_retry(self):
        """Handle retry import button click."""
        try:
            if isinstance(self.import_session, CsvImportSession):
                # Get updated values from controls
                new_separator = self.separator_toggle.value
                new_quote_char = self.quote_toggle.value
                new_has_header = self.header_toggle.value
                new_skip_rows = int(self.skip_rows_input.value)

                # Validate
                if new_skip_rows < 0 or new_skip_rows > 100:
                    ui.notify("Invalid skip rows value", type="negative")
                    return

                # Create new session with updated config
                updated_session = CsvImportSession(
                    input_file=self.selected_file_path,
                    separator=new_separator,
                    quote_char=new_quote_char,
                    has_header=new_has_header,
                    skip_rows=new_skip_rows,
                )

                # Call retry callback with updated session
                await self.on_retry(updated_session)

                # Close dialog
                self.close()

            elif isinstance(self.import_session, ExcelImportSession):
                # For Excel, just use existing session (no changes yet)
                await self.on_retry(self.import_session)
                self.close()

        except Exception as e:
            ui.notify(f"Error updating configuration: {str(e)}", type="negative")
            print(f"Config update error:\n{format_exc()}")
