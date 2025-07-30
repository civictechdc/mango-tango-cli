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

# Memory Management Infrastructure

import psutil
import gc
import logging
import time
from typing import Dict, Optional, Callable
from enum import Enum


class MemoryPressureLevel(Enum):
    LOW = "low"           # < 60% of limit
    MEDIUM = "medium"     # 60-75% of limit  
    HIGH = "high"         # 75-85% of limit
    CRITICAL = "critical" # > 85% of limit


class MemoryManager:
    """
    Real-time memory monitoring and adaptive processing control.
    
    Provides memory usage tracking, adaptive chunk sizing, early warning system,
    and automatic garbage collection triggering for memory pressure scenarios.
    """
    
    def __init__(self, max_memory_gb: float = 4.0, process_name: str = "ngram_analyzer"):
        self.max_memory_bytes = max_memory_gb * 1024**3
        self.process_name = process_name
        self.process = psutil.Process()
        
        # Memory pressure thresholds
        self.thresholds = {
            MemoryPressureLevel.MEDIUM: 0.60,
            MemoryPressureLevel.HIGH: 0.75, 
            MemoryPressureLevel.CRITICAL: 0.85
        }
        
        # Adaptive chunk size factors
        self.chunk_size_factors = {
            MemoryPressureLevel.LOW: 1.0,
            MemoryPressureLevel.MEDIUM: 0.7,
            MemoryPressureLevel.HIGH: 0.4,
            MemoryPressureLevel.CRITICAL: 0.2
        }
        
        # Memory usage history for trend analysis
        self.memory_history = []
        self.max_history_size = 100
        
        self.logger = logging.getLogger(f"{process_name}_memory")
    
    def get_current_memory_usage(self) -> Dict:
        """Get comprehensive current memory statistics."""
        memory_info = self.process.memory_info()
        system_memory = psutil.virtual_memory()
        
        current_rss = memory_info.rss
        current_vms = memory_info.vms
        
        usage_stats = {
            'rss_bytes': current_rss,
            'vms_bytes': current_vms,
            'rss_mb': current_rss / 1024**2,
            'vms_mb': current_vms / 1024**2,
            'rss_gb': current_rss / 1024**3,
            'system_available_gb': system_memory.available / 1024**3,
            'system_used_percent': system_memory.percent,
            'process_memory_percent': (current_rss / self.max_memory_bytes) * 100,
            'pressure_level': self.get_memory_pressure_level().value
        }
        
        # Add to history for trend analysis
        self.memory_history.append({
            'timestamp': time.time(),
            'rss_bytes': current_rss,
            'pressure_level': usage_stats['pressure_level']
        })
        
        # Maintain history size
        if len(self.memory_history) > self.max_history_size:
            self.memory_history.pop(0)
            
        return usage_stats
    
    def get_memory_pressure_level(self) -> MemoryPressureLevel:
        """Determine current memory pressure level."""
        current_usage = self.process.memory_info().rss
        usage_ratio = current_usage / self.max_memory_bytes
        
        if usage_ratio >= self.thresholds[MemoryPressureLevel.CRITICAL]:
            return MemoryPressureLevel.CRITICAL
        elif usage_ratio >= self.thresholds[MemoryPressureLevel.HIGH]:
            return MemoryPressureLevel.HIGH
        elif usage_ratio >= self.thresholds[MemoryPressureLevel.MEDIUM]:
            return MemoryPressureLevel.MEDIUM
        else:
            return MemoryPressureLevel.LOW
    
    def calculate_adaptive_chunk_size(self, base_chunk_size: int, operation_type: str) -> int:
        """Calculate optimal chunk size based on current memory pressure."""
        pressure_level = self.get_memory_pressure_level()
        adjustment_factor = self.chunk_size_factors[pressure_level]
        
        # Operation-specific base adjustments
        operation_factors = {
            "tokenization": 1.0,
            "ngram_generation": 0.6,  # More memory intensive
            "unique_extraction": 1.2,
            "join_operations": 0.8
        }
        
        operation_factor = operation_factors.get(operation_type, 1.0)
        adjusted_size = int(base_chunk_size * adjustment_factor * operation_factor)
        
        # Ensure minimum viable chunk size
        min_chunk_size = max(1000, base_chunk_size // 10)
        return max(adjusted_size, min_chunk_size)
    
    def should_trigger_gc(self, force_threshold: float = 0.7) -> bool:
        """Determine if garbage collection should be triggered."""
        current_usage = self.process.memory_info().rss
        usage_ratio = current_usage / self.max_memory_bytes
        
        return usage_ratio >= force_threshold
    
    def enhanced_gc_cleanup(self) -> Dict:
        """Perform comprehensive garbage collection with metrics."""
        memory_before = self.get_current_memory_usage()
        
        # Multiple GC passes for thorough cleanup
        for i in range(3):
            collected = gc.collect()
            if collected == 0:
                break
        
        memory_after = self.get_current_memory_usage()
        
        cleanup_stats = {
            'memory_freed_mb': (memory_before['rss_mb'] - memory_after['rss_mb']),
            'memory_before_mb': memory_before['rss_mb'],
            'memory_after_mb': memory_after['rss_mb'],
            'pressure_before': memory_before['pressure_level'],
            'pressure_after': memory_after['pressure_level']
        }
        
        self.logger.info(f"GC cleanup freed {cleanup_stats['memory_freed_mb']:.1f}MB")
        return cleanup_stats
    
    def get_memory_trend(self) -> str:
        """Analyze recent memory usage trend."""
        if len(self.memory_history) < 5:
            return "insufficient_data"
            
        recent_usage = [entry['rss_bytes'] for entry in self.memory_history[-5:]]
        
        if all(recent_usage[i] <= recent_usage[i+1] for i in range(len(recent_usage)-1)):
            return "increasing"
        elif all(recent_usage[i] >= recent_usage[i+1] for i in range(len(recent_usage)-1)):
            return "decreasing"
        else:
            return "stable"


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
    memory_manager: Optional[MemoryManager] = None,
) -> pl.LazyFrame:
    """
    Memory-efficient tokenization engine with adaptive memory management.

    Enhanced features:
    - Real-time memory monitoring during processing
    - Dynamic chunk size adjustment based on memory pressure
    - Mid-process memory monitoring and adaptation
    - Graceful fallback to smaller chunks when memory pressure increases
    - Progress reporting with memory statistics

    Args:
        ldf: Input LazyFrame containing text data
        text_column: Name of the column containing text to tokenize
        progress_callback: Optional callback function for progress reporting.
                         Called with (current_chunk, total_chunks) between chunks.
        memory_manager: Optional MemoryManager for adaptive processing

    Returns:
        LazyFrame with additional 'tokens' column containing list of tokens

    Raises:
        ValueError: If text_column does not exist in the LazyFrame
        TypeError: If input is not a polars LazyFrame
        MemoryError: If processing fails even with minimum chunk sizes
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

    # Create memory manager if not provided
    if memory_manager is None:
        memory_manager = MemoryManager(max_memory_gb=4.0, process_name="tokenizer")

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
            r"[Hh][Tt][Tt][Pp][Ss]?://[a-zA-Z0-9._~:/?#@!$&'()*+,;=\-]+",  # URLs (case insensitive HTTP/HTTPS)
            r"@\w+",  # @mentions
            r"#\w+",  # #hashtags
            r"[a-zA-Z\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]{2,}[\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF]+",  # Mixed Latin+CJK (Latin part 2+ chars)
            r"[\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF]+[a-zA-Z\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]+[\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF]+",  # CJK-Latin-CJK (requires Latin chars)
            r"[\uAC00-\uD7AF]+",  # Korean words (Hangul)
            r"[\u0400-\u04FF\u0500-\u052F]+",  # Cyrillic words
            r"[a-zA-Z\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF][a-zA-Z0-9\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF.!?,;:()'\"\\-]*",  # Latin words with accented chars and punctuation
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
                                    r"[Hh][Tt][Tt][Pp][Ss]?://[a-zA-Z0-9._~:/?#@!$&'()*+,;=\-]+",  # URLs
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
                    initial_chunk_size = memory_manager.calculate_adaptive_chunk_size(50000, "tokenization")
                    sample_size = min(1000, initial_chunk_size // 10)
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

    # Calculate initial adaptive chunk size based on memory pressure
    initial_chunk_size = 50000
    adaptive_chunk_size = memory_manager.calculate_adaptive_chunk_size(initial_chunk_size, "tokenization")

    # If dataset is small, check if we should process without chunking
    if total_rows is not None and total_rows <= adaptive_chunk_size:
        # Small dataset - process normally with memory monitoring
        memory_before = memory_manager.get_current_memory_usage()
        result = _tokenize_chunk(ldf)
        memory_after = memory_manager.get_current_memory_usage()

        # Log memory usage for small datasets
        memory_used = memory_after['rss_mb'] - memory_before['rss_mb']
        if memory_used > 100:  # Log if significant memory usage
            logging.info(f"Tokenization used {memory_used:.1f}MB for {total_rows} rows")

        return result

    # For large datasets or unknown sizes, use memory-adaptive chunked processing
    try:
        if total_rows is not None:
            # Known size approach - adaptive chunking with memory monitoring
            chunk_lazyframes = []
            current_chunk_size = adaptive_chunk_size
            processed_rows = 0

            while processed_rows < total_rows:
                # Check memory pressure and adjust chunk size if needed
                pressure_level = memory_manager.get_memory_pressure_level()

                if pressure_level == MemoryPressureLevel.CRITICAL:
                    # Reduce chunk size dramatically for critical pressure
                    current_chunk_size = max(1000, current_chunk_size // 4)
                elif pressure_level == MemoryPressureLevel.HIGH:
                    # Reduce chunk size moderately for high pressure
                    current_chunk_size = max(5000, current_chunk_size // 2)

                # Calculate actual chunk size for this iteration
                remaining_rows = total_rows - processed_rows
                actual_chunk_size = min(current_chunk_size, remaining_rows)

                # Process chunk with memory monitoring
                chunk_ldf = ldf.slice(processed_rows, actual_chunk_size)

                try:
                    processed_chunk_ldf = _tokenize_chunk(chunk_ldf)
                    chunk_lazyframes.append(processed_chunk_ldf)

                    processed_rows += actual_chunk_size

                    # Report progress with memory stats if callback provided
                    if progress_callback:
                        chunk_num = len(chunk_lazyframes)
                        estimated_total_chunks = (total_rows + current_chunk_size - 1) // current_chunk_size

                        callback_result = progress_callback(chunk_num, estimated_total_chunks)

                        # Handle callback suggestions for chunk size adjustment
                        if isinstance(callback_result, dict) and callback_result.get("reduce_chunk_size"):
                            suggested_size = callback_result.get("new_size", current_chunk_size // 2)
                            current_chunk_size = max(1000, suggested_size)

                    # Force garbage collection after each chunk in high memory pressure
                    if pressure_level in [MemoryPressureLevel.HIGH, MemoryPressureLevel.CRITICAL]:
                        cleanup_stats = memory_manager.enhanced_gc_cleanup()
                        if cleanup_stats['memory_freed_mb'] > 20:
                            logging.info(f"Freed {cleanup_stats['memory_freed_mb']:.1f}MB after tokenization chunk")

                except MemoryError as e:
                    # Emergency fallback - reduce chunk size dramatically and retry
                    if current_chunk_size > 1000:
                        current_chunk_size = max(500, current_chunk_size // 8)
                        logging.warning(f"Memory error in tokenization - reducing chunk size to {current_chunk_size}")
                        continue
                    else:
                        # Even minimum chunk size failed - this is a critical error
                        raise MemoryError(f"Cannot process even minimal chunks during tokenization: {e}") from e

            # Return concatenated results
            if not chunk_lazyframes:
                return ldf.with_columns([pl.lit([]).alias("tokens")])

            return pl.concat(chunk_lazyframes)

        else:
            # Unknown size - streaming approach with memory-aware chunk sizing
            chunk_lazyframes = []
            chunk_idx = 0
            estimated_chunks = 10  # Start with conservative estimate
            consecutive_empty_chunks = 0
            max_empty_chunks = 3  # Stop after this many consecutive empty chunks
            current_chunk_size = adaptive_chunk_size

            while consecutive_empty_chunks < max_empty_chunks:
                # Check memory pressure and adjust chunk size
                pressure_level = memory_manager.get_memory_pressure_level()

                if pressure_level == MemoryPressureLevel.CRITICAL:
                    current_chunk_size = max(1000, current_chunk_size // 4)
                elif pressure_level == MemoryPressureLevel.HIGH:
                    current_chunk_size = max(5000, current_chunk_size // 2)

                start_idx = chunk_idx * current_chunk_size
                chunk_ldf = ldf.slice(start_idx, current_chunk_size)

                try:
                    # More efficient emptiness check using lazy operations
                    processed_chunk_ldf = _tokenize_chunk(chunk_ldf)

                    # Use lazy operations to check if chunk has data
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
                    if progress_callback:
                        callback_result = progress_callback(chunk_idx, estimated_chunks)

                        # Handle callback suggestions for chunk size adjustment
                        if isinstance(callback_result, dict) and callback_result.get("reduce_chunk_size"):
                            suggested_size = callback_result.get("new_size", current_chunk_size // 2)
                            current_chunk_size = max(1000, suggested_size)

                    # Force garbage collection in high memory pressure
                    if pressure_level in [MemoryPressureLevel.HIGH, MemoryPressureLevel.CRITICAL]:
                        cleanup_stats = memory_manager.enhanced_gc_cleanup()
                        if cleanup_stats['memory_freed_mb'] > 20:
                            logging.info(f"Freed {cleanup_stats['memory_freed_mb']:.1f}MB after streaming tokenization chunk")

                except MemoryError as e:
                    # Emergency fallback - reduce chunk size dramatically and retry
                    if current_chunk_size > 1000:
                        current_chunk_size = max(500, current_chunk_size // 8)
                        logging.warning(f"Memory error in streaming tokenization - reducing chunk size to {current_chunk_size}")
                        continue
                    else:
                        # Even minimum chunk size failed - critical error
                        raise MemoryError(f"Cannot process even minimal chunks during streaming tokenization: {e}") from e

                except Exception:
                    # If chunk processing fails, likely no more data
                    consecutive_empty_chunks += 1
                    chunk_idx += 1

            # Final progress update
            if progress_callback and chunk_idx > 0:
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
