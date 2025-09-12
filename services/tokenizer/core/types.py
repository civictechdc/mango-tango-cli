"""
TokenizerConfig, enums, and shared types

This module contains configuration dataclasses, enumerations,
and shared type definitions used across the tokenizer service.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class LanguageFamily(Enum):
    """Language families that affect tokenization strategies."""

    LATIN = "latin"  # Space-separated languages (English, French, etc.)
    CJK = "cjk"  # Chinese, Japanese, Korean
    ARABIC = "arabic"  # Arabic script languages
    MIXED = "mixed"  # Mixed content requiring multiple strategies
    UNKNOWN = "unknown"  # Language detection failed or not performed


class TokenType(Enum):
    """Types of tokens that can be extracted."""

    WORD = "word"  # Regular words
    PUNCTUATION = "punctuation"  # Punctuation marks
    NUMERIC = "numeric"  # Numbers
    EMOJI = "emoji"  # Emoji characters
    HASHTAG = "hashtag"  # Social media hashtags
    MENTION = "mention"  # Social media mentions
    URL = "url"  # URLs and links
    EMAIL = "email"  # Email addresses
    WHITESPACE = "whitespace"  # Whitespace (when preserved)


class CaseHandling(Enum):
    """How to handle character case during tokenization."""

    PRESERVE = "preserve"  # Keep original case
    LOWERCASE = "lowercase"  # Convert to lowercase
    UPPERCASE = "uppercase"  # Convert to uppercase
    NORMALIZE = "normalize"  # Smart case normalization


@dataclass
class TokenizerConfig:
    """Configuration for tokenizer behavior."""

    # Language detection settings
    fallback_language_family: LanguageFamily = LanguageFamily.MIXED

    # Token type filtering
    include_punctuation: bool = False
    include_numeric: bool = True
    include_emoji: bool = False

    # Text preprocessing
    case_handling: CaseHandling = CaseHandling.LOWERCASE
    normalize_unicode: bool = True

    # Social media features
    extract_hashtags: bool = True
    extract_mentions: bool = True
    extract_urls: bool = True
    extract_emails: bool = True

    # Output formatting
    min_token_length: int = 1
    max_token_length: Optional[int] = None
    strip_whitespace: bool = True


# Type aliases for common use cases
TokenList = list[str]
