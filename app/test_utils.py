"""
Tests for app/utils.py tokenization engine.

This test suite validates:
- Space-separated vs non-space-separated text detection
- Social media entity preservation
- Mixed script handling
- Edge cases and error conditions
- Performance with various text types
"""

from typing import List

import polars as pl
import pytest

from .utils import is_space_separated, tokenize_text


class TestIsSpaceSeparated:
    """Test the is_space_separated function for various script types."""

    def test_latin_script(self):
        """Test Latin script text is detected as space-separated."""
        text = "Hello world this is English text"
        assert is_space_separated(text) is True

    def test_cyrillic_script(self):
        """Test Cyrillic script text is detected as space-separated."""
        text = "Привет мир это русский текст"
        assert is_space_separated(text) is True

    def test_arabic_script(self):
        """Test Arabic script text is detected as space-separated."""
        text = "مرحبا بالعالم هذا نص عربي"
        assert is_space_separated(text) is True

    def test_chinese_script(self):
        """Test Chinese script text is detected as non-space-separated."""
        text = "你好世界这是中文文本"
        assert is_space_separated(text) is False

    def test_japanese_script(self):
        """Test Japanese script text is detected as non-space-separated."""
        text = "こんにちは世界これは日本語のテキストです"
        assert is_space_separated(text) is False

    def test_thai_script(self):
        """Test Thai script text is detected as non-space-separated."""
        text = "สวัสดีโลกนี่คือข้อความไทย"
        assert is_space_separated(text) is False

    def test_mixed_scripts_majority_latin(self):
        """Test mixed scripts with majority Latin characters."""
        text = "Hello 你好 world this is mostly English"
        assert is_space_separated(text) is True

    def test_mixed_scripts_majority_chinese(self):
        """Test mixed scripts with majority Chinese characters."""
        text = "iPhone用户可以使用这个应用程序在手机上"
        assert is_space_separated(text) is False

    def test_empty_text(self):
        """Test empty text defaults to space-separated."""
        assert is_space_separated("") is True
        assert is_space_separated("   ") is True

    def test_no_script_characters(self):
        """Test text with no specific script characters."""
        text = "123 456 !@# $%^"
        assert is_space_separated(text) is True

    def test_polars_expression(self):
        """Test is_space_separated works with polars expressions."""
        df = pl.DataFrame(
            {"text": ["Hello world", "你好世界", "Привет мир", "こんにちは", ""]}
        )

        result = df.with_columns(
            [is_space_separated(pl.col("text")).alias("is_space_sep")]
        )

        expected = [True, False, True, False, True]
        assert result["is_space_sep"].to_list() == expected


