import types
from pathlib import Path

from preprocessing.series_semantic import datetime_string, identifier, text_catch_all
from services.tokenizer.basic import TokenizerConfig, tokenize_text
from services.tokenizer.core.types import CaseHandling
from testing import CsvTestData, ParquetTestData, test_primary_analyzer

from .ngrams_base.interface import (
    COL_AUTHOR_ID,
    COL_MESSAGE_ID,
    COL_MESSAGE_NGRAM_COUNT,
    COL_MESSAGE_TEXT,
    COL_MESSAGE_TIMESTAMP,
    COL_NGRAM_ID,
    COL_NGRAM_WORDS,
    OUTPUT_MESSAGE,
    OUTPUT_MESSAGE_NGRAMS,
    OUTPUT_NGRAM_DEFS,
    PARAM_MAX_N,
    PARAM_MIN_N,
    interface,
)
from .ngrams_base.main import main, ngrams, serialize_ngram
from .test_data import test_data_dir

TEST_CSV_FILENAME = "ngrams_test_input.csv"
TEST_STRING = "Mango tree is an open source project."

# this is expected output of tokenize_text() with new tokenizer service
TEST_TOKENIZED_EXPECTED = [
    "mango",  # it's lower cased
    "tree",
    "is",
    "an",
    "open",
    "source",
    "project",  # punctuation is now separated - better for n-gram analysis
]

NGRAMS_EXPECTED_min1_max3 = [
    ["mango"],
    ["mango", "tree"],
    ["mango", "tree", "is"],
    ["tree"],
    ["tree", "is"],
    ["tree", "is", "an"],
    ["is"],
    ["is", "an"],
    ["is", "an", "open"],
    ["an"],
    ["an", "open"],
    ["an", "open", "source"],
    ["open"],
    ["open", "source"],
    ["open", "source", "project"],
    ["source"],
    ["source", "project"],
    ["project"],
]

NGRAMS_EXPECTED_min5_max7 = [
    ["mango", "tree", "is", "an", "open"],
    ["mango", "tree", "is", "an", "open", "source"],
    ["mango", "tree", "is", "an", "open", "source", "project"],
    ["tree", "is", "an", "open", "source"],
    ["tree", "is", "an", "open", "source", "project"],
    ["is", "an", "open", "source", "project"],
]

# if max ngram len is not found, it just returns all the shortest ngrams
NGRAMS_EXPECTED_min5_max8 = [
    ["mango", "tree", "is", "an", "open"],
    ["mango", "tree", "is", "an", "open", "source"],
    ["mango", "tree", "is", "an", "open", "source", "project"],
    ["tree", "is", "an", "open", "source"],
    ["tree", "is", "an", "open", "source", "project"],
    ["is", "an", "open", "source", "project"],
]


def test_tokenize():
    # Configure tokenizer for clean word extraction (no social media entities)
    config = TokenizerConfig(
        case_handling=CaseHandling.LOWERCASE,
        normalize_unicode=True,
        extract_hashtags=False,
        extract_mentions=False,
        include_urls=False,
        min_token_length=1,
    )
    test_tokenized_actual = tokenize_text(TEST_STRING, config)

    assert isinstance(
        test_tokenized_actual, list
    ), "output of tokenize_text() is not an instance of list"

    assert (
        test_tokenized_actual == TEST_TOKENIZED_EXPECTED
    ), "Tokenized strings do not match expected tokens."

    pass


def test_ngrams():
    # Configure tokenizer for clean word extraction (no social media entities)
    config = TokenizerConfig(
        case_handling=CaseHandling.LOWERCASE,
        normalize_unicode=True,
        extract_hashtags=False,
        extract_mentions=False,
        include_urls=False,
        min_token_length=1,
    )
    test_string_tokenized = tokenize_text(TEST_STRING, config)

    test_combinations = {
        "min1_max3": {
            "min_gram_len": 1,
            "max_ngram_len": 3,
            "n_expected_ngrams_found": 18,
        },
        "min5_max7": {
            "min_gram_len": 5,
            "max_ngram_len": 7,
            "n_expected_ngrams_found": 6,
        },
        "min5_max8": {
            "min_gram_len": 5,
            "max_ngram_len": 8,
            "n_expected_ngrams_found": 6,
        },
    }

    for test_key, test_params in test_combinations.items():
        ngrams_actual = ngrams(
            test_string_tokenized,
            min=test_params["min_gram_len"],
            max=test_params["max_ngram_len"],
        )

        assert isinstance(ngrams_actual, types.GeneratorType)
        assert (
            len(list(ngrams_actual)) == test_params["n_expected_ngrams_found"]
        ), f"Nr. expected tokens mismatch for {test_key}"


