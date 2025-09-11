"""
BasicTokenizer implementation.

This module contains the main BasicTokenizer class that implements
Unicode-aware tokenization for social media text with entity preservation.
"""

import re
from typing import Dict, Optional

from ..core.base import AbstractTokenizer
from ..core.types import (
    LanguageFamily,
    TokenizedResult,
    TokenizerConfig,
    TokenList,
    TokenType,
)
from .patterns import get_patterns


class BasicTokenizer(AbstractTokenizer):
    """
    Unicode-aware basic tokenizer for social media text.

    This tokenizer handles mixed-script content, preserves social media entities
    (@mentions, #hashtags, URLs), and applies appropriate tokenization strategies
    based on detected language families.
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

        Applies appropriate tokenization strategy based on detected language family
        while preserving social media entities and handling Unicode correctly.

        Args:
            text: Input text to tokenize

        Returns:
            List of tokens extracted from the input text
        """
        if not text:
            return []

        # Apply preprocessing
        processed_text = self.preprocess_text(text)
        if not processed_text:
            return []

        # Extract tokens using comprehensive regex pattern
        tokens = self._extract_tokens(processed_text)

        # Apply post-processing
        return self.postprocess_tokens(tokens)

    def tokenize_with_types(self, text: str) -> TokenizedResult:
        """
        Tokenize input text and return tokens grouped by type.

        Args:
            text: Input text to tokenize

        Returns:
            Dictionary mapping token types to lists of tokens
        """
        if not text:
            return {}

        processed_text = self.preprocess_text(text)
        if not processed_text:
            return {}

        # Initialize result dictionary
        result: TokenizedResult = {}

        # Extract and classify tokens
        classified_tokens = self._extract_and_classify_tokens(processed_text)

        # Group tokens by type
        for token_type, tokens in classified_tokens.items():
            if tokens:  # Only include non-empty token lists
                processed_tokens = self.postprocess_tokens(tokens)
                if processed_tokens:
                    result[token_type.value] = processed_tokens

        return result

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

    def _extract_and_classify_tokens(self, text: str) -> Dict[TokenType, TokenList]:
        """
        Extract tokens and classify them by type using comprehensive regex.

        Args:
            text: Preprocessed text to tokenize

        Returns:
            Dictionary mapping token types to token lists
        """
        result: Dict[TokenType, TokenList] = {}

        # Initialize token type lists
        for token_type in TokenType:
            result[token_type] = []

        # Get all tokens using comprehensive pattern
        comprehensive_pattern = self._patterns.get_comprehensive_pattern(self._config)
        all_tokens = comprehensive_pattern.findall(text)

        # Classify each token by type
        for token in all_tokens:
            if not token.strip():
                continue

            # Classify token by its characteristics
            if token.startswith("http") or "://" in token:
                result[TokenType.URL].append(self._clean_url_token(token))
            elif "@" in token and "." in token and token.count("@") == 1:
                result[TokenType.EMAIL].append(token)
            elif token.startswith("@"):
                result[TokenType.MENTION].append(token)
            elif token.startswith("#"):
                result[TokenType.HASHTAG].append(token)
            elif self._is_emoji_only(token):
                result[TokenType.EMOJI].append(token)
            elif self._is_numeric_only(token):
                result[TokenType.NUMERIC].append(token)
            elif self._is_punctuation_only(token):
                result[TokenType.PUNCTUATION].append(token)
            else:
                result[TokenType.WORD].append(token)

        return result

    def _is_cjk_char(self, char: str) -> bool:
        """Check if character is CJK."""
        code_point = ord(char)
        return (
            (0x4E00 <= code_point <= 0x9FFF)  # CJK Unified Ideographs
            or (0x3400 <= code_point <= 0x4DBF)  # CJK Extension A
            or (0x3040 <= code_point <= 0x309F)  # Hiragana
            or (0x30A0 <= code_point <= 0x30FF)  # Katakana
            or (0xAC00 <= code_point <= 0xD7AF)  # Hangul Syllables
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

        # CJK scripts
        elif self._is_cjk_char(char):
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

            # For CJK languages, break down multi-character tokens into individual characters
            # This maintains compatibility with existing test expectations
            if language_family == LanguageFamily.CJK and self._contains_cjk_chars(
                token
            ):
                # Only break down pure CJK tokens, not mixed tokens
                if self._is_pure_cjk_token(token):
                    tokens.extend(list(token))
                else:
                    # Mixed token - keep as is but process CJK parts
                    tokens.append(token)
            elif language_family == LanguageFamily.MIXED:
                # For mixed script, break down CJK parts but keep Latin parts whole
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

    def _is_emoji_only(self, token: str) -> bool:
        """Check if token contains only emoji characters."""
        # Basic emoji ranges
        for char in token:
            code_point = ord(char)
            if not (
                (0x1F600 <= code_point <= 0x1F64F)  # Emoticons
                or (0x1F300 <= code_point <= 0x1F5FF)  # Misc Symbols
                or (0x1F680 <= code_point <= 0x1F6FF)  # Transport
                or (0x1F1E0 <= code_point <= 0x1F1FF)  # Flags
                or (0x2700 <= code_point <= 0x27BF)  # Dingbats
                or (0x1F900 <= code_point <= 0x1F9FF)  # Supplemental Symbols
                or (0x2600 <= code_point <= 0x26FF)
            ):  # Misc symbols
                return False
        return True

    def _is_url_like(self, token: str) -> bool:
        """Check if token looks like a URL."""
        return (
            token.startswith(("http://", "https://", "www."))
            or "://" in token
            or (token.count(".") >= 1 and any(c.isalpha() for c in token))
        )

    def _clean_url_token(self, url_token: str) -> str:
        """Remove trailing punctuation from URL tokens."""
        trailing_punctuation = ".!?;:,)]}\"'"
        return url_token.rstrip(trailing_punctuation)

    def _contains_cjk_chars(self, token: str) -> bool:
        """Check if token contains any CJK characters."""
        return any(self._is_cjk_char(char) for char in token)

    def _is_pure_cjk_token(self, token: str) -> bool:
        """Check if token contains only CJK characters."""
        return all(self._is_cjk_char(char) or char.isspace() for char in token)

    def _process_mixed_script_token(self, token: str) -> TokenList:
        """Process mixed script tokens by breaking down CJK parts."""
        if not self._contains_cjk_chars(token):
            return [token]

        result = []
        current_token = ""
        current_is_cjk = None

        for char in token:
            char_is_cjk = self._is_cjk_char(char)

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
