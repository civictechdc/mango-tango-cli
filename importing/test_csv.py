from pathlib import Path

from .csv import CSVImporter


class TestCSVImporter:
    def setup_method(self):
        """Set up test fixtures."""
        self.importer = CSVImporter()
        self.test_data_dir = Path(__file__).parent / "test_data"

    def test_detect_skip_rows_and_dialect_simple_header(self):
        """Test detection with simple CSV (no notes to skip)."""
        csv_path = str(self.test_data_dir / "simple_header.csv")
        skip_rows, dialect = self.importer._detect_skip_rows_and_dialect(csv_path)
        assert skip_rows == 0
        assert dialect.delimiter == ","

    def test_detect_skip_rows_and_dialect_notes_with_commas(self):
        """Test detection with notes containing commas."""
        csv_path = str(self.test_data_dir / "notes_with_commas.csv")
        skip_rows, dialect = self.importer._detect_skip_rows_and_dialect(csv_path)
        assert skip_rows == 2
        assert dialect.delimiter == ","

    def test_detect_skip_rows_and_dialect_single_note(self):
        """Test detection with single note line."""
        csv_path = str(self.test_data_dir / "single_note.csv")
        skip_rows, dialect = self.importer._detect_skip_rows_and_dialect(csv_path)
        assert skip_rows == 1
        assert dialect.delimiter == ","

    def test_detect_skip_rows_and_dialect_trailing_commas(self):
        """Test detection with trailing commas (real-world case)."""
        csv_path = str(self.test_data_dir / "trailing_commas.csv")
        skip_rows, dialect = self.importer._detect_skip_rows_and_dialect(csv_path)
        assert skip_rows == 3
        assert dialect.delimiter == ","

    def test_looks_like_csv_header(self):
        """Test CSV header detection logic."""
        # Typical header row
        header_row = ["Name", "Age", "City", "Email"]
        assert self.importer._looks_like_csv_header(header_row)

        # Twitter-style headers
        twitter_headers = [
            "Twitter screenname",
            "Date tweet sent",
            "Tweet text",
            "Times retweeted",
        ]
        assert self.importer._looks_like_csv_header(twitter_headers)

        # Note-style row (descriptive text)
        note_row = [
            "I like my csv files to have notes to make dialect detection harder"
        ]
        assert not self.importer._looks_like_csv_header(note_row)

        # Row with mostly empty fields (trailing commas)
        empty_row = ["From NBC News story", "", "", "", "", ""]
        assert not self.importer._looks_like_csv_header(empty_row)

    def test_init_session_with_notes(self):
        """Test session initialization with automatic note detection."""
        csv_path = str(self.test_data_dir / "notes_with_commas.csv")
        session = self.importer.init_session(csv_path)

        assert session.input_file == csv_path
        assert session.skip_rows == 2
        assert session.separator == ","
        assert session.has_header

    def test_init_session_no_notes(self):
        """Test session initialization with no notes."""
        csv_path = str(self.test_data_dir / "simple_header.csv")
        session = self.importer.init_session(csv_path)

        assert session.input_file == csv_path
        assert session.skip_rows == 0
        assert session.separator == ","
        assert session.has_header

    def test_load_preview_with_skip_rows(self):
        """Test data preview respects skip_rows parameter."""
        csv_path = str(self.test_data_dir / "notes_with_commas.csv")
        session = self.importer.init_session(csv_path)

        # Load preview - should skip notes and start from header
        df = session.load_preview(10)

        # Should have 3 rows (header + 2 data rows)
        assert len(df) == 2  # Data rows only (header is processed)

        # Should have correct columns from header
        expected_columns = ["A", "B", "C"]
        assert list(df.columns) == expected_columns

        # First data row should be (1, 2, 3)
        first_row = df.row(0)
        assert first_row == (1, 2, 3)
