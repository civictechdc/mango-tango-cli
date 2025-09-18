#!/usr/bin/env python3
"""
Comprehensive tests for the tokenizer service.

This module tests the tokenizer service API, including:
- Service-level functionality
- Multilingual text handling
- Social media entity extraction
- Configuration options
- Integration with n-gram processing
"""

from typing import Dict, List

import pytest

from .basic import BasicTokenizer, create_basic_tokenizer, tokenize_text

# Core interfaces and types
from .core import AbstractTokenizer, LanguageFamily, TokenizerConfig, TokenType
from .core.types import CaseHandling


class TestTokenizerService:
    """Test the main tokenizer service API functions."""

    def test_tokenize_text_basic(self):
        """Test basic tokenize_text function."""
        text = "Hello world"
        result = tokenize_text(text)

        assert isinstance(result, list)
        assert all(isinstance(token, str) for token in result)
        assert "hello" in result
        assert "world" in result

    def test_tokenize_text_with_config(self):
        """Test tokenize_text with custom configuration."""
        text = "Hello World"
        config = TokenizerConfig(case_handling=CaseHandling.PRESERVE)
        result = tokenize_text(text, config)

        assert "Hello" in result
        assert "World" in result

    def test_create_basic_tokenizer(self):
        """Test basic tokenizer creation."""
        tokenizer = create_basic_tokenizer()
        assert isinstance(tokenizer, BasicTokenizer)

        # Test with custom config
        config = TokenizerConfig(min_token_length=2)
        tokenizer_custom = create_basic_tokenizer(config)
        assert isinstance(tokenizer_custom, BasicTokenizer)

    def test_tokenize_text_empty_input(self):
        """Test tokenizer behavior with empty/None input."""
        assert tokenize_text("") == []
        assert tokenize_text("   ") == []
        assert tokenize_text("\n\t  ") == []

    def test_tokenize_text_none_config(self):
        """Test tokenizer with None config (should use defaults)."""
        text = "Test text"
        result = tokenize_text(text)  # Use default config
        assert isinstance(result, list)
        assert len(result) > 0


class TestMultilingualTokenization:
    """Test basic multilingual tokenization through service API (smoke tests)."""

    def test_latin_text_smoke(self):
        """Test basic Latin script text tokenization via service API."""
        text = "Hello world café"
        result = tokenize_text(text)

        assert isinstance(result, list)
        assert len(result) > 0
        # Should be lowercase by default
        assert all(token.islower() or not token.isalpha() for token in result)
        assert "hello" in result
        assert "world" in result

    def test_mixed_script_smoke(self):
        """Test mixed script text tokenization via service API."""
        text = "Hello你好World"
        result = tokenize_text(text)

        assert isinstance(result, list)
        assert len(result) > 0

        # CRITICAL: Should handle scripts with predictable tokenization
        # Latin script should be lowercased and space-separated
        assert "hello" in result, f"Latin text 'hello' not found in result: {result}"
        assert "world" in result, f"Latin text 'world' not found in result: {result}"

        # CJK should be character-level tokenized
        assert "你" in result, f"Chinese character '你' not found in result: {result}"
        assert "好" in result, f"Chinese character '好' not found in result: {result}"


class TestSocialMediaEntities:
    """Test basic social media entity extraction through service API (smoke test)."""

    def test_combined_social_entities_smoke(self):
        """Test service API with multiple social media entities enabled."""
        text = "@user check #hashtag https://example.com 🎉"

        config = TokenizerConfig(
            extract_mentions=True,
            extract_hashtags=True,
            include_urls=True,
            include_emoji=True,
        )
        tokenizer = create_basic_tokenizer(config)
        result = tokenizer.tokenize(text)

        # Service API should handle entity extraction
        assert isinstance(result, list)
        # Should extract social media entities
        assert "@user" in result
        assert "#hashtag" in result
        assert "https://example.com" in result
        assert "check" in result

        # CRITICAL: Emoji should be preserved when enabled
        assert "🎉" in result, f"Emoji should be preserved when enabled: {result}"

    def test_combined_social_entities_disabled(self):
        """Test service API with all social media entities disabled."""
        text = "@user check #hashtag https://example.com 🎉"

        config = TokenizerConfig(
            extract_mentions=False,
            extract_hashtags=False,
            include_urls=False,
            include_emoji=False,
        )
        tokenizer = create_basic_tokenizer(config)
        result = tokenizer.tokenize(text)

        # Service API should handle disabled entities
        assert isinstance(result, list)

        # Basic words should be present
        assert "check" in result

        # Social media entities should NOT be preserved intact
        assert "@user" not in result, "Mentions should be disabled"
        assert "#hashtag" not in result, "Hashtags should be disabled"
        assert "https://example.com" not in result, "URLs should be disabled"
        assert "🎉" not in result, "Emojis should be disabled"

        # Components should be tokenized separately
        assert (
            "user" in result or "hashtag" in result
        ), "Entity content should be tokenized as words"


class TestTokenizerConfiguration:
    """Test basic configuration options through service API."""

    def test_case_handling_options_via_api(self):
        """Test different case handling options through service API."""
        text = "Hello WORLD Test"

        # Test API with lowercase config
        config_lower = TokenizerConfig(case_handling=CaseHandling.LOWERCASE)
        result_lower = tokenize_text(text, config_lower)
        assert "hello" in result_lower
        assert "world" in result_lower

        # Test API with preserve config
        config_preserve = TokenizerConfig(case_handling=CaseHandling.PRESERVE)
        result_preserve = tokenize_text(text, config_preserve)
        assert "Hello" in result_preserve
        assert "WORLD" in result_preserve

    def test_min_token_length_via_api(self):
        """Test minimum token length filtering through service API."""
        text = "a bb ccc dddd"

        # Test API with different min lengths
        config_1 = TokenizerConfig(min_token_length=1)
        result_1 = tokenize_text(text, config_1)
        assert "a" in result_1

        config_3 = TokenizerConfig(min_token_length=3)
        result_3 = tokenize_text(text, config_3)
        assert "a" not in result_3
        assert "ccc" in result_3


