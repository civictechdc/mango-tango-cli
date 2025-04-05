import polars as pl
from pydantic import BaseModel
from .importer import Importer, ImporterSession

class ExcelImporter(Importer["ExcelImportSession"]):
    @property
    def name(self) -> str:
        return "Excel"

    def suggest(self, input_path: str) -> bool:
        return input_path.endswith(".xlsx") or input_path.endswith(".xls")

    def init_session(self, input_path: str):
        return ExcelImportSession(input_file=input_path)

    def manual_init_session(self, input_path: str):
        return ExcelImportSession(input_file=input_path)

    def modify_session(self, input_path: str, import_session: "ExcelImportSession", reset_screen):
        return import_session

class ExcelImportSession(ImporterSession, BaseModel):
    input_file: str
    sheet_name: str = "Sheet1"

    def print_config(self):
        print(f"- Excel file: {self.input_file}\n- Sheet: {self.sheet_name}")

    def load_preview(self, n_records: int) -> pl.DataFrame:
        return pl.read_excel(self.input_file, sheet_name=self.sheet_name).head(n_records)

    def import_as_parquet(self, output_path: str) -> None:
        df = pl.read_excel(self.input_file, sheet_name=self.sheet_name)
        df.write_parquet(output_path)
