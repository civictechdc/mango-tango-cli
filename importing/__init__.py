from .csv import CSVImporter
from .excel import ExcelImporter
from .importer import Importer, ImporterSession
from .json import JSONImporter

importers: list[Importer[ImporterSession]] = [
    CSVImporter(),
    JSONImporter(),
    ExcelImporter(),
]
