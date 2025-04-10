from .csv import CSVImporter
from .json import JSONImporter
from .excel import ExcelImporter
from .importer import Importer, ImporterSession

importers: list[Importer[ImporterSession]] = [CSVImporter(), JSONImporter(), ExcelImporter()]