def test_serialize_ngram():
    NGRAM_SERIALIZED_EXPECTED_FIRST = "mango tree is an open"

    # Configure tokenizer for clean word extraction
    config = TokenizerConfig(
        case_handling=CaseHandling.LOWERCASE,
        normalize_unicode=True,
        extract_hashtags=False,
        extract_mentions=False,
        include_urls=False,
        min_token_length=1,
    )
    test_ngrams = list(ngrams(tokenize_text(TEST_STRING, config), min=5, max=8))

    test_ngram_serialized_actual = serialize_ngram(test_ngrams[0])

    assert NGRAM_SERIALIZED_EXPECTED_FIRST == test_ngram_serialized_actual


def test_within_message_repetition():
    """
    Test that repeated n-grams within a single message are counted correctly.

    This test validates Issue #241 fix for English text:
    - Message: "go go go now"
    - With bigrams (min_n=2, max_n=2)
    - Expected: bigram "go go" appears twice (positions 0-1 and 1-2)
    - After aggregation, should have count=2 for this n-gram in this message
    """
    import tempfile

    import polars as pl

    # Configure tokenizer for test
    config = TokenizerConfig(
        case_handling=CaseHandling.LOWERCASE,
        normalize_unicode=True,
        extract_hashtags=False,
        extract_mentions=False,
        include_urls=False,
        min_token_length=1,
    )

    # Test data: message with repeated bigram "go go"
    # Tokens: ["go", "go", "go", "now"]
    # Bigrams generated:
    #   Position 0-1: ["go", "go"] -> "go go"
    #   Position 1-2: ["go", "go"] -> "go go" (duplicate)
    #   Position 2-3: ["go", "now"] -> "go now"
    test_message = "go go go now"
    tokens = tokenize_text(test_message, config)

    # Verify tokenization is correct
    assert tokens == ["go", "go", "go", "now"], f"Unexpected tokens: {tokens}"

    # Generate bigrams manually to verify expected behavior
    bigrams_list = list(ngrams(tokens, min=2, max=2))
    assert len(bigrams_list) == 3, f"Expected 3 bigrams, got {len(bigrams_list)}"

    # Serialize bigrams
    serialized_bigrams = [serialize_ngram(bg) for bg in bigrams_list]

    # Count occurrences of each unique bigram
    from collections import Counter

    bigram_counts = Counter(serialized_bigrams)

    # Verify "go go" appears twice
    assert "go go" in bigram_counts, "Bigram 'go go' not found"
    assert (
        bigram_counts["go go"] == 2
    ), f"Expected 'go go' count=2, got {bigram_counts['go go']}"
    assert (
        bigram_counts["go now"] == 1
    ), f"Expected 'go now' count=1, got {bigram_counts['go now']}"

    # Now test with full analyzer pipeline using temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test input DataFrame
        df_input = pl.DataFrame(
            {
                COL_AUTHOR_ID: ["user_001"],
                COL_MESSAGE_ID: ["msg_test_001"],
                COL_MESSAGE_TEXT: [test_message],
                COL_MESSAGE_TIMESTAMP: ["2024-01-18T10:00:00Z"],
            }
        )

        input_path = tmpdir_path / "input.parquet"
        df_input.write_parquet(input_path)

        # Create output paths
        output_message_ngrams_path = tmpdir_path / "message_ngrams.parquet"
        output_ngrams_path = tmpdir_path / "ngrams.parquet"
        output_messages_path = tmpdir_path / "messages.parquet"

        # Create mock context
        class MockOutputHandle:
            def __init__(self, path):
                self.parquet_path = path

        class MockInputHandle:
            def __init__(self, path):
                self.parquet_path = path

            def preprocess(self, df):
                return df

        class MockContext:
            def __init__(self):
                self.params = {PARAM_MIN_N: 2, PARAM_MAX_N: 2}
                self._outputs = {
                    OUTPUT_MESSAGE_NGRAMS: MockOutputHandle(output_message_ngrams_path),
                    OUTPUT_NGRAM_DEFS: MockOutputHandle(output_ngrams_path),
                    OUTPUT_MESSAGE: MockOutputHandle(output_messages_path),
                }

            def input(self):
                return MockInputHandle(input_path)

            def output(self, name):
                return self._outputs[name]

        # Run the analyzer
        context = MockContext()
        main(context)  # type: ignore

        # Verify outputs exist
        assert output_message_ngrams_path.exists(), "message_ngrams.parquet not created"
        assert output_ngrams_path.exists(), "ngrams.parquet not created"

        # Load and verify message_ngrams output
        df_message_ngrams = pl.read_parquet(output_message_ngrams_path)

        # Should have 2 rows (one for each unique bigram)
        assert (
            len(df_message_ngrams) == 2
        ), f"Expected 2 rows, got {len(df_message_ngrams)}"

        # Load ngrams to get ngram_id mappings
        df_ngrams = pl.read_parquet(output_ngrams_path)

        # Find the "go go" ngram
        go_go_row = df_ngrams.filter(pl.col(COL_NGRAM_WORDS) == "go go")
        assert len(go_go_row) == 1, "Expected exactly one 'go go' ngram definition"
        go_go_id = go_go_row[COL_NGRAM_ID][0]

        # Find the count for "go go" in message_ngrams
        go_go_count_row = df_message_ngrams.filter(pl.col(COL_NGRAM_ID) == go_go_id)
        assert (
            len(go_go_count_row) == 1
        ), "Expected exactly one row for 'go go' in message_ngrams"
        go_go_count = go_go_count_row.select(COL_MESSAGE_NGRAM_COUNT).item()

        # THIS IS THE KEY ASSERTION: count should be 2
        assert go_go_count == 2, f"Expected 'go go' count=2, got {go_go_count}"


