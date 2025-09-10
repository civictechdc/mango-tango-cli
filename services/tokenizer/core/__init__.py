"""
Core tokenizer components

This module exports AbstractTokenizer and TokenizerConfig for
implementing custom tokenization strategies.
"""

from .base import AbstractTokenizer
from .types import (
    CaseHandling,
    LanguageFamily,
    SpaceType,
    TokenizedResult,
    TokenizerConfig,
    TokenList,
    TokenType,
)

# Main exports for plugin implementations
__all__ = [
    "AbstractTokenizer",
    "TokenizerConfig",
    # Type definitions
    "TokenList",
    "TokenizedResult",
    # Enumerations
    "LanguageFamily",
    "SpaceType",
    "TokenType",
    "CaseHandling",
]
