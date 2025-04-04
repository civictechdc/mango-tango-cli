from .csv import CSVImporter
from .excel import ExcelImporter
from .importer import Importer, ImporterSession

importers: list[Importer[ImporterSession]] = [CSVImporter(), ExcelImporter()]
