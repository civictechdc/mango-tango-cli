"""
AbstractTokenizer abstract base class

This module contains the abstract base class that defines
the interface for all tokenizer implementations.
"""

from abc import ABC, abstractmethod
from typing import Optional

from .types import TokenizerConfig, TokenList


class AbstractTokenizer(ABC):
    """
    Abstract base class for all tokenizer implementations.

    This class defines the core interface that all tokenizer plugins must implement.
    It provides a clean contract for tokenization operations while allowing for
    different implementation strategies.
    """

    def __init__(self, config: Optional[TokenizerConfig] = None):
        """
        Initialize the tokenizer with configuration.

        Args:
            config: Tokenizer configuration. If None, default config will be used.
        """
        self._config = config or TokenizerConfig()

    @property
    def config(self) -> TokenizerConfig:
        """Get the current tokenizer configuration."""
        return self._config

    @abstractmethod
    def tokenize(self, text: str) -> TokenList:
        """
        Tokenize input text into a list of tokens.

        This is the main tokenization method that all implementations must provide.

        Args:
            text: Input text to tokenize

        Returns:
            List of tokens extracted from the input text
        """
        pass

    def _preprocess_text(self, text: str) -> str:
        """
        Apply preprocessing to text before tokenization.

        This method applies configuration-based preprocessing such as
        case handling and Unicode normalization.

        Args:
            text: Input text to preprocess

        Returns:
            Preprocessed text
        """
        if not text:
            return text

        # Apply Unicode normalization
        if self._config.normalize_unicode:
            import unicodedata

            text = unicodedata.normalize("NFKC", text)

        # Apply case handling
        from .types import CaseHandling

        if self._config.case_handling == CaseHandling.LOWERCASE:
            text = text.lower()
        elif self._config.case_handling == CaseHandling.UPPERCASE:
            text = text.upper()
        elif self._config.case_handling == CaseHandling.NORMALIZE:
            # TODO: Implement proper noun detection for smart normalization
            # Currently using simple lowercase as a placeholder
            text = text.lower()

        return text

    def _postprocess_tokens(self, tokens: TokenList) -> TokenList:
        """
        Apply post-processing to extracted tokens.

        This method applies configuration-based filtering and cleanup
        to the token list.

        Args:
            tokens: List of raw tokens

        Returns:
            Processed token list
        """
        if not tokens:
            return tokens

        processed_tokens = []

        for token in tokens:
            # Strip whitespace if configured
            if self._config.strip_whitespace:
                token = token.strip()

            # Skip empty tokens
            if not token:
                continue

            # Filter emojis if not included
            if not self._config.include_emoji and self._is_emoji(token):
                continue

            # Apply length filtering
            if len(token) < self._config.min_token_length:
                continue

            if (
                self._config.max_token_length is not None
                and len(token) > self._config.max_token_length
            ):
                continue

            processed_tokens.append(token)

        return processed_tokens

    def _is_emoji(self, token: str) -> bool:
        """
        Check if a token is an emoji character.

        Args:
            token: Token to check

        Returns:
            True if the token is an emoji, False otherwise
        """
        if not token:
            return False

        # Check if the token consists entirely of emoji characters
        for char in token:
            code_point = ord(char)
            # Check common emoji Unicode ranges
            if not (
                (0x1F600 <= code_point <= 0x1F64F)  # Emoticons
                or (0x1F300 <= code_point <= 0x1F5FF)  # Misc Symbols
                or (0x1F680 <= code_point <= 0x1F6FF)  # Transport
                or (0x1F1E0 <= code_point <= 0x1F1FF)  # Flags
                or (0x2700 <= code_point <= 0x27BF)  # Dingbats
                or (0x1F900 <= code_point <= 0x1F9FF)  # Supplemental Symbols
                or (0x2600 <= code_point <= 0x26FF)  # Misc symbols
            ):
                return False

        return True
