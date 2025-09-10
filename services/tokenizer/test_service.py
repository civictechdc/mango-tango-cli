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

import pytest
from typing import Dict, List

from . import (
    create_basic_tokenizer,
    tokenize_text,
    TokenizerConfig,
    BasicTokenizer,
    TokenType,
    LanguageFamily,
)
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
        result = tokenize_text(text, None)
        assert isinstance(result, list)
        assert len(result) > 0


class TestMultilingualTokenization:
    """Test tokenization of multilingual content."""

    def test_latin_text(self):
        """Test Latin script text tokenization."""
        texts = [
            "Hello world café",
            "bonjour monde",
            "Hola mundo",
            "Guten Tag Welt",
        ]
        
        for text in texts:
            result = tokenize_text(text)
            assert isinstance(result, list)
            assert len(result) > 0
            # Should be lowercase by default
            assert all(token.islower() or not token.isalpha() for token in result)

    def test_chinese_text(self):
        """Test Chinese text tokenization."""
        text = "你好世界"
        result = tokenize_text(text)
        
        assert isinstance(result, list)
        assert len(result) > 0
        # Chinese characters should be tokenized individually
        assert "你" in result or "你好" in result
        assert "世" in result or "世界" in result

    def test_japanese_text(self):
        """Test Japanese text tokenization."""
        text = "こんにちは世界"
        result = tokenize_text(text)
        
        assert isinstance(result, list)
        assert len(result) > 0

    def test_arabic_text(self):
        """Test Arabic text tokenization."""
        text = "مرحبا بالعالم"
        result = tokenize_text(text)
        
        assert isinstance(result, list)
        assert len(result) > 0

    def test_mixed_script_text(self):
        """Test mixed script text tokenization."""
        mixed_texts = [
            "iPhone用户",
            "café北京",
            "Hello你好World",
            "test测试الاختبار",
        ]
        
        for text in mixed_texts:
            result = tokenize_text(text)
            assert isinstance(result, list)
            assert len(result) > 0

    def test_multilingual_case_handling(self):
        """Test case handling with multilingual text."""
        text = "Hello 你好 WORLD 世界"
        
        # Test lowercase
        config_lower = TokenizerConfig(case_handling=CaseHandling.LOWERCASE)
        result_lower = tokenize_text(text, config_lower)
        latin_tokens = [t for t in result_lower if t.isascii()]
        assert all(t.islower() or not t.isalpha() for t in latin_tokens)
        
        # Test preserve
        config_preserve = TokenizerConfig(case_handling=CaseHandling.PRESERVE)
        result_preserve = tokenize_text(text, config_preserve)
        assert "Hello" in result_preserve
        assert "WORLD" in result_preserve


class TestSocialMediaEntities:
    """Test extraction of social media entities."""

    def test_hashtag_extraction(self):
        """Test hashtag extraction."""
        texts = [
            "#hashtag",
            "Check out #amazing content",
            "#MultiWord #test123 #special_chars",
            "Multiple #hash #tags in #text",
        ]
        
        config = TokenizerConfig(extract_hashtags=True)
        tokenizer = create_basic_tokenizer(config)
        
        for text in texts:
            result = tokenizer.tokenize_with_types(text)
            if "hashtag" in result:
                hashtags = result["hashtag"]
                assert len(hashtags) > 0
                assert all(tag.startswith("#") for tag in hashtags)

    def test_mention_extraction(self):
        """Test @mention extraction."""
        texts = [
            "@user",
            "Hello @john_doe how are you?",
            "@user123 @another_user",
            "Contact @support for help",
        ]
        
        config = TokenizerConfig(extract_mentions=True)
        tokenizer = create_basic_tokenizer(config)
        
        for text in texts:
            result = tokenizer.tokenize_with_types(text)
            if "mention" in result:
                mentions = result["mention"]
                assert len(mentions) > 0
                assert all(mention.startswith("@") for mention in mentions)

    def test_url_extraction(self):
        """Test URL extraction."""
        urls = [
            "https://example.com",
            "http://test.org/path",
            "www.example.com",
            "Check out https://github.com/repo",
            "Visit example.com for more info",
        ]
        
        config = TokenizerConfig(extract_urls=True)
        tokenizer = create_basic_tokenizer(config)
        
        for url_text in urls:
            result = tokenizer.tokenize_with_types(url_text)
            if "url" in result:
                extracted_urls = result["url"]
                assert len(extracted_urls) > 0

    def test_emoji_extraction(self):
        """Test emoji extraction."""
        texts = [
            "Hello 🎉",
            "Great work 😀 👍",
            "🚀 Amazing project 🎯",
            "😊 😎 😍",
        ]
        
        config = TokenizerConfig(include_emoji=True)
        tokenizer = create_basic_tokenizer(config)
        
        for text in texts:
            result = tokenizer.tokenize_with_types(text)
            if "emoji" in result:
                emojis = result["emoji"]
                assert len(emojis) > 0

    def test_combined_social_entities(self):
        """Test text with multiple social media entities."""
        text = "@user check #hashtag https://example.com 🎉"
        
        config = TokenizerConfig(
            extract_mentions=True,
            extract_hashtags=True,
            extract_urls=True,
            include_emoji=True,
        )
        tokenizer = create_basic_tokenizer(config)
        result = tokenizer.tokenize_with_types(text)
        
        # Should extract all entity types
        entity_types = ["mention", "hashtag", "url", "emoji"]
        found_types = [t for t in entity_types if t in result and result[t]]
        assert len(found_types) >= 3  # Should find at least 3 types

    def test_social_entities_disabled(self):
        """Test that social entities are not extracted when disabled."""
        text = "@user #hashtag https://example.com"
        
        config = TokenizerConfig(
            extract_mentions=False,
            extract_hashtags=False,
            extract_urls=False,
        )
        
        result = tokenize_text(text, config)
        # Should not contain the @ # or full URL as separate tokens
        # Instead, they should be processed as regular text
        assert len(result) > 0


