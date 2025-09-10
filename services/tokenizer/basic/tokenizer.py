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
    TokenizerConfig, 
    TokenList, 
    TokenizedResult, 
    TokenType
)
from .language_detection import detect_language_family
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

        # Detect language family for tokenization strategy
        language_family = self.detect_language_family(processed_text)
        
        # Extract tokens based on language family and configuration
        tokens = self._extract_tokens(processed_text, language_family)
        
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

    def detect_language_family(self, text: str) -> LanguageFamily:
        """
        Detect the language family of input text.

        Args:
            text: Input text to analyze

        Returns:
            Detected language family
        """
        if not self._config.detect_language:
            return self._config.fallback_language_family
        
        return detect_language_family(text)

    def _extract_tokens(self, text: str, language_family: LanguageFamily) -> TokenList:
        """
        Extract tokens using the appropriate strategy for the language family.

        Args:
            text: Preprocessed text to tokenize
            language_family: Detected language family

        Returns:
            List of extracted tokens
        """
        tokens = []

        # First, extract and preserve social media entities
        social_entities, cleaned_text = self._extract_social_entities(text)
        tokens.extend(social_entities)

        # Apply language-specific tokenization to remaining text
        if language_family == LanguageFamily.CJK:
            tokens.extend(self._tokenize_cjk(cleaned_text))
        elif language_family == LanguageFamily.ARABIC:
            tokens.extend(self._tokenize_arabic(cleaned_text))
        elif language_family == LanguageFamily.MIXED:
            tokens.extend(self._tokenize_mixed_script(cleaned_text))
        else:  # LATIN or UNKNOWN
            tokens.extend(self._tokenize_latin(cleaned_text))

        return tokens

    def _extract_and_classify_tokens(self, text: str) -> Dict[TokenType, TokenList]:
        """
        Extract tokens and classify them by type.

        Args:
            text: Preprocessed text to tokenize

        Returns:
            Dictionary mapping token types to token lists
        """
        result: Dict[TokenType, TokenList] = {}
        
        # Initialize token type lists
        for token_type in TokenType:
            result[token_type] = []

        # Extract social media entities first
        if self._config.extract_urls:
            result[TokenType.URL].extend(self._extract_pattern_tokens(text, 'url'))
        if self._config.extract_emails:
            result[TokenType.EMAIL].extend(self._extract_pattern_tokens(text, 'email'))
        if self._config.extract_mentions:
            result[TokenType.MENTION].extend(self._extract_pattern_tokens(text, 'mention'))
        if self._config.extract_hashtags:
            result[TokenType.HASHTAG].extend(self._extract_pattern_tokens(text, 'hashtag'))

        # Remove social entities from text for further processing
        cleaned_text = text
        for pattern_name in ['url', 'email', 'mention', 'hashtag']:
            if hasattr(self._config, f'extract_{pattern_name}s') or pattern_name in ['url', 'email', 'mention', 'hashtag']:
                pattern = self._patterns.get_pattern(pattern_name)
                cleaned_text = pattern.sub(' ', cleaned_text)

        # Extract other token types
        if self._config.include_emoji:
            result[TokenType.EMOJI].extend(self._extract_pattern_tokens(cleaned_text, 'emoji'))
        if self._config.include_numeric:
            result[TokenType.NUMERIC].extend(self._extract_pattern_tokens(cleaned_text, 'numeric'))
        if self._config.include_punctuation:
            result[TokenType.PUNCTUATION].extend(self._extract_pattern_tokens(cleaned_text, 'punctuation'))

        # Extract words (remaining after removing other entities)
        words = self._extract_words_from_cleaned_text(cleaned_text)
        result[TokenType.WORD].extend(words)

        return result

    def _extract_social_entities(self, text: str) -> tuple[TokenList, str]:
        """
        Extract social media entities and return them with cleaned text.

        Args:
            text: Input text

        Returns:
            Tuple of (social_entities, cleaned_text)
        """
        entities = []
        cleaned_text = text

        # Extract entities based on configuration
        if self._config.extract_urls:
            entities.extend(self._extract_pattern_tokens(text, 'url'))
            cleaned_text = self._patterns.get_pattern('url').sub(' ', cleaned_text)

        if self._config.extract_emails:
            entities.extend(self._extract_pattern_tokens(text, 'email'))
            cleaned_text = self._patterns.get_pattern('email').sub(' ', cleaned_text)

        if self._config.extract_mentions:
            entities.extend(self._extract_pattern_tokens(text, 'mention'))
            cleaned_text = self._patterns.get_pattern('mention').sub(' ', cleaned_text)

        if self._config.extract_hashtags:
            entities.extend(self._extract_pattern_tokens(text, 'hashtag'))
            cleaned_text = self._patterns.get_pattern('hashtag').sub(' ', cleaned_text)

        # Clean up multiple spaces
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

        return entities, cleaned_text

    def _extract_pattern_tokens(self, text: str, pattern_name: str) -> TokenList:
        """
        Extract tokens matching a specific pattern.

        Args:
            text: Input text
            pattern_name: Name of the pattern to use

        Returns:
            List of tokens matching the pattern
        """
        try:
            pattern = self._patterns.get_pattern(pattern_name)
            return pattern.findall(text)
        except KeyError:
            return []

    def _tokenize_latin(self, text: str) -> TokenList:
        """
        Tokenize Latin script text (space-separated).

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        if not text.strip():
            return []

        # Use word pattern for Latin script
        pattern = self._patterns.get_pattern('latin_word')
        tokens = pattern.findall(text)
        
        # If no matches, fall back to simple space splitting
        if not tokens:
            tokens = text.split()
        
        return [token for token in tokens if token.strip()]

    def _tokenize_cjk(self, text: str) -> TokenList:
        """
        Tokenize CJK (Chinese, Japanese, Korean) text.

        Args:
            text: Text to tokenize

        Returns:
            List of tokens (individual characters or grouped sequences)
        """
        if not text.strip():
            return []

        tokens = []
        current_token = ""
        
        for char in text:
            if char.isspace():
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
            elif self._is_cjk_char(char):
                # Add current token if it exists
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
                # Add CJK character as individual token
                tokens.append(char)
            else:
                # Accumulate non-CJK characters
                current_token += char

        # Add final token if exists
        if current_token:
            tokens.append(current_token)

        return [token for token in tokens if token.strip()]

    def _tokenize_arabic(self, text: str) -> TokenList:
        """
        Tokenize Arabic script text.

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        if not text.strip():
            return []

        # Arabic is generally space-separated, but handle connected text
        tokens = text.split()
        
        # Filter out empty tokens
        return [token for token in tokens if token.strip()]

    def _tokenize_mixed_script(self, text: str) -> TokenList:
        """
        Tokenize mixed-script text (e.g., "iPhone用户").

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        if not text.strip():
            return []

        tokens = []
        current_token = ""
        current_script = None
        
        for char in text:
            if char.isspace():
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
                    current_script = None
            else:
                char_script = self._get_char_script(char)
                
                if current_script is None:
                    current_script = char_script
                    current_token = char
                elif char_script == current_script or char_script == "other":
                    current_token += char
                else:
                    # Script change - start new token
                    if current_token:
                        tokens.append(current_token)
                    current_token = char
                    current_script = char_script

        # Add final token
        if current_token:
            tokens.append(current_token)

        return [token for token in tokens if token.strip()]

    def _extract_words_from_cleaned_text(self, text: str) -> TokenList:
        """
        Extract word tokens from text that has social entities removed.

        Args:
            text: Cleaned text

        Returns:
            List of word tokens
        """
        if not text.strip():
            return []

        # Detect language family for appropriate word extraction
        language_family = self.detect_language_family(text)
        
        if language_family == LanguageFamily.CJK:
            return self._tokenize_cjk(text)
        elif language_family == LanguageFamily.ARABIC:
            return self._tokenize_arabic(text)
        elif language_family == LanguageFamily.MIXED:
            return self._tokenize_mixed_script(text)
        else:  # LATIN or UNKNOWN
            return self._tokenize_latin(text)

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
        if ((0x0041 <= code_point <= 0x007A) or
            (0x00C0 <= code_point <= 0x024F) or
            (0x1E00 <= code_point <= 0x1EFF)):
            return "latin"
        
        # CJK scripts
        elif self._is_cjk_char(char):
            return "cjk"
        
        # Arabic script
        elif ((0x0600 <= code_point <= 0x06FF) or
              (0x0750 <= code_point <= 0x077F) or
              (0x08A0 <= code_point <= 0x08FF)):
            return "arabic"
        
        else:
            return "other"