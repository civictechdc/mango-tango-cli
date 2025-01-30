import os
from functools import cached_property
from tempfile import TemporaryDirectory

import polars as pl
from pydantic import BaseModel

from analyzer_interface import SecondaryAnalyzerInterface
from analyzer_interface.context import AssetsReader, InputTableReader
from analyzer_interface.context import (
    PrimaryAnalyzerContext as BasePrimaryAnalyzerContext,
)
from analyzer_interface.context import (
    SecondaryAnalyzerContext as BaseSecondaryAnalyzerContext,
)
from analyzer_interface.context import TableReader, TableWriter


class TestPrimaryAnalyzerContext(BasePrimaryAnalyzerContext):
    input_parquet_path: str
    output_parquet_root_path: str

    def input(self) -> InputTableReader:
        return TestTableReader(parquet_path=self.input_parquet_path)

    def output(self, output_id: str) -> TableWriter:
        return TestOutputWriter(parquet_path=self.output_path(output_id))

    def output_path(self, output_id):
        return os.path.join(self.output_parquet_root_path, output_id + ".parquet")

    def prepare(self):
        os.makedirs(
            os.path.dirname(self.output_parquet_paths),
            exist_ok=True,
        )


class TestTableReader(InputTableReader):
    def __init__(self, parquet_path: str):
        self._parquet_path = parquet_path

    @property
    def parquet_path(self) -> str:
        return self._parquet_path

    def preprocess(self, df: pl.DataFrame) -> pl.DataFrame:
        return df


class TestOutputWriter(TableWriter):
    def __init__(self, parquet_path: str):
        self._parquet_path = parquet_path

    @property
    def parquet_path(self) -> str:
        return self._parquet_path


class TestSecondaryAnalyzerContext(BaseSecondaryAnalyzerContext):
    primary_output_parquet_paths: dict[str, str]
    dependency_output_parquet_paths: dict[str, dict[str, str]] = dict()
    output_parquet_root_path: str

    class Config:
        arbitrary_types_allowed = True

    @cached_property
    def base(self) -> AssetsReader:
        return TestOutputReaderGroupContext(
            output_parquet_paths=self.primary_output_parquet_paths
        )

    def dependency(self, interface: SecondaryAnalyzerInterface) -> AssetsReader:
        return TestOutputReaderGroupContext(
            output_parquet_paths=self.dependency_output_parquet_paths[interface.id]
        )

    def temp_dir(self) -> str:
        return TemporaryDirectory(delete=True).name

    def output(self, output_id: str) -> TableWriter:
        return TestOutputWriter(
            parquet_path=os.path.join(
                self.output_parquet_root_path, f"{output_id}.parquet"
            )
        )

    def output_path(self, output_id):
        return os.path.join(self.output_parquet_root_path, output_id + ".parquet")

    def prepare(self):
        os.makedirs(
            os.path.dirname(self.output_parquet_paths),
            exist_ok=True,
        )


class TestOutputReaderGroupContext(AssetsReader, BaseModel):
    output_parquet_paths: dict[str, str]

    def table(self, output_id: str) -> TableReader:
        return TestTableReader(parquet_path=self.output_parquet_paths[output_id])
