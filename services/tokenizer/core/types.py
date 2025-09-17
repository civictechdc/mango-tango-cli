"""
TokenizerConfig, enums, and shared types

This module contains configuration models, enumerations,
and shared type definitions used across the tokenizer service.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class LanguageFamily(str, Enum):
    """Language families that affect tokenization strategies."""

    LATIN = "latin"  # Space-separated languages (English, French, etc.)
    CJK = "cjk"  # Chinese, Japanese, Korean
    ARABIC = "arabic"  # Arabic script languages
    MIXED = "mixed"  # Mixed content requiring multiple strategies
    UNKNOWN = "unknown"  # Language detection failed or not performed


class TokenType(str, Enum):
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


class TokenizerConfig(BaseModel):
    """Configuration for tokenizer behavior.

    Controls all aspects of text tokenization including script handling,
    social media entity processing, and output formatting.

    Social Media Entity Behavior:
    - extract_hashtags/extract_mentions: When False, splits into component words
    - include_urls/include_emails: When False, completely excludes (no fragmentation)
    """

    # Language detection settings
    fallback_language_family: LanguageFamily = LanguageFamily.MIXED
    """Default language family when detection fails or mixed content is found."""

    # Token type filtering
    include_punctuation: bool = False
    """Whether to include punctuation marks as separate tokens."""

    include_numeric: bool = True
    """Whether to include numeric tokens (integers, decimals, etc.)."""

    include_emoji: bool = False
    """Whether to include emoji characters as tokens."""

    # Text preprocessing
    case_handling: CaseHandling = CaseHandling.LOWERCASE
    """How to handle character case during tokenization."""

    normalize_unicode: bool = True
    """Whether to apply Unicode NFKC normalization for consistent character representation."""

    # Social media features
    extract_hashtags: bool = True
    """Whether to preserve hashtags as single tokens. If False, splits into component words."""

    extract_mentions: bool = True
    """Whether to preserve @mentions as single tokens. If False, splits into component words."""

    include_urls: bool = True
    """Whether to include URLs as tokens. If False, URLs are completely excluded (not fragmented)."""

    include_emails: bool = True
    """Whether to include email addresses as tokens. If False, emails are completely excluded (not fragmented)."""

    # Output formatting
    min_token_length: int = 1
    """Minimum length for tokens to be included in output."""

    max_token_length: Optional[int] = None
    """Maximum length for tokens. If None, no length limit is applied."""

    strip_whitespace: bool = True
    """Whether to strip leading/trailing whitespace from tokens."""


# Type aliases for common use cases
TokenList = list[str]
