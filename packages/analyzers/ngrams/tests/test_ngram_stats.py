from pathlib import Path

from cibmangotree_analyzer_ngrams.base.interface import (
    OUTPUT_MESSAGE,
    OUTPUT_MESSAGE_NGRAMS,
    OUTPUT_NGRAM_DEFS,
)
from cibmangotree_analyzer_ngrams.stats.interface import (
    OUTPUT_NGRAM_FULL,
    OUTPUT_NGRAM_STATS,
    interface,
)
from cibmangotree_analyzer_ngrams.stats.main import main
from cibmangotree_testing import ParquetTestData, test_secondary_analyzer

test_data_dir = Path(__file__).parent / "test_data"


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