def test_korean_within_message_repetition():
    """
    Test that repeated n-grams within a single Korean message are counted correctly.

    This test is a regression test for Issue #241:
    - Message: "긴급 긴급 조치 필요" (Korean: "urgent urgent action needed")
    - With bigrams (min_n=2, max_n=2)
    - Expected bigrams:
      - "긴급 긴급" appears once (positions 0-1)
      - "긴급 조치" appears once (positions 1-2)
      - "조치 필요" appears once (positions 2-3)
    - After aggregation, each should have count=1
    """
    import tempfile
    from pathlib import Path

    import polars as pl

    # Configure tokenizer for test
    config = TokenizerConfig(
        case_handling=CaseHandling.LOWERCASE,
        normalize_unicode=True,
        extract_hashtags=False,
        extract_mentions=False,
        include_urls=False,
        min_token_length=1,
    )

    # Test data: Korean message with one repeated bigram
    # Korean is space-separated, so tokenization should split on spaces
    test_message = "긴급 긴급 조치 필요"
    tokens = tokenize_text(test_message, config)

    # Verify tokenization (Korean should be tokenized by spaces)
    # Note: case_handling might affect this - Korean doesn't have case, so should remain unchanged
    expected_tokens = ["긴급", "긴급", "조치", "필요"]
    assert (
        tokens == expected_tokens
    ), f"Unexpected tokens: {tokens}, expected: {expected_tokens}"

    # Generate bigrams manually
    bigrams_list = list(ngrams(tokens, min=2, max=2))
    assert len(bigrams_list) == 3, f"Expected 3 bigrams, got {len(bigrams_list)}"

    # Serialize and count
    serialized_bigrams = [serialize_ngram(bg) for bg in bigrams_list]
    from collections import Counter

    bigram_counts = Counter(serialized_bigrams)

    # Verify each bigram appears exactly once
    assert "긴급 긴급" in bigram_counts, "Bigram '긴급 긴급' not found"
    assert (
        bigram_counts["긴급 긴급"] == 1
    ), f"Expected '긴급 긴급' count=1, got {bigram_counts['긴급 긴급']}"
    assert (
        bigram_counts["긴급 조치"] == 1
    ), f"Expected '긴급 조치' count=1, got {bigram_counts['긴급 조치']}"
    assert (
        bigram_counts["조치 필요"] == 1
    ), f"Expected '조치 필요' count=1, got {bigram_counts['조치 필요']}"

    # Test with full analyzer pipeline
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test input DataFrame
        df_input = pl.DataFrame(
            {
                COL_AUTHOR_ID: ["user_002"],
                COL_MESSAGE_ID: ["msg_test_002"],
                COL_MESSAGE_TEXT: [test_message],
                COL_MESSAGE_TIMESTAMP: ["2024-01-18T11:00:00Z"],
            }
        )

        input_path = tmpdir_path / "input.parquet"
        df_input.write_parquet(input_path)

        # Create output paths
        output_message_ngrams_path = tmpdir_path / "message_ngrams.parquet"
        output_ngrams_path = tmpdir_path / "ngrams.parquet"
        output_messages_path = tmpdir_path / "messages.parquet"

        # Create mock context
        class MockOutputHandle:
            def __init__(self, path):
                self.parquet_path = path

        class MockInputHandle:
            def __init__(self, path):
                self.parquet_path = path

            def preprocess(self, df):
                return df

        class MockContext:
            def __init__(self):
                self.params = {PARAM_MIN_N: 2, PARAM_MAX_N: 2}
                self._outputs = {
                    OUTPUT_MESSAGE_NGRAMS: MockOutputHandle(output_message_ngrams_path),
                    OUTPUT_NGRAM_DEFS: MockOutputHandle(output_ngrams_path),
                    OUTPUT_MESSAGE: MockOutputHandle(output_messages_path),
                }

            def input(self):
                return MockInputHandle(input_path)

            def output(self, name):
                return self._outputs[name]

        # Run the analyzer
        context = MockContext()
        main(context)  # type: ignore

        # Verify outputs exist
        assert output_message_ngrams_path.exists(), "message_ngrams.parquet not created"
        assert output_ngrams_path.exists(), "ngrams.parquet not created"

        # Load and verify message_ngrams output
        df_message_ngrams = pl.read_parquet(output_message_ngrams_path)

        # Should have 3 rows (one for each unique bigram)
        assert (
            len(df_message_ngrams) == 3
        ), f"Expected 3 rows, got {len(df_message_ngrams)}"

        # Load ngrams to get ngram_id mappings
        df_ngrams = pl.read_parquet(output_ngrams_path)

        # Verify all counts are 1
        for row_dict in df_message_ngrams.iter_rows(named=True):
            count = row_dict[COL_MESSAGE_NGRAM_COUNT]
            assert (
                count == 1
            ), f"Expected all counts to be 1, got {count} for ngram_id {row_dict[COL_NGRAM_ID]}"

        # Verify specific bigrams exist
        ngram_words = df_ngrams.select(COL_NGRAM_WORDS).to_series().to_list()
        assert "긴급 긴급" in ngram_words, "Expected '긴급 긴급' in ngrams"
        assert "긴급 조치" in ngram_words, "Expected '긴급 조치' in ngrams"
        assert "조치 필요" in ngram_words, "Expected '조치 필요' in ngrams"


