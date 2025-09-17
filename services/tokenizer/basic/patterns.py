"""
Regex patterns for text tokenization.

This module contains compiled regular expressions for extracting different
types of tokens from social media text, with fallback support for both
regex and re modules.
"""

import re
from typing import Any, Dict, List

# Try to use the more powerful regex module, fall back to re
try:
    import regex

    REGEX_MODULE = regex
    REGEX_AVAILABLE = True
except ImportError:
    REGEX_MODULE = re
    REGEX_AVAILABLE = False


# Pattern constants
# URL patterns (comprehensive)
URL_PATTERN = (
    r"(?:"
    r"https?://\S+|"  # http/https URLs
    r"www\.\S+|"  # www URLs
    r"[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}(?:/\S*)?"  # domain.ext patterns
    r")"
)

# Email patterns
EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

# Social media mentions and hashtags
MENTION_PATTERN = r"@[A-Za-z0-9_]+"
HASHTAG_PATTERN = r"#[A-Za-z0-9_]+"

# Numeric patterns (including decimals, percentages, etc.)
NUMERIC_PATTERN = (
    r"(?:"
    r"\d+\.?\d*%?|"  # Basic numbers with optional percentage
    r"[$€£¥₹₽¥¢]\d+\.?\d*|"  # Money amounts with common currency symbols
    r"\d+[.,]\d+|"  # Numbers with comma/period separators
    r"\d+(?:st|nd|rd|th)?"  # Ordinals
    r")"
)

# Emoji pattern (basic Unicode ranges)
EMOJI_PATTERN = (
    r"(?:"
    r"[\U0001F600-\U0001F64F]|"  # Emoticons
    r"[\U0001F300-\U0001F5FF]|"  # Misc Symbols
    r"[\U0001F680-\U0001F6FF]|"  # Transport
    r"[\U0001F1E0-\U0001F1FF]|"  # Flags
    r"[\U00002700-\U000027BF]|"  # Dingbats
    r"[\U0001F900-\U0001F9FF]|"  # Supplemental Symbols
    r"[\U00002600-\U000026FF]"  # Misc symbols
    r")"
)

# CJK character pattern
CJK_PATTERN = (
    r"(?:"
    r"[\u4e00-\u9fff]|"  # CJK Unified Ideographs
    r"[\u3400-\u4dbf]|"  # CJK Extension A
    r"[\u3040-\u309f]|"  # Hiragana
    r"[\u30a0-\u30ff]|"  # Katakana
    r"[\uac00-\ud7af]"  # Hangul Syllables
    r")"
)

# Arabic script pattern
ARABIC_PATTERN = (
    r"(?:"
    r"[\u0600-\u06ff]|"  # Arabic
    r"[\u0750-\u077f]|"  # Arabic Supplement
    r"[\u08a0-\u08ff]"  # Arabic Extended-A
    r")"
)

# Thai script pattern
THAI_PATTERN = (
    r"(?:"
    r"[\u0e00-\u0e7f]"  # Thai script range
    r")"
)

# Other Southeast Asian scripts (common in social media)
SEA_PATTERN = (
    r"(?:"
    r"[\u1780-\u17ff]|"  # Khmer
    r"[\u1000-\u109f]|"  # Myanmar
    r"[\u1a00-\u1a1f]|"  # Buginese
    r"[\u1b00-\u1b7f]"  # Balinese
    r")"
)

# Word patterns for different script types
LATIN_WORD_PATTERN = r"[a-zA-Z]+(?:\'[a-zA-Z]+)*"  # Handle contractions
WORD_PATTERN = f"(?:{LATIN_WORD_PATTERN}|{CJK_PATTERN}+|{ARABIC_PATTERN}+|{THAI_PATTERN}+|{SEA_PATTERN}+)"

# Punctuation (preserve some, group others)
PUNCTUATION_PATTERN = r'[.!?;:,\-\(\)\[\]{}"\']'

# Main social media tokenization pattern
SOCIAL_MEDIA_PATTERN = (
    f"(?:"
    f"{URL_PATTERN}|"
    f"{EMAIL_PATTERN}|"
    f"{MENTION_PATTERN}|"
    f"{HASHTAG_PATTERN}|"
    f"{EMOJI_PATTERN}|"
    f"{NUMERIC_PATTERN}|"
    f"{WORD_PATTERN}|"
    f"{PUNCTUATION_PATTERN}"
    f")"
)

# Word boundary pattern for space-separated languages
WORD_BOUNDARY_PATTERN = r"\S+"

# Combined social media entity pattern with named groups for single-pass detection
COMBINED_SOCIAL_ENTITIES_PATTERN = (
    f"(?P<url>{URL_PATTERN})|"
    f"(?P<email>{EMAIL_PATTERN})|"
    f"(?P<mention>{MENTION_PATTERN})|"
    f"(?P<hashtag>{HASHTAG_PATTERN})"
)


