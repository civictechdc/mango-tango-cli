"""
Shared pytest fixtures for tokenizer tests.

Provides pre-configured tokenizer fixtures to reduce boilerplate:
- default_tokenizer: Standard configuration (lowercase, social media enabled)
- social_media_tokenizer: Full social media extraction (includes emoji)
- clean_text_tokenizer: No social entities, clean text only
- preserve_case_tokenizer: Case-preserving tokenization

Use fixtures in tests by adding them as function parameters:
    def test_my_feature(self, default_tokenizer):
        result = default_tokenizer.tokenize("test text")
        assert result == ["test", "text"]
"""

import pytest

from services.tokenizer.basic import BasicTokenizer
from services.tokenizer.core.types import CaseHandling, TokenizerConfig

# =============================================================================
# Tokenizer Fixtures
# =============================================================================


@pytest.fixture
def default_tokenizer():
    """Basic tokenizer with default configuration."""
    return BasicTokenizer()


@pytest.fixture
def social_media_tokenizer():
    """Tokenizer configured for social media analysis."""
    config = TokenizerConfig(
        extract_hashtags=True,
        extract_mentions=True,
        extract_cashtags=True,
        include_urls=True,
        include_emails=True,
        include_emoji=True,
        case_handling=CaseHandling.LOWERCASE,
    )
    return BasicTokenizer(config)


@pytest.fixture
def clean_text_tokenizer():
    """Tokenizer configured for clean text (no social entities).

    Example:
        def test_my_feature(self, clean_text_tokenizer):
            result = clean_text_tokenizer.tokenize("@user #hashtag")
            # Social entities removed, only words remain
            assert "user" in result
            assert "hashtag" in result
    """
    config = TokenizerConfig(
        extract_hashtags=False,
        extract_mentions=False,
        extract_cashtags=False,
        include_urls=False,
        include_emails=False,
        include_emoji=False,
        include_punctuation=False,
        case_handling=CaseHandling.LOWERCASE,
    )
    return BasicTokenizer(config)


@pytest.fixture
def preserve_case_tokenizer():
    """Tokenizer that preserves original case.

    Example:
        def test_my_feature(self, preserve_case_tokenizer):
            result = preserve_case_tokenizer.tokenize("Hello World")
            assert result == ["Hello", "World"]
    """
    config = TokenizerConfig(case_handling=CaseHandling.PRESERVE)
    return BasicTokenizer(config)