def test_overlapping_ngrams_repetition():
    """
    Test that overlapping n-grams with repetition are counted correctly.

    Scenario:
    - Message: "abc abc abc test"
    - Tokens: ["abc", "abc", "abc", "test"]
    - Bigrams:
      - Position 0-1: "abc abc"
      - Position 1-2: "abc abc" (overlaps with previous)
      - Position 2-3: "abc test"
    - Expected: "abc abc" count=2, "abc test" count=1
    """
    import tempfile

    import polars as pl

    config = TokenizerConfig(
        case_handling=CaseHandling.LOWERCASE,
        normalize_unicode=True,
        extract_hashtags=False,
        extract_mentions=False,
        include_urls=False,
        min_token_length=1,
    )

    test_message = "abc abc abc test"
    tokens = tokenize_text(test_message, config)
    assert tokens == ["abc", "abc", "abc", "test"], f"Unexpected tokens: {tokens}"

    # Generate bigrams and verify
    bigrams_list = list(ngrams(tokens, min=2, max=2))
    assert len(bigrams_list) == 3, f"Expected 3 bigrams, got {len(bigrams_list)}"

    # Count occurrences
    from collections import Counter

    serialized_bigrams = [serialize_ngram(bg) for bg in bigrams_list]
    bigram_counts = Counter(serialized_bigrams)

    assert (
        bigram_counts["abc abc"] == 2
    ), f"Expected 'abc abc' count=2, got {bigram_counts['abc abc']}"
    assert (
        bigram_counts["abc test"] == 1
    ), f"Expected 'abc test' count=1, got {bigram_counts['abc test']}"

    # Test with full analyzer pipeline
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        df_input = pl.DataFrame(
            {
                COL_AUTHOR_ID: ["user_edge_001"],
                COL_MESSAGE_ID: ["msg_edge_001"],
                COL_MESSAGE_TEXT: [test_message],
                COL_MESSAGE_TIMESTAMP: ["2024-01-18T12:00:00Z"],
            }
        )

        input_path = tmpdir_path / "input.parquet"
        df_input.write_parquet(input_path)

        output_message_ngrams_path = tmpdir_path / "message_ngrams.parquet"
        output_ngrams_path = tmpdir_path / "ngrams.parquet"
        output_messages_path = tmpdir_path / "messages.parquet"

        class MockOutputHandle:
            def __init__(self, path):
                self.parquet_path = path

        class MockInputHandle:
            def __init__(self, path):
                self.parquet_path = path

            def preprocess(self, df):
                return df

        class MockContext:
            def __init__(self):
                self.params = {PARAM_MIN_N: 2, PARAM_MAX_N: 2}
                self._outputs = {
                    OUTPUT_MESSAGE_NGRAMS: MockOutputHandle(output_message_ngrams_path),
                    OUTPUT_NGRAM_DEFS: MockOutputHandle(output_ngrams_path),
                    OUTPUT_MESSAGE: MockOutputHandle(output_messages_path),
                }

            def input(self):
                return MockInputHandle(input_path)

            def output(self, name):
                return self._outputs[name]

        context = MockContext()
        main(context)  # type: ignore

        # Verify outputs
        df_message_ngrams = pl.read_parquet(output_message_ngrams_path)
        df_ngrams = pl.read_parquet(output_ngrams_path)

        # Should have 2 unique bigrams
        assert (
            len(df_message_ngrams) == 2
        ), f"Expected 2 rows, got {len(df_message_ngrams)}"

        # Find "abc abc" and verify count=2
        abc_abc_row = df_ngrams.filter(pl.col(COL_NGRAM_WORDS) == "abc abc")
        assert len(abc_abc_row) == 1, "Expected exactly one 'abc abc' ngram definition"
        abc_abc_id = abc_abc_row[COL_NGRAM_ID][0]

        abc_abc_count_row = df_message_ngrams.filter(pl.col(COL_NGRAM_ID) == abc_abc_id)
        abc_abc_count = abc_abc_count_row.select(COL_MESSAGE_NGRAM_COUNT).item()
        assert abc_abc_count == 2, f"Expected 'abc abc' count=2, got {abc_abc_count}"

        # Find "abc test" and verify count=1
        abc_test_row = df_ngrams.filter(pl.col(COL_NGRAM_WORDS) == "abc test")
        assert (
            len(abc_test_row) == 1
        ), "Expected exactly one 'abc test' ngram definition"
        abc_test_id = abc_test_row[COL_NGRAM_ID][0]

        abc_test_count_row = df_message_ngrams.filter(
            pl.col(COL_NGRAM_ID) == abc_test_id
        )
        abc_test_count = abc_test_count_row.select(COL_MESSAGE_NGRAM_COUNT).item()
        assert abc_test_count == 1, f"Expected 'abc test' count=1, got {abc_test_count}"


