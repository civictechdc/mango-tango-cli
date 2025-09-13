"""
BasicTokenizer implementation.

This module contains the main BasicTokenizer class that implements
Unicode-aware tokenization for social media text with entity preservation.
"""

import re
from typing import Optional

from ..core.base import AbstractTokenizer
from ..core.types import LanguageFamily, TokenizerConfig, TokenList, TokenType
from .patterns import get_patterns


class BasicTokenizer(AbstractTokenizer):
    """
    Unicode-aware basic tokenizer for social media text.

    This tokenizer handles mixed-script content, preserves social media entities
    (@mentions, #hashtags, URLs), and applies appropriate tokenization strategies
    for different script families.
    """

    def __init__(self, config: Optional[TokenizerConfig] = None):
        """
        Initialize BasicTokenizer with configuration.

        Args:
            config: Tokenizer configuration. If None, default config will be used.
        """
        super().__init__(config)
        self._patterns = get_patterns()

    def tokenize(self, text: str) -> TokenList:
        """
        Tokenize input text into a list of tokens.

        Applies appropriate tokenization strategies for mixed-script content
        while preserving social media entities and handling Unicode correctly.

        Args:
            text: Input text to tokenize

        Returns:
            List of tokens extracted from the input text in document order
        """
        if not text:
            return []

        # Apply preprocessing
        processed_text = self._preprocess_text(text)
        if not processed_text:
            return []

        # Extract tokens using comprehensive regex pattern
        tokens = self._extract_tokens(processed_text)

        # Apply post-processing
        return self._postprocess_tokens(tokens)

    def _extract_tokens(self, text: str) -> TokenList:
        """
        Extract tokens using comprehensive regex patterns.
        Preserves the original order of tokens as they appear in the input text.

        Args:
            text: Preprocessed text to tokenize

        Returns:
            List of extracted tokens in their original order
        """
        return self._extract_tokens_ordered(text, LanguageFamily.MIXED)

    def _is_char_level_script(self, char: str) -> bool:
        """Check if character belongs to a script that uses character-level tokenization (scriptio continua)."""
        code_point = ord(char)
        return (
            (0x4E00 <= code_point <= 0x9FFF)  # CJK Unified Ideographs
            or (0x3400 <= code_point <= 0x4DBF)  # CJK Extension A
            or (0x3040 <= code_point <= 0x309F)  # Hiragana
            or (0x30A0 <= code_point <= 0x30FF)  # Katakana
            or (0xAC00 <= code_point <= 0xD7AF)  # Hangul Syllables
            or (0x0E00 <= code_point <= 0x0E7F)  # Thai
            or (0x0E80 <= code_point <= 0x0EFF)  # Lao
            or (0x1000 <= code_point <= 0x109F)  # Myanmar
            or (0x1780 <= code_point <= 0x17FF)  # Khmer
        )

    def _get_char_script(self, char: str) -> str:
        """
        Get the script family for a character.

        Args:
            char: Character to analyze

        Returns:
            Script family name
        """
        code_point = ord(char)

        # Latin script
        if (
            (0x0041 <= code_point <= 0x007A)
            or (0x00C0 <= code_point <= 0x024F)
            or (0x1E00 <= code_point <= 0x1EFF)
        ):
            return "latin"

        # Character-level scripts (CJK, Thai, etc.)
        elif self._is_char_level_script(char):
            return "cjk"

        # Arabic script
        elif (
            (0x0600 <= code_point <= 0x06FF)
            or (0x0750 <= code_point <= 0x077F)
            or (0x08A0 <= code_point <= 0x08FF)
        ):
            return "arabic"

        else:
            return "other"

    def _extract_tokens_ordered(
        self, text: str, language_family: LanguageFamily
    ) -> TokenList:
        """
        Extract tokens preserving their original order in the text.

        Uses a single comprehensive regex pattern to find ALL tokens in document order,
        eliminating the need for complex segmentation and reassembly logic.
        This is the Phase 2 optimization that removes O(n×segments) complexity.

        Args:
            text: Preprocessed text to tokenize
            language_family: Detected language family for the full text

        Returns:
            List of extracted tokens in their original order
        """
        if not text.strip():
            return []

        # Remove excluded entities (URLs/emails) from text if they are disabled
        # This prevents them from being tokenized into component words
        exclusion_pattern = self._patterns.get_exclusion_pattern(self._config)
        if exclusion_pattern:
            # Replace excluded entities with spaces to maintain word boundaries
            text = exclusion_pattern.sub(" ", text)
            # Clean up multiple spaces
            text = " ".join(text.split())

        if not text.strip():
            return []

        # Get comprehensive pattern based on configuration
        # This single pattern finds ALL tokens in document order
        comprehensive_pattern = self._patterns.get_comprehensive_pattern(self._config)

        # Single regex call gets all tokens in order - this is the key optimization!
        raw_tokens = comprehensive_pattern.findall(text)

        # If no tokens were found but input has content, use fallback for edge cases
        if not raw_tokens and text.strip():
            # For pure punctuation or unrecognized content, return as single token
            # This maintains compatibility with old tokenizer behavior for edge cases
            return [text.strip()]

        # Apply postprocessing for language-specific behavior and configuration filtering
        tokens = []
        for token in raw_tokens:
            if not token.strip():
                continue

            # Clean URLs by removing trailing punctuation
            if self._is_url_like(token):
                token = self._clean_url_token(token)

            # For character-level scripts, break down multi-character tokens into individual characters
            # This maintains compatibility with existing test expectations
            if (
                language_family == LanguageFamily.CJK
                and self._contains_char_level_chars(token)
            ):
                # Only break down pure character-level tokens, not mixed tokens
                if self._is_pure_char_level_token(token):
                    tokens.extend(list(token))
                else:
                    # Mixed token - keep as is but process character-level parts
                    tokens.append(token)
            elif language_family == LanguageFamily.MIXED:
                # For mixed script, break down character-level script parts but keep Latin parts whole
                processed_tokens = self._process_mixed_script_token(token)
                tokens.extend(processed_tokens)
            else:
                tokens.append(token)

        return [token for token in tokens if token.strip()]

    def _is_punctuation_only(self, token: str) -> bool:
        """Check if token contains only punctuation."""
        punctuation_chars = ".!?;:,()[]{}\"'-~`@#$%^&*+=<>/|\\"
        return all(c in punctuation_chars for c in token)

    def _is_numeric_only(self, token: str) -> bool:
        """Check if token is purely numeric."""
        return (
            token.replace(".", "")
            .replace(",", "")
            .replace("%", "")
            .replace("$", "")
            .isdigit()
        )

    def _is_url_like(self, token: str) -> bool:
        """Check if token looks like a URL."""
        # Don't classify emails as URLs
        if self._is_email_like(token):
            return False

        return (
            token.startswith(("http://", "https://", "www."))
            or "://" in token
            or (
                token.count(".") >= 1
                and any(c.isalpha() for c in token)
                and "@" not in token
            )
        )

    def _is_email_like(self, token: str) -> bool:
        """Check if token looks like an email address."""
        return "@" in token and "." in token and not token.startswith("@")

    def _clean_url_token(self, url_token: str) -> str:
        """Remove trailing punctuation from URL tokens."""
        trailing_punctuation = ".!?;:,)]}\"'"
        return url_token.rstrip(trailing_punctuation)

    def _contains_char_level_chars(self, token: str) -> bool:
        """Check if token contains any character-level script characters."""
        return any(self._is_char_level_script(char) for char in token)

    def _is_pure_char_level_token(self, token: str) -> bool:
        """Check if token contains only character-level script characters."""
        return all(self._is_char_level_script(char) or char.isspace() for char in token)

    def _process_mixed_script_token(self, token: str) -> TokenList:
        """Process mixed script tokens by breaking down character-level script parts."""
        if not self._contains_char_level_chars(token):
            return [token]

        result = []
        current_token = ""
        current_is_cjk = None

        for char in token:
            char_is_cjk = self._is_char_level_script(char)

            if current_is_cjk is None:
                current_is_cjk = char_is_cjk
                current_token = char
            elif char_is_cjk == current_is_cjk:
                current_token += char
            else:
                # Script change
                if current_token.strip():
                    if current_is_cjk and len(current_token) > 1:
                        # Break CJK into individual characters
                        result.extend(list(current_token))
                    else:
                        result.append(current_token)
                current_token = char
                current_is_cjk = char_is_cjk

        # Handle final token
        if current_token.strip():
            if current_is_cjk and len(current_token) > 1:
                result.extend(list(current_token))
            else:
                result.append(current_token)

        return result

    def _postprocess_tokens(self, tokens: TokenList) -> TokenList:
        """
        Apply post-processing to extracted tokens.

        Args:
            tokens: List of raw tokens

        Returns:
            Processed token list
        """
        if not tokens:
            return tokens

        # Apply base class post-processing (length filtering, whitespace stripping, etc.)
        return super()._postprocess_tokens(tokens)
