"""
Shared pytest fixtures for tokenizer tests.

This module provides common tokenizer configurations and helper functions
to reduce duplication across test files.
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
    """Tokenizer configured for clean text (no social entities)."""
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
    """Tokenizer that preserves original case."""
    config = TokenizerConfig(case_handling=CaseHandling.PRESERVE)
    return BasicTokenizer(config)


# =============================================================================
# Test Data Fixtures
# =============================================================================


@pytest.fixture
def multilingual_test_data():
    """Common multilingual test texts."""
    return {
        "latin": ("Hello world", ["hello", "world"]),
        "chinese": ("你好世界", ["你", "好", "世", "界"]),
        "japanese": ("こんにちは世界", ["こ", "ん", "に", "ち", "は", "世", "界"]),
        "arabic": ("مرحبا بك في العالم", ["مرحبا", "بك", "في", "العالم"]),
        "thai": ("สวัสดีครับ", ["ส", "ว", "ั", "ส", "ด", "ี", "ค", "ร", "ั", "บ"]),
        "korean": ("안녕하세요 세계", ["안녕하세요", "세계"]),
    }


@pytest.fixture
def social_media_test_data():
    """Common social media test texts."""
    return {
        "basic": "@user check #hashtag",
        "with_url": "Visit https://example.com for info",
        "complex": "@user check #hashtag https://example.com 🎉",
    }


# =============================================================================
# Helper Assertion Functions
# =============================================================================


def assert_tokens_present(result, *expected):
    """Assert that all expected tokens are present in result.

    Args:
        result: List of tokens from tokenizer
        *expected: Tokens that should be present
    """
    for token in expected:
        assert token in result, f"Token '{token}' not found in result: {result}"


def assert_tokens_ordered(result, *expected):
    """Assert that tokens appear in expected order.

    Args:
        result: List of tokens from tokenizer
        *expected: Tokens in expected order
    """
    indices = []
    for token in expected:
        if token in result:
            indices.append(result.index(token))
        else:
            raise AssertionError(f"Token '{token}' not found in result: {result}")

    assert indices == sorted(
        indices
    ), f"Tokens not in expected order. Expected order: {expected}, Got: {result}"


def assert_social_entities_preserved(result, mentions=None, hashtags=None, urls=None):
    """Assert that social media entities are preserved.

    Args:
        result: List of tokens from tokenizer
        mentions: List of @mentions to check (optional)
        hashtags: List of #hashtags to check (optional)
        urls: List of URLs to check (optional)
    """
    if mentions:
        for mention in mentions:
            assert mention in result, f"Mention '{mention}' not preserved in: {result}"

    if hashtags:
        for hashtag in hashtags:
            assert hashtag in result, f"Hashtag '{hashtag}' not preserved in: {result}"

    if urls:
        for url in urls:
            assert url in result, f"URL '{url}' not preserved in: {result}"