def test_mixed_unique_and_repeated_ngrams():
    """
    Test that messages with both unique and repeated n-grams are handled correctly.

    Scenario:
    - Message: "hello world hello again"
    - Tokens: ["hello", "world", "hello", "again"]
    - Bigrams:
      - Position 0-1: "hello world"
      - Position 1-2: "world hello"
      - Position 2-3: "hello again"
    - All unique bigrams, each count=1
    """
    import tempfile

    import polars as pl

    config = TokenizerConfig(
        case_handling=CaseHandling.LOWERCASE,
        normalize_unicode=True,
        extract_hashtags=False,
        extract_mentions=False,
        include_urls=False,
        min_token_length=1,
    )

    test_message = "hello world hello again"
    tokens = tokenize_text(test_message, config)
    assert tokens == [
        "hello",
        "world",
        "hello",
        "again",
    ], f"Unexpected tokens: {tokens}"

    # Generate bigrams
    bigrams_list = list(ngrams(tokens, min=2, max=2))
    assert len(bigrams_list) == 3, f"Expected 3 bigrams, got {len(bigrams_list)}"

    # Count occurrences
    from collections import Counter

    serialized_bigrams = [serialize_ngram(bg) for bg in bigrams_list]
    bigram_counts = Counter(serialized_bigrams)

    # All should be unique
    assert (
        len(bigram_counts) == 3
    ), f"Expected 3 unique bigrams, got {len(bigram_counts)}"
    for bigram, count in bigram_counts.items():
        assert count == 1, f"Expected all counts=1, got {count} for '{bigram}'"

    # Test with full analyzer pipeline
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        df_input = pl.DataFrame(
            {
                COL_AUTHOR_ID: ["user_edge_002"],
                COL_MESSAGE_ID: ["msg_edge_002"],
                COL_MESSAGE_TEXT: [test_message],
                COL_MESSAGE_TIMESTAMP: ["2024-01-18T13:00:00Z"],
            }
        )

        input_path = tmpdir_path / "input.parquet"
        df_input.write_parquet(input_path)

        output_message_ngrams_path = tmpdir_path / "message_ngrams.parquet"
        output_ngrams_path = tmpdir_path / "ngrams.parquet"
        output_messages_path = tmpdir_path / "messages.parquet"

        class MockOutputHandle:
            def __init__(self, path):
                self.parquet_path = path

        class MockInputHandle:
            def __init__(self, path):
                self.parquet_path = path

            def preprocess(self, df):
                return df

        class MockContext:
            def __init__(self):
                self.params = {PARAM_MIN_N: 2, PARAM_MAX_N: 2}
                self._outputs = {
                    OUTPUT_MESSAGE_NGRAMS: MockOutputHandle(output_message_ngrams_path),
                    OUTPUT_NGRAM_DEFS: MockOutputHandle(output_ngrams_path),
                    OUTPUT_MESSAGE: MockOutputHandle(output_messages_path),
                }

            def input(self):
                return MockInputHandle(input_path)

            def output(self, name):
                return self._outputs[name]

        context = MockContext()
        main(context)  # type: ignore

        # Verify outputs
        df_message_ngrams = pl.read_parquet(output_message_ngrams_path)

        # Should have 3 unique bigrams
        assert (
            len(df_message_ngrams) == 3
        ), f"Expected 3 rows, got {len(df_message_ngrams)}"

        # Verify all counts are 1
        for row_dict in df_message_ngrams.iter_rows(named=True):
            count = row_dict[COL_MESSAGE_NGRAM_COUNT]
            assert count == 1, f"Expected all counts=1, got {count}"


