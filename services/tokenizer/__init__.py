"""
Tokenizer service for Unicode-aware text tokenization.

This service provides tokenization capabilities for social media analytics,
with support for multilingual content and entity preservation.
"""

# Core interfaces and types
from .core import AbstractTokenizer, TokenizerConfig, TokenType, LanguageFamily

# Basic tokenizer implementation  
from .basic import BasicTokenizer

# Convenience factory functions
def create_basic_tokenizer(config: TokenizerConfig = None) -> BasicTokenizer:
    """Create a BasicTokenizer with optional configuration."""
    if config is None:
        config = TokenizerConfig()
    return BasicTokenizer(config)

def tokenize_text(text: str, config: TokenizerConfig = None) -> list[str]:
    """Simple convenience function for basic text tokenization."""
    tokenizer = create_basic_tokenizer(config)
    return tokenizer.tokenize(text)

# Public API exports
__all__ = [
    # Core types
    "AbstractTokenizer",
    "TokenizerConfig", 
    "TokenType",
    "LanguageFamily",
    
    # Implementations
    "BasicTokenizer",
    
    # Factory functions
    "create_basic_tokenizer",
    "tokenize_text",
]