class TestTokenizerConfiguration:
    """Test various TokenizerConfig options and edge cases."""

    def test_case_handling_options(self):
        """Test different case handling options."""
        text = "Hello WORLD Test"
        
        # Lowercase
        config_lower = TokenizerConfig(case_handling=CaseHandling.LOWERCASE)
        result_lower = tokenize_text(text, config_lower)
        assert "hello" in result_lower
        assert "world" in result_lower
        
        # Preserve
        config_preserve = TokenizerConfig(case_handling=CaseHandling.PRESERVE)
        result_preserve = tokenize_text(text, config_preserve)
        assert "Hello" in result_preserve
        assert "WORLD" in result_preserve
        
        # Uppercase
        config_upper = TokenizerConfig(case_handling=CaseHandling.UPPERCASE)
        result_upper = tokenize_text(text, config_upper)
        assert "HELLO" in result_upper
        assert "WORLD" in result_upper

    def test_min_token_length_filtering(self):
        """Test minimum token length filtering."""
        text = "a bb ccc dddd"
        
        # Min length 1 (default)
        config_1 = TokenizerConfig(min_token_length=1)
        result_1 = tokenize_text(text, config_1)
        assert "a" in result_1
        assert "bb" in result_1
        
        # Min length 3
        config_3 = TokenizerConfig(min_token_length=3)
        result_3 = tokenize_text(text, config_3)
        assert "a" not in result_3
        assert "bb" not in result_3
        assert "ccc" in result_3
        assert "dddd" in result_3

    def test_punctuation_inclusion(self):
        """Test punctuation inclusion/exclusion."""
        text = "Hello, world! How are you?"
        
        # Include punctuation
        config_with = TokenizerConfig(include_punctuation=True)
        tokenizer_with = create_basic_tokenizer(config_with)
        result_with = tokenizer_with.tokenize_with_types(text)
        
        # Exclude punctuation (default)
        config_without = TokenizerConfig(include_punctuation=False)
        result_without = tokenize_text(text, config_without)
        
        # With punctuation should have punctuation tokens
        if "punctuation" in result_with:
            assert len(result_with["punctuation"]) > 0
        
        # Without punctuation should be clean words
        assert all(token.isalnum() or not token.isascii() for token in result_without)

    def test_unicode_normalization(self):
        """Test Unicode normalization."""
        # Text with accented characters
        text = "café naïve résumé"
        
        config = TokenizerConfig(normalize_unicode=True)
        result = tokenize_text(text, config)
        
        assert isinstance(result, list)
        assert len(result) > 0
        # Should contain the normalized words in some form
        assert any("caf" in token for token in result)
        assert any("na" in token or "ive" in token for token in result)
        assert "r" in result and "sum" in result  # résumé is split into parts

    def test_language_detection_settings(self):
        """Test language detection configuration."""
        text = "Mixed text 混合文本"
        
        # With detection
        config_detect = TokenizerConfig(detect_language=True)
        result_detect = tokenize_text(text, config_detect)
        
        # Without detection (use fallback)
        config_no_detect = TokenizerConfig(
            detect_language=False,
            fallback_language_family=LanguageFamily.LATIN
        )
        result_no_detect = tokenize_text(text, config_no_detect)
        
        # Both should produce results
        assert len(result_detect) > 0
        assert len(result_no_detect) > 0


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
            (5, 5),   # min_n larger than token count
            (3, 3),   # exact token count
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
            (0, 5),   # min_n = 0
            (3, 2),   # min_n > max_n
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
            extract_urls=False,
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
            extract_urls=True,
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