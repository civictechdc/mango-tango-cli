"""
Language detection utilities for text tokenization.

This module provides Unicode script-based language detection to determine
appropriate tokenization strategies for different writing systems.
"""

import re
import unicodedata
from typing import Union

import polars as pl

from ..core.types import LanguageFamily


def detect_language_family(text: str) -> LanguageFamily:
    """
    Detect the language family of input text based on Unicode scripts.

    Analyzes the Unicode script composition of text to determine the
    appropriate tokenization strategy. Handles mixed-script content
    commonly found in social media.

    Args:
        text: Input text to analyze

    Returns:
        Detected language family (LATIN, CJK, ARABIC, MIXED, or UNKNOWN)
    """
    if not text or not text.strip():
        return LanguageFamily.UNKNOWN

    # Remove URLs, mentions, hashtags for cleaner script analysis
    clean_text = _clean_text_for_analysis(text)
    if not clean_text:
        return LanguageFamily.UNKNOWN

    # Count characters by script category
    script_counts = {
        "latin": 0,
        "cjk": 0,
        "arabic": 0,
        "other": 0,
    }

    for char in clean_text:
        if char.isspace() or not char.isprintable():
            continue

        script_name = unicodedata.name(char, "").split()[0] if unicodedata.name(char, "") else ""

        if _is_latin_script(char, script_name):
            script_counts["latin"] += 1
        elif _is_cjk_script(char, script_name):
            script_counts["cjk"] += 1
        elif _is_arabic_script(char, script_name):
            script_counts["arabic"] += 1
        else:
            script_counts["other"] += 1

    total_chars = sum(script_counts.values())
    if total_chars == 0:
        return LanguageFamily.UNKNOWN

    # Calculate script percentages
    latin_pct = script_counts["latin"] / total_chars
    cjk_pct = script_counts["cjk"] / total_chars
    arabic_pct = script_counts["arabic"] / total_chars

    # Thresholds for script detection
    PRIMARY_THRESHOLD = 0.8  # Dominant script threshold (increased for cleaner detection)
    MIXED_THRESHOLD = 0.15   # Minimum secondary script for mixed classification
    
    # Check for mixed content first (more sensitive to mixed usage patterns)
    if (
        (latin_pct >= MIXED_THRESHOLD and cjk_pct >= MIXED_THRESHOLD)
        or (latin_pct >= MIXED_THRESHOLD and arabic_pct >= MIXED_THRESHOLD)
        or (cjk_pct >= MIXED_THRESHOLD and arabic_pct >= MIXED_THRESHOLD)
    ):
        return LanguageFamily.MIXED

    # Then check for dominant scripts
    if latin_pct >= PRIMARY_THRESHOLD:
        return LanguageFamily.LATIN
    elif cjk_pct >= PRIMARY_THRESHOLD:
        return LanguageFamily.CJK
    elif arabic_pct >= PRIMARY_THRESHOLD:
        return LanguageFamily.ARABIC
    else:
        # Default to most common script if no clear pattern
        if latin_pct >= cjk_pct and latin_pct >= arabic_pct:
            return LanguageFamily.LATIN
        elif cjk_pct >= arabic_pct:
            return LanguageFamily.CJK
        else:
            return LanguageFamily.ARABIC


def is_space_separated(text: Union[str, pl.Expr]) -> Union[bool, pl.Expr]:
    """
    Determine if text uses space-separated tokens.

    Supports both string and polars expression inputs for flexible usage
    in data processing pipelines.

    Args:
        text: Input text or polars expression to analyze

    Returns:
        Boolean or polars expression indicating space separation
    """
    if isinstance(text, pl.Expr):
        # Return polars expression for use in dataframe operations
        return text.map_elements(
            lambda x: _is_space_separated_string(x) if x else False,
            return_dtype=pl.Boolean,
        )
    else:
        return _is_space_separated_string(text)


def _is_space_separated_string(text: str) -> bool:
    """Helper function for string-based space separation detection."""
    if not text:
        return False

    family = detect_language_family(text)
    return family in (LanguageFamily.LATIN, LanguageFamily.ARABIC)


def _clean_text_for_analysis(text: str) -> str:
    """
    Clean text for language detection by removing social media entities.

    Removes URLs, mentions, hashtags, and other non-linguistic content
    that could interfere with script detection, but preserves the actual
    linguistic content for accurate script analysis.
    """
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    # Remove mentions and hashtags (but keep the content after # and @)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'#\w+', '', text)
    
    # Remove excessive whitespace but preserve the actual text
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def _is_latin_script(char: str, script_name: str) -> bool:
    """Check if character belongs to Latin script family."""
    # Basic Latin and Latin Extended blocks
    code_point = ord(char)
    return (
        (0x0041 <= code_point <= 0x007A)  # Basic Latin letters
        or (0x00C0 <= code_point <= 0x024F)  # Latin Extended
        or (0x1E00 <= code_point <= 0x1EFF)  # Latin Extended Additional
        or script_name.startswith("LATIN")
    )


def _is_cjk_script(char: str, script_name: str) -> bool:
    """Check if character belongs to CJK (Chinese, Japanese, Korean) scripts."""
    code_point = ord(char)
    return (
        (0x4E00 <= code_point <= 0x9FFF)  # CJK Unified Ideographs
        or (0x3400 <= code_point <= 0x4DBF)  # CJK Extension A
        or (0x20000 <= code_point <= 0x2A6DF)  # CJK Extension B
        or (0x3040 <= code_point <= 0x309F)  # Hiragana
        or (0x30A0 <= code_point <= 0x30FF)  # Katakana
        or (0xAC00 <= code_point <= 0xD7AF)  # Hangul Syllables
        or script_name.startswith(("CJK", "HIRAGANA", "KATAKANA", "HANGUL"))
    )


def _is_arabic_script(char: str, script_name: str) -> bool:
    """Check if character belongs to Arabic script family."""
    code_point = ord(char)
    return (
        (0x0600 <= code_point <= 0x06FF)  # Arabic
        or (0x0750 <= code_point <= 0x077F)  # Arabic Supplement
        or (0x08A0 <= code_point <= 0x08FF)  # Arabic Extended-A
        or (0xFB50 <= code_point <= 0xFDFF)  # Arabic Presentation Forms-A
        or (0xFE70 <= code_point <= 0xFEFF)  # Arabic Presentation Forms-B
        or script_name.startswith("ARABIC")
    )