class TestTokenizeText:
    """Test the tokenize_text function for various text types and edge cases."""

    def test_simple_english_text(self):
        """Test basic English text tokenization."""
        df = pl.DataFrame({"text": ["Hello world this is a test"]}).lazy()

        result = tokenize_text(df, "text").collect()
        tokens = result["tokens"][0].to_list()

        expected = ["hello", "world", "this", "is", "a", "test"]
        assert tokens == expected

    def test_social_media_entities(self):
        """Test preservation of social media entities."""
        df = pl.DataFrame(
            {"text": ["Check out https://example.com and @username #hashtag"]}
        ).lazy()

        result = tokenize_text(df, "text").collect()
        tokens = result["tokens"][0].to_list()

        # URLs, mentions, and hashtags should be preserved as-is
        assert "https://example.com" in tokens
        assert "@username" in tokens
        assert "#hashtag" in tokens
        assert "check" in tokens
        assert "out" in tokens
        assert "and" in tokens

    def test_chinese_text(self):
        """Test Chinese text character-level tokenization."""
        df = pl.DataFrame({"text": ["这是中文测试"]}).lazy()

        result = tokenize_text(df, "text").collect()
        tokens = result["tokens"][0].to_list()

        # Chinese text should be split into individual characters
        expected = ["这", "是", "中", "文", "测", "试"]
        assert tokens == expected

    def test_chinese_text_with_spaces(self):
        """Test Chinese text with spaces (should still split into characters)."""
        df = pl.DataFrame({"text": ["你好 世界 这是 中文"]}).lazy()

        result = tokenize_text(df, "text").collect()
        tokens = result["tokens"][0].to_list()

        # Should split into individual characters, not space-separated words
        expected = ["你", "好", "世", "界", "这", "是", "中", "文"]
        assert tokens == expected

    def test_url_with_cjk_text(self):
        """Test URL preservation with surrounding CJK characters."""
        df = pl.DataFrame({"text": ["访问https://example.com网站"]}).lazy()

        result = tokenize_text(df, "text").collect()
        tokens = result["tokens"][0].to_list()

        # URL should be preserved, CJK characters should be split individually
        expected = ["访", "问", "https://example.com", "网", "站"]
        assert tokens == expected

    def test_mixed_script_text(self):
        """Test mixed script text handling."""
        df = pl.DataFrame({"text": ["iPhone用户 can use this app"]}).lazy()

        result = tokenize_text(df, "text").collect()
        tokens = result["tokens"][0].to_list()

        # Should contain both the mixed token and separate words
        assert "iphone用户" in tokens  # Mixed script token (lowercased)
        assert "can" in tokens
        assert "use" in tokens
        assert "this" in tokens
        assert "app" in tokens

    def test_whitespace_normalization(self):
        """Test that multiple whitespace is normalized."""
        df = pl.DataFrame({"text": ["hello    world\t\ttest\n\nmore   spaces"]}).lazy()

        result = tokenize_text(df, "text").collect()
        tokens = result["tokens"][0].to_list()

        expected = ["hello", "world", "test", "more", "spaces"]
        assert tokens == expected

    def test_empty_text(self):
        """Test handling of empty text."""
        df = pl.DataFrame({"text": ["", "   ", "\t\n"]}).lazy()

        result = tokenize_text(df, "text").collect()

        # All should result in empty token lists
        assert result["tokens"][0].to_list() == []
        assert result["tokens"][1].to_list() == []
        assert result["tokens"][2].to_list() == []

    def test_punctuation_handling(self):
        """Test handling of punctuation."""
        df = pl.DataFrame({"text": ["Hello, world! How are you?"]}).lazy()

        result = tokenize_text(df, "text").collect()
        tokens = result["tokens"][0].to_list()

        # Punctuation should be included with words (except for social media entities)
        expected = ["hello,", "world!", "how", "are", "you?"]
        assert tokens == expected

    def test_case_preservation_for_urls(self):
        """Test that URLs preserve their case."""
        df = pl.DataFrame({"text": ["Visit HTTPS://Example.COM/Path today"]}).lazy()

        result = tokenize_text(df, "text").collect()
        tokens = result["tokens"][0].to_list()

        assert "HTTPS://Example.COM/Path" in tokens
        assert "visit" in tokens
        assert "today" in tokens

    def test_multiple_messages(self):
        """Test tokenization of multiple messages."""
        df = pl.DataFrame(
            {
                "text": [
                    "First message here",
                    "Second message with @mention",
                    "Third message 你好世界",
                ]
            }
        ).lazy()

        result = tokenize_text(df, "text").collect()

        assert len(result) == 3
        assert result["tokens"][0].to_list() == ["first", "message", "here"]
        assert "@mention" in result["tokens"][1].to_list()
        # CJK characters should be split individually for consistency
        tokens_2 = result["tokens"][2].to_list()
        assert "你" in tokens_2
        assert "好" in tokens_2
        assert "世" in tokens_2
        assert "界" in tokens_2

    def test_invalid_input_types(self):
        """Test error handling for invalid input types."""
        # Non-LazyFrame input
        with pytest.raises(TypeError, match="Expected polars LazyFrame"):
            tokenize_text("not a dataframe", "text")

        # Non-string column name
        df = pl.DataFrame({"text": ["test"]}).lazy()
        with pytest.raises(TypeError, match="text_column must be a string"):
            tokenize_text(df, 123)

    def test_nonexistent_column(self):
        """Test error handling for nonexistent column."""
        df = pl.DataFrame({"other_col": ["test"]}).lazy()

        # This should raise an error when the lazy frame is executed
        with pytest.raises(Exception):  # Will be a polars error about missing column
            tokenize_text(df, "nonexistent_column").collect()

    def test_special_characters(self):
        """Test handling of various special characters."""
        df = pl.DataFrame(
            {"text": ["Text with émojis 😀 and àccénts café naïve"]}
        ).lazy()

        result = tokenize_text(df, "text").collect()
        tokens = result["tokens"][0].to_list()

        # Should handle accented characters properly
        assert "émojis" in tokens
        assert "😀" in tokens
        assert "àccénts" in tokens
        assert "café" in tokens
        assert "naïve" in tokens

    def test_performance_with_large_text(self):
        """Test tokenization performance with larger text."""
        large_text = " ".join(["word"] * 1000)
        df = pl.DataFrame({"text": [large_text]}).lazy()

        result = tokenize_text(df, "text").collect()
        tokens = result["tokens"][0].to_list()

        assert len(tokens) == 1000
        assert all(token == "word" for token in tokens)

    def test_social_media_entity_variations(self):
        """Test various social media entity formats."""
        df = pl.DataFrame(
            {
                "text": [
                    "Check http://short.ly and https://secure.example.com/path?query=123 plus @user_name and #CamelCaseTag"
                ]
            }
        ).lazy()

        result = tokenize_text(df, "text").collect()
        tokens = result["tokens"][0].to_list()

        # All URL formats should be preserved
        assert "http://short.ly" in tokens
        assert "https://secure.example.com/path?query=123" in tokens
        assert "@user_name" in tokens
        assert "#CamelCaseTag" in tokens

    def test_pure_punctuation_filtering(self):
        """Test that pure punctuation tokens are filtered out."""
        df = pl.DataFrame({
            "text": [
                "!!! ... ,,, ??? ::: ;;;",  # Pure punctuation only
                "Hello!!! World... Test,,,",  # Mixed content 
                "。。。 ！！！ ？？？",  # CJK punctuation
                "((())) [[[]]] {{{}}}"  # Brackets and braces
            ]
        }).lazy()

        result = tokenize_text(df, "text").collect()
        
        # First row: pure punctuation should be filtered to empty list
        tokens_0 = result["tokens"][0].to_list()
        assert tokens_0 == [], f"Expected empty tokens for pure punctuation, got: {tokens_0}"
        
        # Second row: mixed content should preserve words but filter pure punctuation  
        tokens_1 = result["tokens"][1].to_list()
        # Should contain words but not pure punctuation sequences
        word_tokens = [token for token in tokens_1 if any(c.isalnum() for c in token)]
        assert len(word_tokens) >= 2, f"Expected words to be preserved, got: {tokens_1}"
        
        # Third row: CJK punctuation should also be filtered
        tokens_2 = result["tokens"][2].to_list()
        assert tokens_2 == [], f"Expected CJK punctuation to be filtered, got: {tokens_2}"
        
        # Fourth row: brackets and braces should be filtered
        tokens_3 = result["tokens"][3].to_list()
        assert tokens_3 == [], f"Expected brackets/braces to be filtered, got: {tokens_3}"

    def test_punctuation_edge_cases_preserved(self):
        """Test that legitimate tokens with punctuation are preserved."""
        df = pl.DataFrame({
            "text": [
                "Visit https://example.com/path?query=test&param=1 today",
                "Contact @user123 and check #hashtag!",  
                "Words like don't, can't, won't should work",
                "Email test@example.com or visit sub.domain.com"
            ]
        }).lazy()

        result = tokenize_text(df, "text").collect()
        
        # URLs with punctuation should be preserved
        tokens_0 = result["tokens"][0].to_list() 
        assert "https://example.com/path?query=test&param=1" in tokens_0
        
        # Social media entities should be preserved
        tokens_1 = result["tokens"][1].to_list()
        assert "@user123" in tokens_1
        assert "#hashtag" in tokens_1
        
        # Contractions should be preserved
        tokens_2 = result["tokens"][2].to_list()
        contraction_found = any("'" in token for token in tokens_2)
        assert contraction_found, f"Expected contractions to be preserved, got: {tokens_2}"
        
        # Email-like patterns should work (even if not in URL pattern)
        tokens_3 = result["tokens"][3].to_list()
        email_or_domain_found = any("." in token and len(token) > 1 for token in tokens_3)
        assert email_or_domain_found, f"Expected domain/email patterns, got: {tokens_3}"

    def test_punctuation_with_multilingual_text(self):
        """Test punctuation filtering with various languages."""
        df = pl.DataFrame({
            "text": [
                "English... 中文。。。 한국어!!! русский???",
                "Mixed iPhone用户!!! can use this.",
                "URL https://例え.com/パス works fine."
            ]
        }).lazy()

        result = tokenize_text(df, "text").collect()
        
        # Should preserve language text but filter pure punctuation
        tokens_0 = result["tokens"][0].to_list()
        has_text = any(any(c.isalnum() or ord(c) > 127 for c in token) for token in tokens_0)
        assert has_text, f"Expected multilingual text to be preserved, got: {tokens_0}"
        
        # Mixed script tokens should be preserved
        tokens_1 = result["tokens"][1].to_list()
        assert any("iphone" in token.lower() for token in tokens_1), f"Mixed script not found: {tokens_1}"
        
        # International domain names: protocol should be preserved, but non-ASCII parts will be tokenized separately
        tokens_2 = result["tokens"][2].to_list()
        https_found = any("https:" in token for token in tokens_2)
        japanese_chars_found = any(ord(c) > 127 for token in tokens_2 for c in token if c.isalpha())
        assert https_found, f"HTTPS protocol not preserved: {tokens_2}"
        assert japanese_chars_found, f"Japanese characters not preserved: {tokens_2}"

    def test_ngram_punctuation_regression(self):
        """Test that n-gram analysis won't generate pure punctuation n-grams."""
        df = pl.DataFrame({
            "text": [
                "Normal text with... excessive punctuation!!! And more???",
                "!!! ... ,,, !!! ... ,,,", # Pattern that previously generated bad n-grams
                "Good content. Bad punctuation!!!"
            ]
        }).lazy()

        result = tokenize_text(df, "text").collect()
        
        # Collect all tokens and ensure no pure punctuation tokens exist
        all_tokens = []
        for token_list in result["tokens"].to_list():
            all_tokens.extend(token_list)
        
        # No token should be pure punctuation
        pure_punctuation_tokens = [
            token for token in all_tokens 
            if token and all(not c.isalnum() and ord(c) < 256 for c in token)
            and not token.startswith(('http', '@', '#'))  # Exclude legitimate patterns
        ]
        
        assert pure_punctuation_tokens == [], f"Found pure punctuation tokens: {pure_punctuation_tokens}"
        
        # Should still have legitimate content
        content_tokens = [token for token in all_tokens if any(c.isalnum() for c in token)]
        assert len(content_tokens) > 0, "No content tokens found - over-filtering occurred"

    def test_complex_urls_with_punctuation(self):
        """Test complex URLs with various punctuation marks are preserved."""
        df = pl.DataFrame({
            "text": ["Check https://example.com/path?query=1&param=test#anchor and http://sub.domain.co.uk/"]
        }).lazy()

        result = tokenize_text(df, "text").collect()
        tokens = result["tokens"][0].to_list()

        # Complex URLs should be preserved exactly
        assert "https://example.com/path?query=1&param=test#anchor" in tokens
        assert "http://sub.domain.co.uk/" in tokens
        assert "check" in tokens
        assert "and" in tokens

    def test_symbol_filtering_specificity(self):
        """Test that only problematic symbols are filtered, not meaningful ones."""
        df = pl.DataFrame({
            "text": [
                "Math symbols === +++ --- should be filtered",
                "But emojis 😀😎🎉 should be preserved",
                "Currency symbols $100 €50 should be filtered"
            ]
        }).lazy()

        result = tokenize_text(df, "text").collect()
        
        # Math symbols should be filtered
        tokens_0 = result["tokens"][0].to_list()
        math_symbols_found = any(token in ["===", "+++", "---"] for token in tokens_0)
        assert not math_symbols_found, f"Math symbols not filtered: {tokens_0}"
        assert "math" in tokens_0
        assert "symbols" in tokens_0
        
        # Emojis should be preserved  
        tokens_1 = result["tokens"][1].to_list()
        emoji_found = any(ord(c) > 127 and not c.isalpha() for token in tokens_1 for c in token)
        assert emoji_found, f"Emojis not preserved: {tokens_1}"
        
        # Currency symbols should be filtered, numbers preserved as individual digits
        tokens_2 = result["tokens"][2].to_list()
        currency_symbols_found = any(token in ["$", "€"] for token in tokens_2)
        assert not currency_symbols_found, f"Currency symbols not filtered: {tokens_2}"
        # Numbers may be tokenized as individual digits or groups
        has_numbers = any(c.isdigit() for token in tokens_2 for c in token)
        assert has_numbers, f"Numbers not preserved: {tokens_2}"

    def test_real_world_social_media_example(self):
        """Test realistic social media content with mixed punctuation."""
        df = pl.DataFrame({
            "text": ["OMG!!! Check this out: https://tinyurl.com/demo @everyone #viral #trending... So cool!!!"]
        }).lazy()

        result = tokenize_text(df, "text").collect()
        tokens = result["tokens"][0].to_list()

        # Should preserve content but filter pure punctuation
        assert "https://tinyurl.com/demo" in tokens
        assert "@everyone" in tokens  
        assert "#viral" in tokens
        assert "#trending" in tokens
        assert any("omg" in token.lower() for token in tokens)
        assert any("check" in token.lower() for token in tokens)
        assert any("cool" in token.lower() for token in tokens)

    def test_comprehensive_punctuation_categories(self):
        """Test various Unicode punctuation categories are properly filtered.""" 
        df = pl.DataFrame({
            "text": [
                "Brackets: ()[]{}  Quotes: \"'`  Dashes: -–—  Math: +=*÷",
                "CJK punct: 。！？，：；  Symbols: @#$%^&*  Mixed: word!!! ...word"
            ]
        }).lazy()

        result = tokenize_text(df, "text").collect()
        
        # First row: various punctuation types
        tokens_0 = result["tokens"][0].to_list() 
        content_words = [token for token in tokens_0 if any(c.isalpha() for c in token)]
        # Words may include attached punctuation (like "brackets:")
        word_stems = [w.rstrip(':').lower() for w in content_words]
        assert "brackets" in word_stems
        assert "quotes" in word_stems
        
        # Second row: mixed content  
        tokens_1 = result["tokens"][1].to_list()
        # Should preserve mixed punctuation with letters but filter pure punctuation
        mixed_tokens = [token for token in tokens_1 if any(c.isalpha() for c in token)]
        assert len(mixed_tokens) >= 2, f"Expected mixed alpha tokens: {tokens_1}"