class TokenizerPatterns:
    """
    Compiled regex patterns for tokenization.

    Organizes patterns logically and provides efficient compiled regex objects
    for different token types found in social media text.
    """

    def __init__(self):
        """Initialize and compile all tokenization patterns."""
        self._patterns: Dict[str, Any] = {}
        self._compile_patterns()

    def get_pattern(self, pattern_name: str) -> Any:
        """
        Get compiled pattern by name.

        Args:
            pattern_name: Name of the pattern to retrieve

        Returns:
            Compiled regex pattern

        Raises:
            KeyError: If pattern name is not found
        """
        if pattern_name not in self._patterns:
            raise KeyError(f"Pattern '{pattern_name}' not found")
        return self._patterns[pattern_name]

    def get_comprehensive_pattern(self, config) -> Any:
        """
        Build comprehensive tokenization pattern based on configuration.

        This creates a single regex pattern that finds ALL tokens in document order,
        eliminating the need for segmentation and reassembly. URLs and emails are
        conditionally included in the regex itself based on configuration, avoiding
        the need for post-processing filtering.

        Args:
            config: TokenizerConfig specifying which token types to include

        Returns:
            Compiled regex pattern that matches all desired token types in priority order
        """
        pattern_parts = []

        # Conditionally add URL and email patterns based on configuration
        # This eliminates the need for post-processing filtering
        if config.include_urls:
            pattern_parts.append(self.get_pattern("url").pattern)

        if config.include_emails:
            pattern_parts.append(self.get_pattern("email").pattern)

        if config.extract_mentions:
            pattern_parts.append(self.get_pattern("mention").pattern)

        if config.extract_hashtags:
            pattern_parts.append(self.get_pattern("hashtag").pattern)

        if config.include_emoji:
            pattern_parts.append(self.get_pattern("emoji").pattern)

        if config.include_numeric:
            pattern_parts.append(self.get_pattern("numeric").pattern)

        # Always include word pattern (this is the core tokenization)
        pattern_parts.append(self.get_pattern("word").pattern)

        if config.include_punctuation:
            pattern_parts.append(self.get_pattern("punctuation").pattern)

        # Don't add the greedy fallback - let configuration control what gets captured

        # Combine patterns with alternation (| operator)
        comprehensive_pattern = "(?:" + "|".join(pattern_parts) + ")"

        try:
            return REGEX_MODULE.compile(comprehensive_pattern, REGEX_MODULE.IGNORECASE)
        except Exception:
            # Fallback to standard re module
            if REGEX_AVAILABLE and REGEX_MODULE is not re:
                try:
                    return re.compile(comprehensive_pattern, re.IGNORECASE)
                except Exception:
                    # Ultimate fallback - just match words
                    return re.compile(r"\S+", re.IGNORECASE)
            else:
                return re.compile(r"\S+", re.IGNORECASE)

    def get_exclusion_pattern(self, config) -> Any:
        """
        Build pattern to identify and skip excluded entities in text.

        This creates a pattern that matches URLs and emails that should be excluded,
        allowing the tokenizer to skip over them entirely instead of breaking them
        into component words.

        Args:
            config: TokenizerConfig specifying which token types to exclude

        Returns:
            Compiled regex pattern that matches excluded entities, or None if no exclusions
        """
        exclusion_parts = []

        if not config.include_urls:
            exclusion_parts.append(self.get_pattern("url").pattern)

        if not config.include_emails:
            exclusion_parts.append(self.get_pattern("email").pattern)

        if not config.include_numeric:
            exclusion_parts.append(self.get_pattern("numeric").pattern)

        if not exclusion_parts:
            return None

        # Combine exclusion patterns
        exclusion_pattern = "(?:" + "|".join(exclusion_parts) + ")"

        try:
            return REGEX_MODULE.compile(exclusion_pattern, REGEX_MODULE.IGNORECASE)
        except Exception:
            # Fallback to standard re module
            if REGEX_AVAILABLE and REGEX_MODULE is not re:
                try:
                    return re.compile(exclusion_pattern, re.IGNORECASE)
                except Exception:
                    return None
            else:
                return None

    def list_patterns(self) -> List[str]:
        """Get list of available pattern names."""
        return list(self._patterns.keys())

    def _compile_patterns(self):
        """Compile all regex patterns with fallback support."""

        # Compile patterns with fallback handling
        patterns_to_compile = {
            "url": URL_PATTERN,
            "email": EMAIL_PATTERN,
            "mention": MENTION_PATTERN,
            "hashtag": HASHTAG_PATTERN,
            "emoji": EMOJI_PATTERN,
            "numeric": NUMERIC_PATTERN,
            "word": WORD_PATTERN,
            "latin_word": LATIN_WORD_PATTERN,
            "cjk_chars": CJK_PATTERN,
            "arabic_chars": ARABIC_PATTERN,
            "punctuation": PUNCTUATION_PATTERN,
            "social_media": SOCIAL_MEDIA_PATTERN,
            "word_boundary": WORD_BOUNDARY_PATTERN,
            "combined_social_entities": COMBINED_SOCIAL_ENTITIES_PATTERN,
        }

        for name, pattern in patterns_to_compile.items():
            try:
                self._patterns[name] = REGEX_MODULE.compile(
                    pattern, REGEX_MODULE.IGNORECASE
                )
            except Exception:
                # If compilation fails with regex module, fall back to re
                if REGEX_AVAILABLE and REGEX_MODULE is not re:
                    try:
                        self._patterns[name] = re.compile(pattern, re.IGNORECASE)
                    except Exception:
                        # If both fail, create a simple fallback
                        self._patterns[name] = re.compile(r"\S+", re.IGNORECASE)
                else:
                    # Already using re module, create simple fallback
                    self._patterns[name] = re.compile(r"\S+", re.IGNORECASE)


# Global instance for easy access
_global_patterns = None


def get_patterns() -> TokenizerPatterns:
    """
    Get global TokenizerPatterns instance.

    Returns:
        Singleton TokenizerPatterns instance
    """
    global _global_patterns
    if _global_patterns is None:
        _global_patterns = TokenizerPatterns()
    return _global_patterns


# Pattern categories for easy access
SOCIAL_PATTERNS = ["url", "email", "mention", "hashtag"]
LINGUISTIC_PATTERNS = ["word", "latin_word", "cjk_chars", "arabic_chars"]
FORMATTING_PATTERNS = ["emoji", "numeric", "punctuation"]
