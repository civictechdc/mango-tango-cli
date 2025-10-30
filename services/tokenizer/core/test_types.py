#!/usr/bin/env python3
"""
Tests for tokenizer configuration and type system.

This module tests the TokenizerConfig Pydantic model, enum types,
type aliases, and configuration validation.

Test Organization:
- TestTokenizerConfig: Configuration model and defaults
- TestEnumTypes: Enum value and behavior validation
- TestTypeAliases: Type alias usage
- TestConfigurationValidation: Edge cases and validation
- TestConfigurationUseCases: Common configuration presets

Running Tests:
    pytest services/tokenizer/core/test_types.py
"""

from typing import Optional

import pytest

from .types import CaseHandling, LanguageFamily, TokenizerConfig, TokenList, TokenType


@pytest.mark.unit
@pytest.mark.config
class TestTokenizerConfig:
    """Test TokenizerConfig Pydantic model and validation."""

    def test_default_config(self):
        """Test default configuration values."""
        config = TokenizerConfig()

        # Language detection defaults (optimized for performance)
        assert config.fallback_language_family == LanguageFamily.MIXED

        # Space handling defaults

        # Token type filtering defaults
        assert config.include_punctuation is False
        assert config.include_numeric is True
        assert config.include_emoji is False

        # Text preprocessing defaults
        assert config.case_handling == CaseHandling.LOWERCASE
        assert config.normalize_unicode is False

        # Social media defaults
        assert config.extract_hashtags is True
        assert config.extract_mentions is True
        assert config.include_urls is True
        assert config.include_emails is True

        # Output formatting defaults
        assert config.min_token_length == 1
        assert config.max_token_length is None
        assert config.strip_whitespace is True

    def test_custom_config(self):
        """Test custom configuration values."""
        config = TokenizerConfig(
            fallback_language_family=LanguageFamily.ARABIC,
            include_punctuation=True,
            include_numeric=False,
            include_emoji=False,
            case_handling=CaseHandling.PRESERVE,
            normalize_unicode=False,
            extract_hashtags=False,
            extract_mentions=False,
            include_urls=False,
            include_emails=True,
            min_token_length=2,
            max_token_length=100,
            strip_whitespace=False,
        )

        # Verify all custom values are set correctly
        assert config.fallback_language_family == LanguageFamily.ARABIC
        assert config.include_punctuation is True
        assert config.include_numeric is False
        assert config.include_emoji is False
        assert config.case_handling == CaseHandling.PRESERVE
        assert config.normalize_unicode is False
        assert config.extract_hashtags is False
        assert config.extract_mentions is False
        assert config.include_urls is False
        assert config.include_emails is True
        assert config.min_token_length == 2
        assert config.max_token_length == 100
        assert config.strip_whitespace is False

    def test_config_mutability(self):
        """Test that configuration can be modified after creation (dataclass is mutable by default)."""
        config = TokenizerConfig()

        # Should be able to modify (dataclass is mutable by default)
        original_min_length = config.min_token_length
        config.min_token_length = 5
        assert config.min_token_length == 5
        assert config.min_token_length != original_min_length

        # Test modification of other fields to ensure true mutability
        config.include_emoji = not config.include_emoji
        config.case_handling = CaseHandling.UPPERCASE
        assert config.case_handling == CaseHandling.UPPERCASE

    def test_social_media_presets(self):
        """Test common social media configuration presets."""
        # Preset 1: Full social media extraction
        social_config = TokenizerConfig(
            extract_hashtags=True,
            extract_mentions=True,
            include_urls=True,
            include_emails=True,
            include_emoji=True,
            case_handling=CaseHandling.LOWERCASE,
        )

        assert social_config.extract_hashtags
        assert social_config.extract_mentions
        assert social_config.include_urls
        assert social_config.include_emails
        assert social_config.include_emoji

        # Preset 2: Clean text only (no social entities)
        clean_config = TokenizerConfig(
            extract_hashtags=False,
            extract_mentions=False,
            include_urls=False,
            include_emails=False,
            include_emoji=False,
            include_punctuation=False,
            case_handling=CaseHandling.LOWERCASE,
        )

        assert not clean_config.extract_hashtags
        assert not clean_config.extract_mentions
        assert not clean_config.include_urls
        assert not clean_config.include_emails
        assert not clean_config.include_emoji
        assert not clean_config.include_punctuation