def test_long_ngram_repetition():
    """
    Test that repetition counting works for longer n-grams (trigrams).

    Scenario:
    - Message: "the quick brown the quick brown fox"
    - Tokens: ["the", "quick", "brown", "the", "quick", "brown", "fox"]
    - Trigrams:
      - Position 0-2: "the quick brown"
      - Position 1-3: "quick brown the"
      - Position 2-4: "brown the quick"
      - Position 3-5: "the quick brown" (repeat)
      - Position 4-6: "quick brown fox"
    - Expected: "the quick brown" count=2, others count=1
    """
    import tempfile

    import polars as pl

    config = TokenizerConfig(
        case_handling=CaseHandling.LOWERCASE,
        normalize_unicode=True,
        extract_hashtags=False,
        extract_mentions=False,
        include_urls=False,
        min_token_length=1,
    )

    test_message = "the quick brown the quick brown fox"
    tokens = tokenize_text(test_message, config)
    expected_tokens = ["the", "quick", "brown", "the", "quick", "brown", "fox"]
    assert tokens == expected_tokens, f"Unexpected tokens: {tokens}"

    # Generate trigrams
    trigrams_list = list(ngrams(tokens, min=3, max=3))
    assert len(trigrams_list) == 5, f"Expected 5 trigrams, got {len(trigrams_list)}"

    # Count occurrences
    from collections import Counter

    serialized_trigrams = [serialize_ngram(tg) for tg in trigrams_list]
    trigram_counts = Counter(serialized_trigrams)

    # Verify "the quick brown" appears twice
    assert (
        trigram_counts["the quick brown"] == 2
    ), f"Expected 'the quick brown' count=2, got {trigram_counts['the quick brown']}"

    # Test with full analyzer pipeline
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        df_input = pl.DataFrame(
            {
                COL_AUTHOR_ID: ["user_edge_003"],
                COL_MESSAGE_ID: ["msg_edge_003"],
                COL_MESSAGE_TEXT: [test_message],
                COL_MESSAGE_TIMESTAMP: ["2024-01-18T14:00:00Z"],
            }
        )

        input_path = tmpdir_path / "input.parquet"
        df_input.write_parquet(input_path)

        output_message_ngrams_path = tmpdir_path / "message_ngrams.parquet"
        output_ngrams_path = tmpdir_path / "ngrams.parquet"
        output_messages_path = tmpdir_path / "messages.parquet"

        class MockOutputHandle:
            def __init__(self, path):
                self.parquet_path = path

        class MockInputHandle:
            def __init__(self, path):
                self.parquet_path = path

            def preprocess(self, df):
                return df

        class MockContext:
            def __init__(self):
                self.params = {PARAM_MIN_N: 3, PARAM_MAX_N: 3}
                self._outputs = {
                    OUTPUT_MESSAGE_NGRAMS: MockOutputHandle(output_message_ngrams_path),
                    OUTPUT_NGRAM_DEFS: MockOutputHandle(output_ngrams_path),
                    OUTPUT_MESSAGE: MockOutputHandle(output_messages_path),
                }

            def input(self):
                return MockInputHandle(input_path)

            def output(self, name):
                return self._outputs[name]

        context = MockContext()
        main(context)  # type: ignore

        # Verify outputs
        df_message_ngrams = pl.read_parquet(output_message_ngrams_path)
        df_ngrams = pl.read_parquet(output_ngrams_path)

        # Should have 4 unique trigrams
        assert (
            len(df_message_ngrams) == 4
        ), f"Expected 4 rows, got {len(df_message_ngrams)}"

        # Find "the quick brown" and verify count=2
        the_quick_brown_row = df_ngrams.filter(
            pl.col(COL_NGRAM_WORDS) == "the quick brown"
        )
        assert (
            len(the_quick_brown_row) == 1
        ), "Expected exactly one 'the quick brown' ngram definition"
        the_quick_brown_id = the_quick_brown_row[COL_NGRAM_ID][0]

        the_quick_brown_count_row = df_message_ngrams.filter(
            pl.col(COL_NGRAM_ID) == the_quick_brown_id
        )
        the_quick_brown_count = the_quick_brown_count_row.select(
            COL_MESSAGE_NGRAM_COUNT
        ).item()
        assert (
            the_quick_brown_count == 2
        ), f"Expected 'the quick brown' count=2, got {the_quick_brown_count}"


