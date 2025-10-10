"""
Services Module

This module provides core services for CIB Mango Tree:
- storage: Data persistence, project management, and file operations
- importing: Data import from CSV, Excel, and other formats
- preprocessing: Data preprocessing and semantic type detection
"""

# Re-export storage (no circular import)
from .storage import Storage


# Lazy import for importing module to avoid circular import
# The importing module imports from TUI which imports from app
def __getattr__(name):
    if name == "CSVImporter":
        from .importing import CSVImporter

        return CSVImporter
    elif name == "ExcelImporter":
        from .importing import ExcelImporter

        return ExcelImporter
    elif name == "Importer":
        from .importing import Importer

        return Importer
    elif name == "ImporterSession":
        from .importing import ImporterSession

        return ImporterSession
    elif name == "SeriesSemantic":
        from .preprocessing import SeriesSemantic

        return SeriesSemantic
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Storage
    "Storage",
    # Importing (lazy)
    "CSVImporter",
    "ExcelImporter",
    "Importer",
    "ImporterSession",
    # Preprocessing (lazy)
    "SeriesSemantic",
]
