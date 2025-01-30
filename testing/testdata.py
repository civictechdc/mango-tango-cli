from abc import ABC, abstractmethod
from typing import TypeVar

import polars as pl
from pydantic import BaseModel

from preprocessing.series_semantic import SeriesSemantic

T = TypeVar("T", bound=pl.DataFrame | pl.LazyFrame)


class TestData(ABC, BaseModel):
    semantics: dict[str, SeriesSemantic]

    def load(self) -> pl.DataFrame:
        df = self._load_as_polars()
        return self._transform(df)

    def convert_to_parquet(self, target_path: str):
        try:
            # Attempt to convert to parquet lazily if possible.
            lf = self._scan_as_polars()
            return self._transform(lf).sink_parquet(target_path)
        except (NotImplementedError, pl.exceptions.InvalidOperationError):
            # If the lazy conversion is not possible, load the data in full
            # # and convert it to parquet.
            df = self.load()
            df.write_parquet(target_path)

    @abstractmethod
    def _load_as_polars(self) -> pl.DataFrame:
        pass

    def _scan_as_polars(self) -> pl.LazyFrame:
        raise NotImplementedError()

    def _transform[T](self, df: T) -> T:
        return df.with_columns(
            [
                pl.col(column_name)
                .map_batches(column_semantic.try_convert)
                .alias(column_name)
                for column_name in (
                    df.collect_schema().names()
                    if isinstance(df, pl.LazyFrame)
                    else df.columns
                )
                if (column_semantic := self.semantics.get(column_name)) is not None
            ]
        )


class FileTestData(TestData):
    filepath: str

    def __init__(self, filepath: str, *, semantics: dict[str, SeriesSemantic] = dict()):
        super().__init__(filepath=filepath, semantics=semantics)


class CsvConfig(BaseModel):
    has_header: bool = True
    quote_char: str = '"'
    encoding: str = "utf8"
    separator: str = ","


class CsvTestData(TestData):
    filepath: str
    csv_config: CsvConfig

    def __init__(
        self,
        filepath: str,
        *,
        csv_config: CsvConfig = CsvConfig(),
        semantics: dict[str, SeriesSemantic] = dict(),
    ):
        super().__init__(filepath=filepath, semantics=semantics, csv_config=csv_config)

    def _load_as_polars(self) -> pl.DataFrame:
        return pl.read_csv(self.filepath)

    def _scan_as_polars(self) -> pl.LazyFrame:
        return pl.scan_csv(self.filepath)


class JsonTestData(FileTestData):
    def _load_as_polars(self) -> pl.DataFrame:
        return pl.read_json(self.filepath)


class ExcelTestData(FileTestData):
    def _load_as_polars(self) -> pl.DataFrame:
        return pl.read_excel(self.filepath)


class PolarsTestData(TestData):
    def __init__(self, df: pl.DataFrame):
        self.df = df

    def _load_as_polars(self) -> pl.DataFrame:
        return self.df

    def _scan_as_polars(self) -> pl.LazyFrame:
        return self.df.lazy()
