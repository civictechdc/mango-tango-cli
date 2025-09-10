"""
Services package for Mango Tango CLI.

This package contains service modules that provide core functionality
for the application, organized in a modular and testable architecture.
"""

# Export tokenizer service for easy access
from .tokenizer import tokenize_text, create_basic_tokenizer, BasicTokenizer, TokenizerConfig

__all__ = [
    "tokenize_text",
    "create_basic_tokenizer", 
    "BasicTokenizer",
    "TokenizerConfig",
]