import csv
from csv import Sniffer
from typing import Callable, Optional

import polars as pl
from pydantic import BaseModel

import terminal_tools.prompts as prompts
from terminal_tools.utils import print_message, smart_print_data_frame

from .importer import Importer, ImporterSession


class CSVImporter(Importer["CsvImportSession"]):
    @property
    def name(self) -> str:
        return "CSV"

    def suggest(self, input_path: str) -> bool:
        return input_path.endswith(".csv")

    def _detect_skip_rows_and_dialect(self, input_path: str) -> tuple[int, csv.Dialect]:
        """Detect the number of rows to skip before CSV data begins and the CSV dialect."""
        skip_rows = 0

        try:
            with open(input_path, "r", encoding="utf8") as file:

                MAX_LINES = 50  # check the first 50 lines only
                lines = [line.strip() for i, line in enumerate(file) if i <= MAX_LINES]
                total_lines = len(lines)

                # Only analyze if we have enough lines
                if len(lines) >= 2:
                    # Parse each line and analyze content, keeping track of original line numbers
                    parsed_rows = []
                    line_numbers = []
                    for line_idx, line in enumerate(lines):
                        if not line:  # Skip empty lines
                            continue
                        try:
                            reader = csv.reader([line])
                            row = next(reader)
                            parsed_rows.append(row)
                            line_numbers.append(line_idx)
                        except Exception:
                            parsed_rows.append([line])  # Fallback for problematic lines
                            line_numbers.append(line_idx)

                    if len(parsed_rows) >= 2:
                        # Look for the actual CSV header (column names)
                        for i, row in enumerate(parsed_rows):
                            if self._looks_like_csv_header(row):
                                skip_rows = line_numbers[i]
                                break
                        else:
                            # Fallback: use field count analysis
                            field_counts = [len(row) for row in parsed_rows]
                            from collections import Counter

                            count_frequency = Counter(field_counts)
                            most_common_count = count_frequency.most_common(1)[0][0]

                            # Find first row that matches the most common field count
                            for i, count in enumerate(field_counts):
                                if count == most_common_count:
                                    skip_rows = line_numbers[i]
                                    break

                # Validate skip_rows doesn't exceed available lines
                if skip_rows >= total_lines:
                    skip_rows = 0  # Reset to safe default

                # Now detect dialect from the CSV content (after skip_rows)
                file.seek(0)
                for _ in range(skip_rows):
                    file.readline()

                sample = file.read(65536)
                dialect = Sniffer().sniff(sample)

        except Exception:
            # If anything fails, use defaults and try basic dialect detection
            skip_rows = 0
            try:
                with open(input_path, "r", encoding="utf8") as file:
                    sample = file.read(65536)
                    dialect = Sniffer().sniff(sample)
            except Exception:
                # Create a default dialect if everything fails
                class DefaultDialect:
                    delimiter = ","
                    quotechar = '"'

                dialect = DefaultDialect()

        return skip_rows, dialect

    def _looks_like_csv_header(self, row: list[str]) -> bool:
        """Check if a row looks like a CSV header with column names."""
        if not row or len(row) < 2:
            return False

        # Skip rows where most fields are empty (likely CSV notes with trailing commas)
        non_empty_fields = [field.strip() for field in row if field.strip()]
        if len(non_empty_fields) < len(row) // 2:
            return False

        # Look for typical CSV header characteristics
        header_indicators = 0

        for field in non_empty_fields:
            field = field.lower().strip()

            # Common column name patterns
            if any(
                word in field
                for word in [
                    "id",
                    "name",
                    "date",
                    "time",
                    "user",
                    "tweet",
                    "text",
                    "count",
                    "number",
                    "sent",
                    "screen",
                    "retweeted",
                    "favorited",
                ]
            ):
                header_indicators += 1

            # Short descriptive column names (not long sentences like CSV notes)
            if 3 <= len(field) <= 30 and not field.startswith(
                ("http", "www", "from ", "if you")
            ):
                header_indicators += 1

        # Consider it a CSV header if at least 50% of non-empty fields look like column names
        return header_indicators >= len(non_empty_fields) * 0.5

    def init_session(self, input_path: str):
        skip_rows, dialect = self._detect_skip_rows_and_dialect(input_path)

        return CsvImportSession(
            input_file=input_path,
            separator=dialect.delimiter,
            quote_char=dialect.quotechar,
            has_header=True,
            skip_rows=skip_rows,
        )

    def manual_init_session(self, input_path: str):
        separator = self._separator_option(None)
        if separator is None:
            return None

        quote_char = self._quote_char_option(None)
        if quote_char is None:
            return None

        has_header = self._header_option(None)
        if has_header is None:
            return None

        skip_rows = self._skip_rows_option(None)
        if skip_rows is None:
            return None

        return CsvImportSession(
            input_file=input_path,
            separator=separator,
            quote_char=quote_char,
            has_header=has_header,
            skip_rows=skip_rows,
        )

    def modify_session(
        self,
        input_path: str,
        import_session: "CsvImportSession",
        reset_screen: Callable[[], None],
    ):
        is_first_time = True
        while True:
            reset_screen(import_session)
            action = prompts.list_input(
                "What would you like to change?",
                choices=[
                    ("Column separator", "separator"),
                    ("Quote character", "quote_char"),
                    ("Header", "header"),
                    ("Skip rows", "skip_rows"),
                    ("Done. Use these options.", "done"),
                ],
                default=None if is_first_time else "done",
            )
            is_first_time = False
            if action is None:
                return None

            if action == "done":
                return import_session

            if action == "separator":
                separator = self._separator_option(import_session.separator)
                if separator is None:
                    continue
                import_session.separator = separator

            if action == "quote_char":
                quote_char = self._quote_char_option(import_session.quote_char)
                if quote_char is None:
                    continue
                import_session.quote_char = quote_char

            if action == "header":
                has_header = self._header_option(import_session.has_header)
                if has_header is None:
                    continue
                import_session.has_header = has_header

            if action == "skip_rows":
                skip_rows = self._skip_rows_option(import_session.skip_rows)
                if skip_rows is None:
                    continue
                import_session.skip_rows = skip_rows

    @staticmethod
    def _separator_option(previous_value: Optional[str]) -> Optional[str]:
        input: Optional[str] = prompts.list_input(
            "Select the column separator",
            choices=[
                ("comma (,)", ","),
                ("semicolon (;)", ";"),
                ("Pipe (|)", "|"),
                ("Tab", "\t"),
                ("Other", "other"),
            ],
            default=(
                previous_value
                if previous_value in [",", ";", "\t"]
                else "other" if previous_value is not None else None
            ),
        )
        if input is None:
            return None
        if input != "other":
            return input

        input = prompts.text("Enter the separator")
        if input is None:
            return None
        input = input.strip()
        if len(input) == 0:
            return None

    @staticmethod
    def _quote_char_option(previous_value: Optional[str]) -> Optional[str]:
        input: Optional[str] = prompts.list_input(
            "Select the quote character",
            choices=[
                ('Double quote (")', '"'),
                ("Single quote (')", "'"),
                ("Other", "other"),
            ],
            default=(
                previous_value
                if previous_value in ['"', "'"]
                else "other" if previous_value is not None else None
            ),
        )
        if input is None:
            return None
        if input != "other":
            return input

        input = prompts.text("Enter the quote character")
        if input is None:
            return None
        input = input.strip()
        if len(input) == 0:
            return None

    def _header_option(self, previous_value: Optional[bool]) -> Optional[bool]:
        return prompts.list_input(
            "Does the file have a header?",
            choices=[
                ("Yes", True),
                ("No", False),
            ],
            default=previous_value,
        )

    @staticmethod
    def _skip_rows_option(previous_value: Optional[int]) -> Optional[int]:
        while True:
            input_str = prompts.text(
                f"Number of rows to skip at the beginning of file (current: {previous_value or 0}).",
                default=str(previous_value) if previous_value is not None else "0",
            )
            if input_str is None:  # User cancelled
                return None

            try:
                skip_rows = int(input_str.strip())
                if skip_rows < 0:
                    print_message(
                        "Skip rows cannot be negative. Please try again.", "error"
                    )
                    continue
                if skip_rows > 10:
                    confirm = prompts.confirm(
                        f"Skip {skip_rows} rows? This seems high. Continue?",
                        default=True,
                    )
                    if not confirm:
                        continue  # Ask for input again instead of returning None
                return skip_rows
            except ValueError:
                print_message("Please enter a valid number.", "error")
                continue


