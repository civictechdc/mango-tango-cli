"""
Basic tokenizer implementation.

This module exports the BasicTokenizer implementation that provides
fundamental Unicode-aware tokenization capabilities for social media text.
"""

from ..core.types import TokenizerConfig
from .patterns import get_patterns
from .tokenizer import BasicTokenizer


# Convenience factory functions
def create_basic_tokenizer(config: TokenizerConfig | None = None) -> BasicTokenizer:
    """Create a BasicTokenizer with optional configuration."""
    if config is None:
        config = TokenizerConfig()
    return BasicTokenizer(config)


def tokenize_text(text: str, config: TokenizerConfig | None = None) -> list[str]:
    """Simple convenience function for basic text tokenization."""
    tokenizer = create_basic_tokenizer(config)
    return tokenizer.tokenize(text)


__all__ = [
    "BasicTokenizer",
    "TokenizerConfig",
    "get_patterns",
    "create_basic_tokenizer",
    "tokenize_text",
]
