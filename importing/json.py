import polars as pl
from pydantic import BaseModel

from .importer import Importer, ImporterSession


class JSONImporter(Importer["JsonImportSession"]):
    @property
    def name(self) -> str:
        return "JSON"

    def suggest(self, input_path: str) -> bool:
        return input_path.endswith(".json")

    def init_session(self, input_path: str):
        return JsonImportSession(input_file=input_path)

    def manual_init_session(self, input_path: str):
        return JsonImportSession(input_file=input_path)

    def modify_session(
        self, input_path: str, import_session: "JsonImportSession", reset_screen
    ):
        return import_session


class JsonImportSession(ImporterSession, BaseModel):
    input_file: str

    def print_config(self):
        print(f"- JSON file: {self.input_file}")

    def load_preview(self, n_records: int) -> pl.DataFrame:
        return pl.read_json(self.input_file).head(n_records)

    def import_as_parquet(self, output_path: str) -> None:
        df = pl.read_json(self.input_file)
        df.write_parquet(output_path)