class TestTokenizationIntegration:
    """Integration tests for tokenization engine with n-gram analysis."""

    def test_tokenization_with_ngram_pipeline(self):
        """Test that tokenization works well with n-gram generation."""
        df = pl.DataFrame(
            {
                "message_text": [
                    "This is a test message",
                    "Check out @user and https://example.com",
                    "Mixed text with 中文 content",
                ],
                "message_surrogate_id": [1, 2, 3],
            }
        ).lazy()

        # Apply tokenization
        tokenized = tokenize_text(df, "message_text").collect()

        # Verify all messages were tokenized
        assert len(tokenized) == 3
        assert all(isinstance(tokens.to_list(), list) for tokens in tokenized["tokens"])
        assert all(len(tokens.to_list()) > 0 for tokens in tokenized["tokens"])

        # Verify social media entities are preserved
        tokens_2 = tokenized["tokens"][1].to_list()
        assert any("@user" in str(token) for token in tokens_2)
        assert any("https://example.com" in str(token) for token in tokens_2)

    def test_empty_message_handling(self):
        """Test handling of datasets with empty messages."""
        df = pl.DataFrame(
            {
                "message_text": ["Valid message", "", "   ", "Another valid message"],
                "message_surrogate_id": [1, 2, 3, 4],
            }
        ).lazy()

        result = tokenize_text(df, "message_text").collect()

        # Should handle empty messages gracefully
        assert len(result) == 4
        assert len(result["tokens"][0].to_list()) > 0  # Valid message
        assert len(result["tokens"][1].to_list()) == 0  # Empty message
        assert len(result["tokens"][2].to_list()) == 0  # Whitespace-only message
        assert len(result["tokens"][3].to_list()) > 0  # Valid message