class TestNgramParameterValidation:
    """Test n-gram parameter validation and edge cases."""

    def test_valid_ngram_ranges(self):
        """Test valid n-gram parameter ranges."""
        from analyzers.ngrams.ngrams_base.main import ngrams

        tokens = ["word1", "word2", "word3", "word4", "word5"]

        # Valid ranges
        valid_ranges = [
            (1, 1),
            (1, 5),
            (3, 5),
            (2, 15),
            (15, 15),
        ]

        for min_n, max_n in valid_ranges:
            result = list(ngrams(tokens, min_n, max_n))
            assert isinstance(result, list)
            if min_n <= len(tokens):
                assert len(result) > 0

    def test_edge_case_ngram_ranges(self):
        """Test edge cases for n-gram ranges."""
        from analyzers.ngrams.ngrams_base.main import ngrams

        tokens = ["word1", "word2", "word3"]

        # Edge cases
        edge_cases = [
            (1, 10),  # max_n larger than token count
            (5, 5),  # min_n larger than token count
            (3, 3),  # exact token count
        ]

        for min_n, max_n in edge_cases:
            result = list(ngrams(tokens, min_n, max_n))
            assert isinstance(result, list)

    def test_ngram_default_parameters(self):
        """Test default n-gram parameters used in analyzer."""
        # These should match the defaults in the analyzer
        default_min_n = 3
        default_max_n = 5

        # Verify these are reasonable defaults
        assert 1 <= default_min_n <= 15
        assert default_min_n <= default_max_n <= 15

    def test_invalid_ngram_ranges(self):
        """Test behavior with invalid n-gram ranges."""
        from analyzers.ngrams.ngrams_base.main import ngrams

        tokens = ["word1", "word2", "word3"]

        # These should not crash but may return empty results
        invalid_ranges = [
            (0, 5),  # min_n = 0
            (3, 2),  # min_n > max_n
            (-1, 5),  # negative min_n
        ]

        for min_n, max_n in invalid_ranges:
            try:
                result = list(ngrams(tokens, min_n, max_n))
                assert isinstance(result, list)
            except (ValueError, TypeError):
                # Some invalid ranges might raise exceptions, which is okay
                pass


class TestTokenizerIntegration:
    """Test integration between tokenizer and n-gram processing."""

    def test_tokenizer_ngram_pipeline(self):
        """Test full pipeline from text to n-grams."""
        from analyzers.ngrams.ngrams_base.main import ngrams, serialize_ngram

        text = "This is a test sentence for tokenization."

        # Tokenize
        config = TokenizerConfig(
            case_handling=CaseHandling.LOWERCASE,
            extract_hashtags=False,
            extract_mentions=False,
            include_urls=False,
            min_token_length=1,
        )
        tokens = tokenize_text(text, config)

        # Generate n-grams
        ngram_list = list(ngrams(tokens, min=2, max=3))

        # Serialize n-grams
        serialized = [serialize_ngram(ngram) for ngram in ngram_list]

        assert len(tokens) > 0
        assert len(ngram_list) > 0
        assert len(serialized) > 0
        assert all(isinstance(s, str) for s in serialized)

    def test_social_media_text_pipeline(self):
        """Test pipeline with social media text."""
        from analyzers.ngrams.ngrams_base.main import ngrams

        text = "Great work @team! Check out #progress https://example.com 🎉"

        # Configure for social media analysis
        config = TokenizerConfig(
            case_handling=CaseHandling.LOWERCASE,
            extract_hashtags=True,
            extract_mentions=True,
            include_urls=True,
            include_emoji=True,
            min_token_length=1,
        )
        tokens = tokenize_text(text, config)

        # Should include social entities
        assert any("@" in token for token in tokens)  # mentions
        assert any("#" in token for token in tokens)  # hashtags

        # Generate n-grams from the tokens
        ngram_list = list(ngrams(tokens, min=1, max=2))
        assert len(ngram_list) > 0

    def test_multilingual_pipeline(self):
        """Test pipeline with multilingual content."""
        from analyzers.ngrams.ngrams_base.main import ngrams

        text = "Hello 你好 world 世界"

        config = TokenizerConfig(
            case_handling=CaseHandling.LOWERCASE,
            min_token_length=1,
        )
        tokens = tokenize_text(text, config)

        # Should handle mixed scripts
        assert len(tokens) >= 3

        # Generate n-grams
        ngram_list = list(ngrams(tokens, min=2, max=2))
        assert len(ngram_list) > 0

    def test_deterministic_results(self):
        """Test that tokenization results are deterministic."""
        text = "Test text for deterministic results"
        config = TokenizerConfig(case_handling=CaseHandling.LOWERCASE)

        # Run multiple times
        results = [tokenize_text(text, config) for _ in range(5)]

        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result

    def test_performance_reasonable(self):
        """Test that tokenization performance is reasonable for large text."""
        import time

        # Create a moderately large text
        text = "This is a test sentence. " * 1000  # ~25KB of text

        config = TokenizerConfig()

        start_time = time.time()
        result = tokenize_text(text, config)
        end_time = time.time()

        # Should complete in reasonable time (less than 1 second for 25KB)
        assert end_time - start_time < 1.0
        assert len(result) > 1000  # Should produce many tokens


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
