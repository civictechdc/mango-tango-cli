from .csv import CSVImporter, CSVImporterTerminal
from .excel import ExcelImporter, ExcelImporterTerminal
from .importer import Importer, ImporterSession

# Terminal importers - includes interactive UI methods
importers: list[Importer[ImporterSession]] = [
    CSVImporterTerminal(),
    ExcelImporterTerminal(),
]

# GUI importers - core logic only, no terminal dependencies
gui_importers: list[Importer[ImporterSession]] = [
    CSVImporter(),
    ExcelImporter(),
]
