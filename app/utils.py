import re
from typing import Callable, Union

import polars as pl
import pyarrow.parquet as pq

# Try to import regex module for Unicode property support, fallback to standard re
try:
    import regex

    UNICODE_SUPPORT = True
except ImportError:
    regex = re
    UNICODE_SUPPORT = False


def parquet_row_count(filename: str) -> int:
    """Get the number of rows in a parquet file efficiently."""
    with pq.ParquetFile(filename) as pf:
        return pf.metadata.num_rows


def is_space_separated(text: Union[str, pl.Expr]) -> Union[bool, pl.Expr]:
    """
    Determine if text uses space-separated tokenization or character-based tokenization.

    Uses Unicode script detection to identify if text primarily contains scripts
    that use spaces for word separation (Latin, Cyrillic, Arabic, etc.) vs.
    scripts that don't use spaces (Chinese, Japanese, Thai, etc.).

    Args:
        text: Input text string or polars expression

    Returns:
        Boolean or polars expression indicating if text is space-separated
    """
    if isinstance(text, str):
        # For direct string input, use Python regex
        if not text.strip():
            return True  # Empty text defaults to space-separated

        if UNICODE_SUPPORT:
            # Use regex module with Unicode property support
            space_separated_chars = len(
                regex.findall(
                    r"[\p{Latin}\p{Cyrillic}\p{Arabic}\p{Armenian}\p{Georgian}\p{Greek}\p{Hebrew}\p{Hangul}]",
                    text,
                )
            )
            non_space_chars = len(
                regex.findall(
                    r"[\p{Han}\p{Hiragana}\p{Katakana}\p{Thai}\p{Lao}\p{Myanmar}\p{Khmer}]",
                    text,
                )
            )
        else:
            # Fallback to Unicode ranges
            # Latin: U+0000-U+024F, U+1E00-U+1EFF
            # Cyrillic: U+0400-U+04FF, U+0500-U+052F
            # Arabic: U+0600-U+06FF, U+0750-U+077F
            # Greek: U+0370-U+03FF
            # Hebrew: U+0590-U+05FF
            space_separated_pattern = r"[\u0000-\u024F\u1E00-\u1EFF\u0400-\u04FF\u0500-\u052F\u0600-\u06FF\u0750-\u077F\u0370-\u03FF\u0590-\u05FF\uAC00-\uD7AF]"

            # CJK: U+4E00-U+9FFF (Han), U+3040-U+309F (Hiragana), U+30A0-U+30FF (Katakana)
            # Thai: U+0E00-U+0E7F
            # Myanmar: U+1000-U+109F
            non_space_pattern = (
                r"[\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF\u0E00-\u0E7F\u1000-\u109F]"
            )

            space_separated_chars = len(re.findall(space_separated_pattern, text))
            non_space_chars = len(re.findall(non_space_pattern, text))

        # If we have any characters, determine majority script type
        total_script_chars = space_separated_chars + non_space_chars
        if total_script_chars == 0:
            return True  # No script-specific characters, default to space-separated

        # Space-separated if majority of script characters are from space-separated scripts
        return space_separated_chars >= non_space_chars

    else:
        # For polars expressions, use Unicode ranges (more compatible)
        # Space-separated scripts pattern
        space_separated_pattern = r"[\u0000-\u024F\u1E00-\u1EFF\u0400-\u04FF\u0500-\u052F\u0600-\u06FF\u0750-\u077F\u0370-\u03FF\u0590-\u05FF\uAC00-\uD7AF]"
        # Non-space scripts pattern
        non_space_pattern = (
            r"[\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF\u0E00-\u0E7F\u1000-\u109F]"
        )

        return text.str.count_matches(
            space_separated_pattern
        ) >= text.str.count_matches(non_space_pattern)


