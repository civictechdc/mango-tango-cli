from pathlib import Path

from testing import ParquetTestData, test_secondary_analyzer

from .ngram_stats.interface import OUTPUT_NGRAM_FULL, OUTPUT_NGRAM_STATS, interface
from .ngram_stats.main import main
from .ngrams_base.interface import (
    OUTPUT_MESSAGE,
    OUTPUT_MESSAGE_NGRAMS,
    OUTPUT_NGRAM_DEFS,
)
from .test_data import test_data_dir


# This example shows you how to test a secondary analyzer.
# It runs on pytest.
def test_ngram_stats():
    # You use this test function.
    test_secondary_analyzer(
        interface,
        main,
        primary_outputs={
            OUTPUT_MESSAGE_NGRAMS: ParquetTestData(
                filepath=str(Path(test_data_dir, OUTPUT_MESSAGE_NGRAMS + ".parquet"))
            ),
            OUTPUT_NGRAM_DEFS: ParquetTestData(
                filepath=str(Path(test_data_dir, OUTPUT_NGRAM_DEFS + ".parquet"))
            ),
            OUTPUT_MESSAGE: ParquetTestData(
                filepath=str(Path(test_data_dir, OUTPUT_MESSAGE + ".parquet"))
            ),
        },
        expected_outputs={
            OUTPUT_NGRAM_STATS: ParquetTestData(
                str(Path(test_data_dir, OUTPUT_NGRAM_STATS + ".parquet"))
            ),
            OUTPUT_NGRAM_FULL: ParquetTestData(
                str(Path(test_data_dir, OUTPUT_NGRAM_FULL + ".parquet"))
            ),
        },
    )
