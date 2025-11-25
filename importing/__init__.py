from .csv import CSVImporter, CSVImporterTerminal
from .excel import ExcelImporter, ExcelImporterTerminal
from .importer import Importer, ImporterSession

# Core importers - no terminal dependencies
importers: list[Importer[ImporterSession]] = [
    CSVImporter(),
    ExcelImporter(),
]

# Terminal importers - includes interactive UI methods
terminal_importers: list[Importer[ImporterSession]] = [
    CSVImporterTerminal(),
    ExcelImporterTerminal(),
]