def test_single_token_message():
    """
    Test that single-token messages generate no n-grams when min_n > 1.

    Scenario:
    - Message: "hello"
    - Tokens: ["hello"]
    - Bigrams: None (need at least 2 tokens)
    - Expected: Zero rows in output
    """
    import tempfile

    import polars as pl

    config = TokenizerConfig(
        case_handling=CaseHandling.LOWERCASE,
        normalize_unicode=True,
        extract_hashtags=False,
        extract_mentions=False,
        include_urls=False,
        min_token_length=1,
    )

    test_message = "hello"
    tokens = tokenize_text(test_message, config)
    assert tokens == ["hello"], f"Unexpected tokens: {tokens}"

    # Generate bigrams - should be empty
    bigrams_list = list(ngrams(tokens, min=2, max=2))
    assert len(bigrams_list) == 0, f"Expected 0 bigrams, got {len(bigrams_list)}"

    # Test with full analyzer pipeline
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        df_input = pl.DataFrame(
            {
                COL_AUTHOR_ID: ["user_edge_004"],
                COL_MESSAGE_ID: ["msg_edge_004"],
                COL_MESSAGE_TEXT: [test_message],
                COL_MESSAGE_TIMESTAMP: ["2024-01-18T15:00:00Z"],
            }
        )

        input_path = tmpdir_path / "input.parquet"
        df_input.write_parquet(input_path)

        output_message_ngrams_path = tmpdir_path / "message_ngrams.parquet"
        output_ngrams_path = tmpdir_path / "ngrams.parquet"
        output_messages_path = tmpdir_path / "messages.parquet"

        class MockOutputHandle:
            def __init__(self, path):
                self.parquet_path = path

        class MockInputHandle:
            def __init__(self, path):
                self.parquet_path = path

            def preprocess(self, df):
                return df

        class MockContext:
            def __init__(self):
                self.params = {PARAM_MIN_N: 2, PARAM_MAX_N: 2}
                self._outputs = {
                    OUTPUT_MESSAGE_NGRAMS: MockOutputHandle(output_message_ngrams_path),
                    OUTPUT_NGRAM_DEFS: MockOutputHandle(output_ngrams_path),
                    OUTPUT_MESSAGE: MockOutputHandle(output_messages_path),
                }

            def input(self):
                return MockInputHandle(input_path)

            def output(self, name):
                return self._outputs[name]

        context = MockContext()
        main(context)  # type: ignore

        # Verify outputs
        df_message_ngrams = pl.read_parquet(output_message_ngrams_path)
        df_ngrams = pl.read_parquet(output_ngrams_path)

        # Should have zero n-grams
        assert (
            len(df_message_ngrams) == 0
        ), f"Expected 0 rows for single-token message, got {len(df_message_ngrams)}"
        assert (
            len(df_ngrams) == 0
        ), f"Expected 0 ngram definitions, got {len(df_ngrams)}"

        # Messages table should still have the message record
        df_messages = pl.read_parquet(output_messages_path)
        assert (
            len(df_messages) == 1
        ), f"Expected 1 message record, got {len(df_messages)}"


def test_ngram_analyzer():
    test_primary_analyzer(
        interface=interface,
        main=main,
        input=CsvTestData(
            filepath=str(Path(test_data_dir, TEST_CSV_FILENAME)),
            semantics={
                COL_AUTHOR_ID: identifier,
                COL_MESSAGE_ID: identifier,
                COL_MESSAGE_TEXT: text_catch_all,
                COL_MESSAGE_TIMESTAMP: datetime_string,
            },
        ),
        outputs={
            OUTPUT_MESSAGE_NGRAMS: ParquetTestData(
                filepath=str(Path(test_data_dir, OUTPUT_MESSAGE_NGRAMS + ".parquet")),
                semantics={},
            ),
            OUTPUT_NGRAM_DEFS: ParquetTestData(
                filepath=str(Path(test_data_dir, OUTPUT_NGRAM_DEFS + ".parquet")),
                semantics={},
            ),
            OUTPUT_MESSAGE: ParquetTestData(
                filepath=str(Path(test_data_dir, OUTPUT_MESSAGE + ".parquet")),
                semantics={},
            ),
        },
    )