@pytest.mark.unit
class TestEnumTypes:
    """Test enum types and their values."""

    def test_language_family_enum(self):
        """Test LanguageFamily enum values."""
        # Test all enum values exist
        assert hasattr(LanguageFamily, "LATIN")
        assert hasattr(LanguageFamily, "ARABIC")
        assert hasattr(LanguageFamily, "MIXED")
        assert hasattr(LanguageFamily, "UNKNOWN")

        # Test enum values
        assert LanguageFamily.LATIN.value == "latin"
        assert LanguageFamily.ARABIC.value == "arabic"
        assert LanguageFamily.MIXED.value == "mixed"
        assert LanguageFamily.UNKNOWN.value == "unknown"

    def test_token_type_enum(self):
        """Test TokenType enum values."""
        expected_types = [
            "WORD",
            "PUNCTUATION",
            "NUMERIC",
            "EMOJI",
            "HASHTAG",
            "MENTION",
            "URL",
            "EMAIL",
            "WHITESPACE",
        ]

        for type_name in expected_types:
            assert hasattr(TokenType, type_name)

        # Test specific values
        assert TokenType.WORD.value == "word"
        assert TokenType.HASHTAG.value == "hashtag"
        assert TokenType.MENTION.value == "mention"
        assert TokenType.URL.value == "url"
        assert TokenType.EMAIL.value == "email"
        assert TokenType.EMOJI.value == "emoji"

    def test_case_handling_enum(self):
        """Test CaseHandling enum values."""
        expected_cases = ["PRESERVE", "LOWERCASE", "UPPERCASE", "NORMALIZE"]

        for case_name in expected_cases:
            assert hasattr(CaseHandling, case_name)

        # Test values
        assert CaseHandling.PRESERVE.value == "preserve"
        assert CaseHandling.LOWERCASE.value == "lowercase"
        assert CaseHandling.UPPERCASE.value == "uppercase"
        assert CaseHandling.NORMALIZE.value == "normalize"


@pytest.mark.unit
@pytest.mark.config
class TestConfigurationValidation:
    """Test configuration validation and edge cases."""

    def test_min_max_token_length_validation(self):
        """Test minimum and maximum token length validation."""
        # Valid configurations
        config1 = TokenizerConfig(min_token_length=1, max_token_length=None)
        assert config1.min_token_length == 1
        assert config1.max_token_length is None

        config2 = TokenizerConfig(min_token_length=1, max_token_length=10)
        assert config2.min_token_length == 1
        assert config2.max_token_length == 10

        # Edge cases that should be allowed (validation might be in tokenizer)
        config3 = TokenizerConfig(min_token_length=0)  # Zero length
        assert config3.min_token_length == 0

        config4 = TokenizerConfig(min_token_length=100)  # Large minimum
        assert config4.min_token_length == 100

    def test_boolean_combinations(self):
        """Test various boolean configuration combinations."""
        # All social features enabled
        config_all = TokenizerConfig(
            extract_hashtags=True,
            extract_mentions=True,
            include_urls=True,
            include_emails=True,
            include_emoji=True,
            include_punctuation=True,
            include_numeric=True,
        )

        social_features = [
            config_all.extract_hashtags,
            config_all.extract_mentions,
            config_all.include_urls,
            config_all.include_emails,
        ]
        include_features = [
            config_all.include_emoji,
            config_all.include_punctuation,
            config_all.include_numeric,
        ]

        assert all(social_features)
        assert all(include_features)

        # All features disabled
        config_none = TokenizerConfig(
            extract_hashtags=False,
            extract_mentions=False,
            include_urls=False,
            include_emails=False,
            include_emoji=False,
            include_punctuation=False,
            include_numeric=False,
        )

        social_features_none = [
            config_none.extract_hashtags,
            config_none.extract_mentions,
            config_none.include_urls,
            config_none.include_emails,
        ]
        include_features_none = [
            config_none.include_emoji,
            config_none.include_punctuation,
            config_none.include_numeric,
        ]

        assert not any(social_features_none)
        assert not any(include_features_none)


