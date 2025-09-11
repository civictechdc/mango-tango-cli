"""
Tokenizer service for Unicode-aware text tokenization.

This service provides tokenization capabilities for social media analytics,
with support for multilingual content and entity preservation.
"""

# Core interfaces and types
from .core import (
    AbstractTokenizer,
    CaseHandling,
    LanguageFamily,
    TokenizerConfig,
    TokenList,
    TokenType,
)

# Basic implementation
from .basic import BasicTokenizer, create_basic_tokenizer, tokenize_text

# Main exports
__all__ = [
    # Core interfaces
    "AbstractTokenizer",
    "TokenizerConfig",
    # Core types
    "TokenList",
    "LanguageFamily",
    "TokenType",
    "CaseHandling",
    # Basic implementation
    "BasicTokenizer",
    "create_basic_tokenizer",
    "tokenize_text",
]