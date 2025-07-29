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
