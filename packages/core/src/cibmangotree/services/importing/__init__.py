# Import base classes first (no circular dependency)
from .importer import Importer, ImporterSession

# Lazy import for CSV and Excel to avoid circular import
# CSV/Excel importers use TUI which imports from app
def __getattr__(name):
    if name == "CSVImporter":
        from .csv import CSVImporter
        return CSVImporter
    elif name == "ExcelImporter":
        from .excel import ExcelImporter
        return ExcelImporter
    elif name == "importers":
        from .csv import CSVImporter
        from .excel import ExcelImporter
        return [CSVImporter(), ExcelImporter()]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["Importer", "ImporterSession", "CSVImporter", "ExcelImporter", "importers"]