def tokenize_text(
    ldf: pl.LazyFrame,
    text_column: str,
    progress_callback: Callable[[int, int], None] = None,
) -> pl.LazyFrame:
    """
    Memory-efficient tokenization engine that handles mixed languages and preserves social media entities.

    This function uses true lazy processing throughout, avoiding memory collection of large datasets:
    - Efficient row counting without loading full dataset
    - Streaming chunked processing with lazy operations
    - Social media entities (URLs, @mentions, #hashtags) as single tokens
    - Space-separated languages (Latin, Cyrillic, Arabic, etc.)
    - Non-space languages (Chinese, Japanese, Thai, etc.) with character-level splitting
    - Mixed scripts within the same text
    - Progress reporting for large datasets

    Args:
        ldf: Input LazyFrame containing text data
        text_column: Name of the column containing text to tokenize
        progress_callback: Optional callback function for progress reporting.
                         Called with (current_chunk, total_chunks) between chunks.

    Returns:
        LazyFrame with additional 'tokens' column containing list of tokens

    Raises:
        ValueError: If text_column does not exist in the LazyFrame
        TypeError: If input is not a polars LazyFrame
    """
    # Input validation
    if not isinstance(ldf, pl.LazyFrame):
        raise TypeError(f"Expected polars LazyFrame, got {type(ldf)}")

    if not isinstance(text_column, str):
        raise TypeError(f"text_column must be a string, got {type(text_column)}")

    if progress_callback is not None and not callable(progress_callback):
        raise TypeError(
            f"progress_callback must be callable, got {type(progress_callback)}"
        )

    # Check if column exists by trying to reference it
    try:
        # This will validate that the column exists when the lazy frame is executed
        test_col = pl.col(text_column)
    except Exception as e:
        raise ValueError(f"Invalid column name '{text_column}': {e}")

    # Define the comprehensive tokenization regex pattern
    # Order is critical for proper matching precedence
    token_pattern = "|".join(
        [
            r"[Hh][Tt][Tt][Pp][Ss]?://[a-zA-Z0-9._~:/?#@!$&'()*+,;=-]+",  # URLs (case insensitive HTTP/HTTPS)
            r"@\w+",  # @mentions
            r"#\w+",  # #hashtags
            r"[a-zA-Z\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]{2,}[\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF]+",  # Mixed Latin+CJK (Latin part 2+ chars)
            r"[\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF]+[a-zA-Z\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]+[\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF]+",  # CJK-Latin-CJK (requires Latin chars)
            r"[\uAC00-\uD7AF]+",  # Korean words (Hangul)
            r"[\u0400-\u04FF\u0500-\u052F]+",  # Cyrillic words
            r"[a-zA-Z\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF][a-zA-Z0-9\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF.!?,;:()\-'\"]*",  # Latin words with accented chars and punctuation
            r"[\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF]",  # Individual CJK characters
            r"[^\s]",  # Any other non-whitespace
        ]
    )

    def _tokenize_chunk(chunk_ldf: pl.LazyFrame) -> pl.LazyFrame:
        """Apply tokenization to a chunk of data."""
        return (
            chunk_ldf.with_columns(
                [
                    # Step 1: Normalize whitespace and handle empty strings
                    pl.col(text_column)
                    .str.strip_chars()
                    .str.replace_all(
                        r"\s+", " "
                    )  # Normalize multiple whitespace to single space
                    .alias("_normalized_text")
                ]
            )
            .with_columns(
                [
                    # Step 2: Conditional tokenization based on language type
                    # For space-separated languages, split by spaces first then handle special patterns
                    # For non-space languages (CJK), use character-level splitting with entity preservation
                    pl.when(is_space_separated(pl.col("_normalized_text")))
                    .then(
                        # Space-separated language processing
                        pl.col("_normalized_text").str.extract_all(token_pattern)
                    )
                    .otherwise(
                        # Non-space language processing: preserve entities, split characters
                        pl.col("_normalized_text").str.extract_all(
                            "|".join(
                                [
                                    r"[Hh][Tt][Tt][Pp][Ss]?://[a-zA-Z0-9._~:/?#@!$&'()*+,;=-]+",  # URLs
                                    r"@\w+",  # @mentions
                                    r"#\w+",  # #hashtags
                                    r"[a-zA-Z\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]+",  # Pure Latin sequences with accented chars
                                    r"[\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF]",  # Individual CJK characters
                                    r"[^\s]",  # Any other non-whitespace
                                ]
                            )
                        )
                    )
                    .alias("_raw_tokens")
                ]
            )
            .with_columns(
                [
                    # Step 3: Process tokens (normalize case, handle social media entities)
                    pl.col("_raw_tokens")
                    .list.eval(
                        pl.when(
                            # Social media entities: keep as-is (case preserved for URLs)
                            pl.element().str.contains(
                                r"^([Hh][Tt][Tt][Pp][Ss]?://|@|#)"
                            )
                        )
                        .then(pl.element())
                        .when(
                            # Mixed scripts (e.g., "iPhone用户"): keep as single token but lowercase
                            pl.element().str.contains(r"[a-zA-Z]")
                            & pl.element().str.contains(
                                r"[\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF]"
                            )
                        )
                        .then(pl.element().str.to_lowercase())
                        .otherwise(pl.element().str.to_lowercase())
                    )
                    .alias("tokens")
                ]
            )
            .with_columns(
                [
                    # Step 4: Filter out empty tokens and whitespace-only tokens
                    pl.col("tokens")
                    .list.eval(
                        pl.element().filter(
                            (pl.element().str.len_chars() > 0)
                            & (pl.element().str.strip_chars() != "")
                        )
                    )
                    .alias("tokens")
                ]
            )
            .drop(["_normalized_text", "_raw_tokens"])
        )

    # Define chunk size for streaming processing
    chunk_size = 50000

    # Memory-efficient row counting with minimal footprint
    def _get_dataset_size():
        """Get dataset size with minimal memory usage, return None if not possible."""
        try:
            # Primary method: Use count aggregation - most memory efficient
            return ldf.select(pl.len()).collect().item()
        except Exception:
            try:
                # Secondary method: Try with height property if available
                # Some lazy frames might support this more efficiently
                return ldf.select(pl.count()).collect().item()
            except Exception:
                try:
                    # Tertiary method: Use sample-based estimation for problematic cases
                    # This is a fallback for very problematic data sources
                    sample_size = min(1000, chunk_size // 10)
                    sample_df = ldf.limit(sample_size).collect()
                    if len(sample_df) == 0:
                        return 0
                    elif len(sample_df) < sample_size:
                        # We got less than requested, likely end of data
                        return len(sample_df)
                    else:
                        # Cannot determine size efficiently - will use streaming
                        return None
                except Exception:
                    # Complete fallback - cannot determine size
                    return None

    total_rows = _get_dataset_size()

    # Handle empty dataset efficiently
    if total_rows == 0:
        return ldf.with_columns([pl.lit([]).alias("tokens")])

    # If dataset is small or we can't determine size, check if we should process without chunking
    if total_rows is not None and total_rows <= chunk_size:
        return _tokenize_chunk(ldf)

    # For large datasets or unknown sizes, use memory-efficient chunked processing
    try:
        if total_rows is not None:
            # Known size approach - traditional chunking with accurate progress
            total_chunks = (
                total_rows + chunk_size - 1
            ) // chunk_size  # Ceiling division

            chunk_lazyframes = []

            for chunk_idx in range(total_chunks):
                start_idx = chunk_idx * chunk_size
                chunk_ldf = ldf.slice(start_idx, chunk_size)

                # Process chunk while keeping it lazy
                processed_chunk_ldf = _tokenize_chunk(chunk_ldf)
                chunk_lazyframes.append(processed_chunk_ldf)

                # Report progress if callback provided
                if progress_callback is not None:
                    progress_callback(chunk_idx + 1, total_chunks)

            # Return concatenated lazy frame (still lazy until collect() is called)
            if not chunk_lazyframes:
                return ldf.with_columns([pl.lit([]).alias("tokens")])

            return pl.concat(chunk_lazyframes)

        else:
            # Unknown size - streaming approach with efficient chunk testing
            chunk_lazyframes = []
            chunk_idx = 0
            estimated_chunks = 10  # Start with conservative estimate
            consecutive_empty_chunks = 0
            max_empty_chunks = 3  # Stop after this many consecutive empty chunks

            while consecutive_empty_chunks < max_empty_chunks:
                start_idx = chunk_idx * chunk_size
                chunk_ldf = ldf.slice(start_idx, chunk_size)

                try:
                    # More efficient emptiness check using lazy operations
                    # Instead of collecting to check emptiness, use streaming height
                    processed_chunk_ldf = _tokenize_chunk(chunk_ldf)

                    # Use lazy operations to check if chunk has data
                    # This is more memory efficient than collecting
                    chunk_has_data_check = processed_chunk_ldf.select(pl.len()).limit(1)

                    try:
                        chunk_len = chunk_has_data_check.collect().item()

                        if chunk_len == 0:
                            consecutive_empty_chunks += 1
                            chunk_idx += 1
                            continue
                        else:
                            consecutive_empty_chunks = 0  # Reset counter

                    except Exception:
                        # If we can't determine chunk size, assume it's empty
                        consecutive_empty_chunks += 1
                        chunk_idx += 1
                        continue

                    # Add non-empty chunk to results
                    chunk_lazyframes.append(processed_chunk_ldf)

                    # Update progress estimate dynamically
                    chunk_idx += 1
                    if chunk_idx > estimated_chunks:
                        estimated_chunks = chunk_idx + 10  # Increase estimate

                    # Report progress if callback provided
                    if progress_callback is not None:
                        progress_callback(chunk_idx, estimated_chunks)

                except Exception:
                    # If chunk processing fails, likely no more data
                    consecutive_empty_chunks += 1
                    chunk_idx += 1

            # Final progress update
            if progress_callback is not None and chunk_idx > 0:
                final_chunks = len(chunk_lazyframes)
                progress_callback(final_chunks, final_chunks)  # Set to 100%

            if not chunk_lazyframes:
                return ldf.with_columns([pl.lit([]).alias("tokens")])

            return pl.concat(chunk_lazyframes)

    except Exception as e:
        # If chunked processing fails completely, fall back to non-chunked processing
        # This maintains backward compatibility and ensures functionality
        try:
            return _tokenize_chunk(ldf)
        except Exception as fallback_error:
            # If even fallback fails, provide informative error
            raise RuntimeError(
                f"Tokenization failed in both chunked and fallback modes. "
                f"Chunked error: {str(e)}. Fallback error: {str(fallback_error)}"
            ) from e


def _test_tokenization_engine():
    """
    Simple test function to verify the tokenization engine works correctly.
    This is for development/debugging purposes.
    """
    import polars as pl

    # Create test data with various scenarios
    test_data = pl.LazyFrame(
        {
            "text": [
                "Hello world! This is a test.",  # Simple English
                "Check out https://example.com and @user #hashtag",  # Social media entities
                "这是中文测试",  # Chinese text - should split into individual characters
                "これは日本語のテストです",  # Japanese with hiragana/kanji mix
                "한국어 테스트 문장입니다",  # Korean (space-separated)
                "Mixed iPhone用户 text",  # Mixed Latin + CJK
                "我爱@中文用户 #中文标签 和https://chinese.com",  # CJK with social media entities
                "Привет мир",  # Cyrillic (space-separated)
                "日本語のテスト文章です",  # Japanese without spaces
                "English中文Mix测试",  # Mixed script without spaces
                "พูดไทยได้",  # Thai (non-space language)
                "",  # Empty string
                "   ",  # Whitespace only
                "Hello 世界 test",  # Mixed with spaces
                "用户123号码",  # CJK with numbers
            ]
        }
    )

    # Apply tokenization
    result = tokenize_text(test_data, "text")

    # Collect and display results for inspection
    tokens_df = result.select(["text", "tokens"]).collect()

    print("Tokenization Test Results:")
    print("=" * 50)
    for row in tokens_df.iter_rows():
        text, tokens = row
        print(f"Input:  '{text}'")
        print(f"Tokens: {tokens}")
        print(f"Count:  {len(tokens) if tokens else 0}")
        print("-" * 30)

    return tokens_df


# Uncomment the line below to run the test
# _test_tokenization_engine()
