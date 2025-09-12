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
        eliminating the need for segmentation and reassembly.

        Args:
            config: TokenizerConfig specifying which token types to include

        Returns:
            Compiled regex pattern that matches all desired token types in priority order
        """
        pattern_parts = []

        # Add patterns in priority order (most specific first)
        if config.extract_urls:
            pattern_parts.append(self.get_pattern("url").pattern)

        if config.extract_emails:
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

    def list_patterns(self) -> List[str]:
        """Get list of available pattern names."""
        return list(self._patterns.keys())

    def _compile_patterns(self):
        """Compile all regex patterns with fallback support."""

        # URL patterns (comprehensive)
        url_pattern = (
            r"(?:"
            r"https?://\S+|"  # http/https URLs
            r"www\.\S+|"  # www URLs
            r"\S+\.\w{2,}(?:/\S*)?"  # domain.ext patterns
            r")"
        )

        # Email patterns
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

        # Social media mentions and hashtags
        mention_pattern = r"@[A-Za-z0-9_]+"
        hashtag_pattern = r"#[A-Za-z0-9_]+"

        # Numeric patterns (including decimals, percentages, etc.)
        numeric_pattern = (
            r"(?:"
            r"\d+\.?\d*%?|"  # Basic numbers with optional percentage
            r"\$\d+\.?\d*|"  # Money amounts
            r"\d+[.,]\d+|"  # Numbers with comma/period separators
            r"\d+(?:st|nd|rd|th)?"  # Ordinals
            r")"
        )

        # Emoji pattern (basic Unicode ranges)
        emoji_pattern = (
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
        cjk_pattern = (
            r"(?:"
            r"[\u4e00-\u9fff]|"  # CJK Unified Ideographs
            r"[\u3400-\u4dbf]|"  # CJK Extension A
            r"[\u3040-\u309f]|"  # Hiragana
            r"[\u30a0-\u30ff]|"  # Katakana
            r"[\uac00-\ud7af]"  # Hangul Syllables
            r")"
        )

        # Arabic script pattern
        arabic_pattern = (
            r"(?:"
            r"[\u0600-\u06ff]|"  # Arabic
            r"[\u0750-\u077f]|"  # Arabic Supplement
            r"[\u08a0-\u08ff]"  # Arabic Extended-A
            r")"
        )

        # Thai script pattern
        thai_pattern = r"[\u0e00-\u0e7f]+"  # Thai script range

        # Other Southeast Asian scripts (common in social media)
        sea_pattern = (
            r"(?:"
            r"[\u1780-\u17ff]|"  # Khmer
            r"[\u1000-\u109f]|"  # Myanmar
            r"[\u1a00-\u1a1f]|"  # Buginese
            r"[\u1b00-\u1b7f]"  # Balinese
            r")"
        )

        # Word patterns for different script types
        latin_word_pattern = r"[a-zA-Z]+(?:\'[a-zA-Z]+)*"  # Handle contractions
        word_pattern = f"(?:{latin_word_pattern}|{cjk_pattern}+|{arabic_pattern}+|{thai_pattern}|{sea_pattern}+)"

        # Punctuation (preserve some, group others)
        punctuation_pattern = r'[.!?;:,\-\(\)\[\]{}"\']'

        # Main social media tokenization pattern
        social_media_pattern = (
            f"(?:"
            f"{url_pattern}|"
            f"{email_pattern}|"
            f"{mention_pattern}|"
            f"{hashtag_pattern}|"
            f"{emoji_pattern}|"
            f"{numeric_pattern}|"
            f"{word_pattern}|"
            f"{punctuation_pattern}"
            f")"
        )

        # Word boundary pattern for space-separated languages
        word_boundary_pattern = r"\S+"

        # Combined social media entity pattern with named groups for single-pass detection
        combined_social_entities_pattern = (
            f"(?P<url>{url_pattern})|"
            f"(?P<email>{email_pattern})|"
            f"(?P<mention>{mention_pattern})|"
            f"(?P<hashtag>{hashtag_pattern})"
        )

        # Compile patterns with fallback handling
        patterns_to_compile = {
            "url": url_pattern,
            "email": email_pattern,
            "mention": mention_pattern,
            "hashtag": hashtag_pattern,
            "emoji": emoji_pattern,
            "numeric": numeric_pattern,
            "word": word_pattern,
            "latin_word": latin_word_pattern,
            "cjk_chars": cjk_pattern,
            "arabic_chars": arabic_pattern,
            "punctuation": punctuation_pattern,
            "social_media": social_media_pattern,
            "word_boundary": word_boundary_pattern,
            "combined_social_entities": combined_social_entities_pattern,
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