class CsvImportSession(ImporterSession, BaseModel):
    input_file: str
    separator: str
    quote_char: str
    has_header: bool = True
    skip_rows: int = 0

    def print_config(self):
        def present_separator(value: str) -> str:
            if value == "\t":
                return "(Tab)"
            if value == " ":
                return "(Space)"
            if value == ",":
                return "(Comma ,)"
            if value == ";":
                return "(Semicolon ;)"
            if value == "'":
                return "(Single quote ')"
            if value == '"':
                return '(Double quote ")'
            if value == "|":
                return "(Pipe |)"
            return value

        # Create configuration DataFrame
        config_data = pl.DataFrame(
            {
                "Option": [
                    "Column separator",
                    "Quote character",
                    "Has header",
                    "Skip rows",
                ],
                "Value": [
                    present_separator(self.separator),
                    present_separator(self.quote_char),
                    "Yes" if self.has_header else "No",
                    str(self.skip_rows),
                ],
            }
        )

        smart_print_data_frame(config_data, title=None, apply_color=None)

    def load_preview(self, n_records: int) -> pl.DataFrame:
        return pl.read_csv(
            self.input_file,
            separator=self.separator,
            quote_char=self.quote_char,
            has_header=self.has_header,
            skip_rows=self.skip_rows,
            n_rows=n_records,
            truncate_ragged_lines=True,
            ignore_errors=True,
        )

    def import_as_parquet(self, output_path: str) -> None:
        lazyframe = pl.scan_csv(
            self.input_file,
            separator=self.separator,
            quote_char=self.quote_char,
            has_header=self.has_header,
            skip_rows=self.skip_rows,
            truncate_ragged_lines=True,
            ignore_errors=True,
        )
        lazyframe.sink_parquet(output_path)
