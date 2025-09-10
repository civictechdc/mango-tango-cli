"""
AbstractTokenizer abstract base class

This module contains the abstract base class that defines
the interface for all tokenizer implementations.
"""

from abc import ABC, abstractmethod
from typing import Optional

from .types import LanguageFamily, TokenizedResult, TokenizerConfig, TokenList


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

    def update_config(self, **kwargs) -> None:
        """
        Update configuration parameters.

        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
            else:
                raise ValueError(f"Unknown configuration parameter: {key}")

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

    @abstractmethod
    def tokenize_with_types(self, text: str) -> TokenizedResult:
        """
        Tokenize input text and return tokens grouped by type.

        Args:
            text: Input text to tokenize

        Returns:
            Dictionary mapping token types to lists of tokens
        """
        pass

    @abstractmethod
    def detect_language_family(self, text: str) -> LanguageFamily:
        """
        Detect the language family of input text.

        This method should analyze the text and determine which language family
        it belongs to, which affects tokenization strategy.

        Args:
            text: Input text to analyze

        Returns:
            Detected language family
        """
        pass

    def is_space_separated(self, text: str) -> bool:
        """
        Determine if the text uses space-separated tokens.

        This is a convenience method that uses language detection to determine
        if the text uses spaces to separate words.

        Args:
            text: Input text to analyze

        Returns:
            True if the text appears to use space separation, False otherwise
        """
        family = self.detect_language_family(text)
        return family in (LanguageFamily.LATIN, LanguageFamily.ARABIC)

    def preprocess_text(self, text: str) -> str:
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
            # Simple normalization - convert to lowercase but preserve proper nouns
            # This is a basic implementation, can be enhanced later
            text = text.lower()

        return text

    def postprocess_tokens(self, tokens: TokenList) -> TokenList:
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
