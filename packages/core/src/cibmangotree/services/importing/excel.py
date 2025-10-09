from typing import Callable

import polars as pl
from fastexcel import read_excel
from pydantic import BaseModel

import terminal_tools.prompts as prompts
from terminal_tools.utils import wait_for_key

from .importer import Importer, ImporterSession


class ExcelImporter(Importer["ExcelImportSession"]):
    @property
    def name(self) -> str:
        return "Excel"

    def suggest(self, input_path: str) -> bool:
        return input_path.endswith(".xlsx")

    def init_session(self, input_path: str):
        reader = read_excel(input_path)
        sheet_names = reader.sheet_names

        if not sheet_names:
            return None
        if len(sheet_names) == 1:
            return ExcelImportSession(
                input_file=input_path,
                selected_sheet=sheet_names[0],
                sheet_names=sheet_names,
            )

        sheet_name = prompts.list_input(
            "Which sheet would you like to import?", choices=sheet_names
        )
        if sheet_name is None:
            return None

        return ExcelImportSession(
            input_file=input_path,
            selected_sheet=sheet_name,
            sheet_names=sheet_names,
        )

    def manual_init_session(self, input_path: str):
        return self.init_session(input_path)

    def modify_session(
        self,
        input_path: str,
        import_session: "ExcelImportSession",
        reset_screen: Callable[[], None],
    ):
        reset_screen(import_session)
        if len(import_session.sheet_names) == 1:
            print("This Excel file only has one sheet.\nThere's nothing to modify.\n\n")
            wait_for_key(prompt=True)
            return import_session

        new_session = self.init_session(input_path)
        return new_session or import_session


class ExcelImportSession(ImporterSession, BaseModel):
    input_file: str
    selected_sheet: str
    sheet_names: list[str]

    def print_config(self):
        print(f"- Sheet name: {self.selected_sheet}")

    def load_preview(self, n_records: int) -> pl.DataFrame:
        return pl.read_excel(self.input_file, sheet_name=self.selected_sheet).head(
            n_records
        )

    def import_as_parquet(self, output_path: str) -> None:
        return pl.read_excel(
            self.input_file, sheet_name=self.selected_sheet
        ).write_parquet(output_path)