@pytest.mark.unit
@pytest.mark.config
class TestConfigurationEdgeCases:
    """Test configuration validation and edge cases."""

    def test_min_greater_than_max_token_length(self):
        """Test behavior when min_token_length > max_token_length."""
        from ..basic.tokenizer import BasicTokenizer

        # This should either raise an error or be handled gracefully
        config = TokenizerConfig(min_token_length=10, max_token_length=5)
        tokenizer = BasicTokenizer(config)

        # Test with text that has tokens in the conflicting range
        text = "short verylongword medium"
        result = tokenizer.tokenize(text)

        # When min > max, no tokens should pass both filters
        # This documents the behavior (even if it's a logical error)
        assert result == []

    def test_negative_min_token_length(self):
        """Test handling of negative min_token_length."""
        from ..basic.tokenizer import BasicTokenizer

        config = TokenizerConfig(min_token_length=-1)
        tokenizer = BasicTokenizer(config)
        text = "test text"
        result = tokenizer.tokenize(text)

        # Should handle gracefully (probably treat as 0 or 1)
        assert isinstance(result, list)
        assert len(result) == 2  # expected 2 tokens

    def test_zero_min_token_length(self):
        """Test zero min_token_length allows empty tokens."""
        from ..basic.tokenizer import BasicTokenizer

        config = TokenizerConfig(min_token_length=0)
        tokenizer = BasicTokenizer(config)
        text = "test this and a new word"
        result = tokenizer.tokenize(text)

        assert len(result) == 6  # expect 6 tokens

    def test_extremely_large_token_length_limits(self):
        """Test very large token length limits."""
        from ..basic.tokenizer import BasicTokenizer

        config = TokenizerConfig(min_token_length=1000)
        tokenizer = BasicTokenizer(config)
        text = "normal length words here"
        result = tokenizer.tokenize(text)

        # Should filter out all normal-length tokens
        assert result == []

    def test_max_token_length_zero(self):
        """Test max_token_length=0."""
        from ..basic.tokenizer import BasicTokenizer

        config = TokenizerConfig(max_token_length=0)
        tokenizer = BasicTokenizer(config)
        text = "test words"
        result = tokenizer.tokenize(text)

        # Should filter everything
        assert result == []


@pytest.mark.unit
@pytest.mark.config
class TestConfigurationUseCases:
    """Test configurations for common use cases."""

    def test_research_analysis_config(self):
        """Test configuration suitable for research/academic analysis."""
        config = TokenizerConfig(
            # Clean text processing
            extract_hashtags=False,
            extract_mentions=False,
            include_urls=False,
            include_emails=False,
            include_emoji=False,
            include_punctuation=False,
            # Consistent casing
            case_handling=CaseHandling.LOWERCASE,
            normalize_unicode=True,
            # Filter very short tokens
            min_token_length=2,
        )

        # Verify research-friendly settings
        assert not config.extract_hashtags
        assert not config.extract_mentions
        assert not config.include_emoji
        assert config.case_handling == CaseHandling.LOWERCASE
        assert config.min_token_length >= 2

    def test_social_media_monitoring_config(self):
        """Test configuration for social media monitoring."""
        config = TokenizerConfig(
            # Extract all social entities
            extract_hashtags=True,
            extract_mentions=True,
            include_urls=True,
            include_emails=True,
            include_emoji=True,
            # Keep some formatting
            include_punctuation=True,
            case_handling=CaseHandling.PRESERVE,
            # Include very short tokens (acronyms, etc.)
            min_token_length=1,
            # Handle multilingual content
            normalize_unicode=True,
        )

        # Verify social media settings
        assert config.extract_hashtags
        assert config.extract_mentions
        assert config.include_urls
        assert config.include_emoji
        assert config.case_handling == CaseHandling.PRESERVE
        assert config.min_token_length == 1

    def test_content_analysis_config(self):
        """Test configuration for content analysis (no social entities)."""
        config = TokenizerConfig(
            # Pure content focus
            extract_hashtags=False,
            extract_mentions=False,
            include_urls=False,
            include_emails=False,
            include_emoji=False,
            # Clean text processing
            include_punctuation=False,
            case_handling=CaseHandling.LOWERCASE,
            normalize_unicode=True,
            # Standard filtering
            min_token_length=1,
            include_numeric=True,
        )

        # Verify content analysis settings
        social_extractions = [
            config.extract_hashtags,
            config.extract_mentions,
            config.include_urls,
            config.include_emails,
            config.include_emoji,
        ]
        assert not any(social_extractions)
        assert config.case_handling == CaseHandling.LOWERCASE
        assert config.normalize_unicode


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
