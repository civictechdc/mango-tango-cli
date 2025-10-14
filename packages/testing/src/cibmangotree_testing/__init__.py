"""Testing utilities for CIB Mango Tree analyzers.

This package provides utilities for testing analyzers including:
- Test data loaders (CSV, JSON, Excel, Parquet)
- Test context implementations for primary and secondary analyzers
- DataFrame comparison utilities
- Test runner functions
"""

from .comparers import compare_dfs
from .context import (
    TestOutputReaderGroupContext,
    TestOutputWriter,
    TestPrimaryAnalyzerContext,
    TestSecondaryAnalyzerContext,
    TestTableReader,
)
from .testdata import (
    CsvConfig,
    CsvTestData,
    ExcelTestData,
    JsonTestData,
    ParquetTestData,
    PolarsTestData,
    TestData,
)
from .testers import test_primary_analyzer, test_secondary_analyzer

__all__ = [
    # Test data loaders
    "CsvConfig",
    "CsvTestData",
    "ExcelTestData",
    "JsonTestData",
    "ParquetTestData",
    "PolarsTestData",
    "TestData",
    # Test contexts
    "TestPrimaryAnalyzerContext",
    "TestSecondaryAnalyzerContext",
    "TestOutputReaderGroupContext",
    "TestTableReader",
    "TestOutputWriter",
    # Comparison utilities
    "compare_dfs",
    # Test runners
    "test_primary_analyzer",
    "test_secondary_analyzer",
]
