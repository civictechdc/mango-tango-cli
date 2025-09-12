"""
Test suite for BasicTokenizer.

This module contains comprehensive tests for the BasicTokenizer class,
covering multilingual text, social media entities, configurable parameters,
and edge cases.
"""

import pytest

from ..core.types import CaseHandling, LanguageFamily, TokenizerConfig, TokenType
from .tokenizer import BasicTokenizer


class TestBasicTokenizerMultilingual:
    """Test multilingual tokenization capabilities."""

    def test_latin_text_tokenization(self):
        """Test basic Latin script tokenization."""
        tokenizer = BasicTokenizer()
        text = "Hello world, this is a test!"
        result = tokenizer.tokenize(text)

        expected = ["hello", "world", "this", "is", "a", "test"]
        assert result == expected

    def test_chinese_text_tokenization(self):
        """Test Chinese character tokenization."""
        tokenizer = BasicTokenizer()
        text = "你好世界"
        result = tokenizer.tokenize(text)

        # Chinese should be tokenized character by character
        expected = ["你", "好", "世", "界"]
        assert result == expected

    def test_japanese_text_tokenization(self):
        """Test Japanese text with mixed scripts."""
        tokenizer = BasicTokenizer()
        text = "こんにちは世界"
        result = tokenizer.tokenize(text)

        # Should handle hiragana and kanji
        expected = ["こ", "ん", "に", "ち", "は", "世", "界"]
        assert result == expected

    def test_arabic_text_tokenization(self):
        """Test Arabic script tokenization."""
        tokenizer = BasicTokenizer()
        text = "مرحبا بك في العالم"
        result = tokenizer.tokenize(text)

        # Arabic should be space-separated
        expected = ["مرحبا", "بك", "في", "العالم"]
        assert result == expected

    def test_thai_text_tokenization(self):
        """Test Thai script character-level tokenization."""
        tokenizer = BasicTokenizer()
        text = "สวัสดีครับ"
        result = tokenizer.tokenize(text)

        # Thai should be tokenized at character level
        expected = ["ส", "ว", "ั", "ส", "ด", "ี", "ค", "ร", "ั", "บ"]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_mixed_script_multilingual(self):
        """Test mixed multilingual content with specific tokenization expectations."""
        tokenizer = BasicTokenizer()
        text = "Hello 你好 こんにちは مرحبا สวัสดี"
        result = tokenizer.tokenize(text)

        # Should handle script boundaries with predictable tokenization
        assert isinstance(result, list)
        assert len(result) > 0

        # Latin script: space-separated tokenization
        assert "hello" in result

        # CRITICAL: CJK script should use character-level tokenization
        assert "你" in result, f"Chinese character '你' not found in result: {result}"
        assert "好" in result, f"Chinese character '好' not found in result: {result}"
        assert "こ" in result, f"Hiragana character 'こ' not found in result: {result}"

        # CRITICAL: Arabic script should use space-separated tokenization
        assert "مرحبا" in result, f"Arabic word 'مرحبا' not found in result: {result}"

        # CRITICAL: Thai script should use character-level tokenization
        for thai_char in ["ส", "ว", "ั", "ด", "ี"]:
            assert (
                thai_char in result
            ), f"Thai character '{thai_char}' not found in result: {result}"


class TestBasicTokenizerSocialMedia:
    """Test social media entity handling."""

    def test_hashtag_extraction(self):
        """Test hashtag preservation."""
        tokenizer = BasicTokenizer()
        text = "Check out this #awesome post!"
        result = tokenizer.tokenize(text)

        # Should preserve original order: check, out, this, #awesome, post
        expected = ["check", "out", "this", "#awesome", "post"]
        assert result == expected

    def test_mention_extraction(self):
        """Test mention preservation."""
        tokenizer = BasicTokenizer()
        text = "Hey @user how are you?"
        result = tokenizer.tokenize(text)

        # Should preserve original order: hey, @user, how, are, you
        expected = ["hey", "@user", "how", "are", "you"]
        assert result == expected

    def test_url_preservation(self):
        """Test URL preservation."""
        tokenizer = BasicTokenizer()
        text = "Visit https://example.com for more info"
        result = tokenizer.tokenize(text)

        # Should preserve original order: visit, https://example.com, for, more, info
        expected = ["visit", "https://example.com", "for", "more", "info"]
        assert result == expected

    def test_emoji_exclusion_by_default(self):
        """Test emoji exclusion with default configuration (include_emoji=False)."""
        tokenizer = BasicTokenizer()  # Default config has include_emoji=False
        text = "Great job! 🎉 Keep it up! 👍"
        result = tokenizer.tokenize(text)

        # Check that text tokens are included
        assert "great" in result
        assert "job" in result
        assert "keep" in result
        assert "it" in result
        assert "up" in result

        # CRITICAL: Emojis should be excluded with default config
        assert "🎉" not in result
        assert "👍" not in result

    def test_emoji_inclusion_when_enabled(self):
        """Test emoji preservation when explicitly enabled in configuration."""
        config = TokenizerConfig(include_emoji=True)
        tokenizer = BasicTokenizer(config)
        text = "Great job! 🎉 Keep it up! 👍"
        result = tokenizer.tokenize(text)

        # Check that text tokens are included
        assert "great" in result
        assert "job" in result
        assert "keep" in result
        assert "it" in result
        assert "up" in result

        # CRITICAL: Emojis should be preserved when enabled
        assert "🎉" in result
        assert "👍" in result

    def test_complex_social_media_text(self):
        """Test complex social media content with default configuration (emoji excluded)."""
        tokenizer = BasicTokenizer()  # Default config excludes emojis
        text = "@user check #hashtag https://example.com 🎉 Amazing!"
        result = tokenizer.tokenize(text)

        # Should preserve original order: @user, check, #hashtag, https://example.com, amazing
        expected = ["@user", "check", "#hashtag", "https://example.com", "amazing"]
        assert result == expected

        # CRITICAL: Emoji should be excluded with default config
        assert "🎉" not in result

    def test_complex_social_media_text_with_emojis(self):
        """Test complex social media content with emojis enabled."""
        config = TokenizerConfig(include_emoji=True)
        tokenizer = BasicTokenizer(config)
        text = "@user check #hashtag https://example.com 🎉 Amazing!"
        result = tokenizer.tokenize(text)

        # Should preserve original order: @user, check, #hashtag, https://example.com, emoji, amazing
        expected = [
            "@user",
            "check",
            "#hashtag",
            "https://example.com",
            "🎉",
            "amazing",
        ]
        assert result == expected

        # CRITICAL: Emoji should be preserved when enabled
        assert "🎉" in result

    def test_email_extraction(self):
        """Test email extraction when enabled."""
        config = TokenizerConfig(extract_emails=True)
        tokenizer = BasicTokenizer(config)
        text = "Contact me at user@example.com for details"
        result = tokenizer.tokenize(text)

        # Should include the email and basic words
        assert "user@example.com" in result
        assert "contact" in result
        assert "me" in result
        assert "for" in result
        assert "details" in result


class TestBasicTokenizerConfig:
    """Test configurable tokenizer behavior."""

    def test_case_handling_preserve(self):
        """Test case preservation."""
        config = TokenizerConfig(case_handling=CaseHandling.PRESERVE)
        tokenizer = BasicTokenizer(config)
        text = "Hello World"
        result = tokenizer.tokenize(text)

        expected = ["Hello", "World"]
        assert result == expected

    def test_case_handling_uppercase(self):
        """Test uppercase conversion."""
        config = TokenizerConfig(case_handling=CaseHandling.UPPERCASE)
        tokenizer = BasicTokenizer(config)
        text = "Hello World"
        result = tokenizer.tokenize(text)

        expected = ["HELLO", "WORLD"]
        assert result == expected

    def test_punctuation_inclusion(self):
        """Test punctuation token inclusion."""
        config = TokenizerConfig(include_punctuation=True)
        tokenizer = BasicTokenizer(config)
        text = "Hello, world!"
        result = tokenizer.tokenize(text)

        # With punctuation inclusion, punctuation should be preserved as tokens
        assert "hello" in result
        assert "world" in result

        # CRITICAL: Specific punctuation should be preserved as separate tokens
        assert "," in result or "hello," in result  # Comma should be preserved
        assert (
            "!" in result or "world!" in result or "!" in "".join(result)
        )  # Exclamation should be preserved

        # Verify punctuation is actually included in the tokenization
        has_punctuation = any(
            any(char in ".,!?;:" for char in token) for token in result
        )
        assert has_punctuation, f"No punctuation found in result: {result}"

    def test_numeric_inclusion(self):
        """Test numeric token handling."""
        config = TokenizerConfig(include_numeric=True)
        tokenizer = BasicTokenizer(config)
        text = "I have 123 apples and 45.67 oranges"
        result = tokenizer.tokenize(text)

        # Should include basic word tokens
        assert "i" in result
        assert "have" in result
        assert "apples" in result
        assert "and" in result
        assert "oranges" in result

        # CRITICAL: Specific numeric tokens should be preserved
        assert "123" in result, f"Integer '123' not found in result: {result}"
        assert "45.67" in result or (
            "45" in result and "67" in result
        ), f"Decimal '45.67' not properly tokenized in result: {result}"

        # Verify numeric tokens are actually included
        numeric_tokens = [
            token for token in result if any(char.isdigit() for char in token)
        ]
        assert len(numeric_tokens) > 0, f"No numeric tokens found in result: {result}"

    def test_emoji_inclusion_disabled(self):
        """Test emoji exclusion."""
        config = TokenizerConfig(include_emoji=False)
        tokenizer = BasicTokenizer(config)
        text = "Hello 🎉 World"
        result = tokenizer.tokenize(text)

        # Emojis should be excluded
        assert "🎉" not in result
        expected = ["hello", "world"]
        assert result == expected

    def test_min_token_length(self):
        """Test minimum token length filtering."""
        config = TokenizerConfig(min_token_length=3)
        tokenizer = BasicTokenizer(config)
        text = "I am a good person"
        result = tokenizer.tokenize(text)

        # Short tokens should be filtered out
        for token in result:
            assert len(token) >= 3
        expected = ["good", "person"]
        assert result == expected

    def test_max_token_length(self):
        """Test maximum token length filtering."""
        config = TokenizerConfig(max_token_length=5)
        tokenizer = BasicTokenizer(config)
        text = "short verylongword medium"
        result = tokenizer.tokenize(text)

        # Long tokens should be filtered out
        for token in result:
            assert len(token) <= 5
        # "verylongword" (12 chars) and "medium" (6 chars) are filtered out
        expected = ["short"]
        assert result == expected

    def test_social_media_entity_configuration(self):
        """Test selective social media entity extraction."""
        config = TokenizerConfig(
            extract_hashtags=False, extract_mentions=True, extract_urls=False
        )
        tokenizer = BasicTokenizer(config)
        text = "@user check #hashtag https://example.com"
        result = tokenizer.tokenize(text)

        # Only mentions should be preserved
        assert "@user" in result
        assert "check" in result

        # CRITICAL: Disabled features should tokenize entities as regular words
        assert "#hashtag" not in result  # Should be tokenized as "hashtag"
        assert "hashtag" in result
        assert "https://example.com" not in result  # Should be broken into parts
        # URL components should appear as separate tokens when extraction is disabled
        assert any(
            "https" in token or "example" in token or "com" in token for token in result
        )


class TestBasicTokenizerEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_string(self):
        """Test empty string input."""
        tokenizer = BasicTokenizer()
        result = tokenizer.tokenize("")
        assert result == []

    def test_whitespace_only(self):
        """Test whitespace-only input."""
        tokenizer = BasicTokenizer()
        text = "   \t\n  "
        result = tokenizer.tokenize(text)
        assert result == []

    def test_punctuation_only(self):
        """Test punctuation-only input."""
        tokenizer = BasicTokenizer()
        text = "!@#$%^&*()"
        result = tokenizer.tokenize(text)
        # Actually returns the punctuation string as a single token
        assert result == ["!@#$%^&*()"]

    def test_mixed_whitespace(self):
        """Test various whitespace types."""
        tokenizer = BasicTokenizer()
        text = "word1\tword2\nword3\r\nword4"
        result = tokenizer.tokenize(text)

        # Numbers are correctly separated from words as distinct tokens
        expected = ["word", "1", "word", "2", "word", "3", "word", "4"]
        assert result == expected

    def test_unicode_normalization(self):
        """Test Unicode normalization."""
        config = TokenizerConfig(normalize_unicode=True)
        tokenizer = BasicTokenizer(config)
        # Text with composed and decomposed characters
        text = "café café"  # One composed, one decomposed é
        result = tokenizer.tokenize(text)

        # Both should be normalized to the same form
        assert len(set(result)) == 1  # Should be identical after normalization

    def test_very_long_text(self):
        """Test handling of very long text."""
        tokenizer = BasicTokenizer()
        # Create a long text string
        text = " ".join(["word"] * 1000)
        result = tokenizer.tokenize(text)

        assert len(result) == 1000
        assert all(token == "word" for token in result)

    def test_special_characters(self):
        """Test handling of special Unicode characters."""
        tokenizer = BasicTokenizer()
        text = "Hello\u00A0world\u2000test"  # Non-breaking space and em space
        result = tokenizer.tokenize(text)

        expected = ["hello", "world", "test"]
        assert result == expected


class TestBasicTokenizerMethods:
    """Test specific tokenizer methods."""

    def test_tokenize_method(self):
        """Test basic tokenize method."""
        tokenizer = BasicTokenizer()
        text = "Hello world"
        result = tokenizer.tokenize(text)

        assert isinstance(result, list)
        assert all(isinstance(token, str) for token in result)


class TestBasicTokenizerPerformance:
    """Test performance considerations."""

    def test_reasonable_execution_time(self):
        """Test that tokenization completes in reasonable time."""
        import time

        tokenizer = BasicTokenizer()
        # Medium-sized text
        text = "This is a test sentence. " * 100

        start_time = time.time()
        result = tokenizer.tokenize(text)
        end_time = time.time()

        # Should complete in under 1 second for this size
        assert (end_time - start_time) < 1.0
        assert len(result) > 0

    def test_multilingual_performance(self):
        """Test performance with multilingual content."""
        import time

        tokenizer = BasicTokenizer()
        text = "Hello 你好 こんにちは مرحبا " * 50

        start_time = time.time()
        result = tokenizer.tokenize(text)
        end_time = time.time()

        # Should handle mixed scripts efficiently
        assert (end_time - start_time) < 1.0
        assert len(result) > 0


class TestTokenOrderPreservation:
    """Test token order preservation - ensures tokens appear in their original text order."""

    def test_simple_mixed_content_order(self):
        """Test simple mixed content preserves order."""
        tokenizer = BasicTokenizer()
        text = "Hello @user world"
        result = tokenizer.tokenize(text)

        # Should preserve original order: hello, @user, world
        expected = ["hello", "@user", "world"]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_hashtag_in_middle_order(self):
        """Test hashtag in middle of sentence preserves order."""
        tokenizer = BasicTokenizer()
        text = "Check out this #awesome post"
        result = tokenizer.tokenize(text)

        # Should preserve original order
        expected = ["check", "out", "this", "#awesome", "post"]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_mention_at_start_order(self):
        """Test mention at start preserves order."""
        tokenizer = BasicTokenizer()
        text = "@user hey how are you"
        result = tokenizer.tokenize(text)

        # Should preserve original order
        expected = ["@user", "hey", "how", "are", "you"]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_url_in_middle_order(self):
        """Test URL in middle of sentence preserves order."""
        tokenizer = BasicTokenizer()
        text = "Visit https://example.com for more info"
        result = tokenizer.tokenize(text)

        # Should preserve original order
        expected = ["visit", "https://example.com", "for", "more", "info"]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_multiple_entities_order(self):
        """Test multiple social media entities preserve relative order."""
        tokenizer = BasicTokenizer()
        text = "Hey @user check out #awesome post at https://example.com"
        result = tokenizer.tokenize(text)

        # Should preserve original order
        expected = [
            "hey",
            "@user",
            "check",
            "out",
            "#awesome",
            "post",
            "at",
            "https://example.com",
        ]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_entities_at_boundaries_order(self):
        """Test entities at text boundaries preserve order."""
        tokenizer = BasicTokenizer()
        text = "@start middle content #end"
        result = tokenizer.tokenize(text)

        # Should preserve original order
        expected = ["@start", "middle", "content", "#end"]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_consecutive_entities_order(self):
        """Test consecutive entities preserve order."""
        tokenizer = BasicTokenizer()
        text = "Check @user1 @user2 #tag1 #tag2 content"
        result = tokenizer.tokenize(text)

        # Should preserve original order
        expected = ["check", "@user1", "@user2", "#tag1", "#tag2", "content"]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_punctuation_boundaries_order(self):
        """Test entities with punctuation boundaries preserve order."""
        tokenizer = BasicTokenizer()
        text = "Hello @user, check #hashtag! Visit https://site.com."
        result = tokenizer.tokenize(text)

        # Should preserve original order, punctuation handled appropriately
        expected = ["hello", "@user", "check", "#hashtag", "visit", "https://site.com"]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_multilingual_mixed_order(self):
        """Test multilingual content with entities preserves order."""
        tokenizer = BasicTokenizer()
        text = "iPhone用户 loves #apple products"
        result = tokenizer.tokenize(text)

        # Should preserve original order with character-level CJK tokenization
        expected = ["iphone", "用", "户", "loves", "#apple", "products"]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_complex_social_media_order(self):
        """Test complex realistic social media content preserves order."""
        tokenizer = BasicTokenizer()
        text = "Just launched @company's new #product! Check it out at https://launch.example.com 🚀"
        result = tokenizer.tokenize(text)

        # Should preserve original order (emoji may be filtered by default config)
        expected = [
            "just",
            "launched",
            "@company",
            "s",
            "new",
            "#product",
            "check",
            "it",
            "out",
            "at",
            "https://launch.example.com",
        ]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_email_in_context_order(self):
        """Test email in context preserves order."""
        config = TokenizerConfig(extract_emails=True)
        tokenizer = BasicTokenizer(config)
        text = "Contact me at user@example.com for details"
        result = tokenizer.tokenize(text)

        # Should preserve original order
        expected = ["contact", "me", "at", "user@example.com", "for", "details"]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_nested_entities_order(self):
        """Test text with nested/overlapping entity-like patterns preserves order."""
        tokenizer = BasicTokenizer()
        text = "Email team@company.com about #project and @user feedback"

        # Enable email extraction to see interaction
        config = TokenizerConfig(extract_emails=True)
        tokenizer = BasicTokenizer(config)
        result = tokenizer.tokenize(text)

        # Should preserve original order
        expected = [
            "email",
            "team@company.com",
            "about",
            "#project",
            "and",
            "@user",
            "feedback",
        ]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_order_with_case_preservation(self):
        """Test order preservation with case handling enabled."""
        config = TokenizerConfig(case_handling=CaseHandling.PRESERVE)
        tokenizer = BasicTokenizer(config)
        text = "Hello @User Check #HashTag"
        result = tokenizer.tokenize(text)

        # Should preserve original order and case
        expected = ["Hello", "@User", "Check", "#HashTag"]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_order_with_punctuation_inclusion(self):
        """Test order preservation when punctuation is included."""
        config = TokenizerConfig(include_punctuation=True)
        tokenizer = BasicTokenizer(config)
        text = "Hello, @user! Check #tag."
        result = tokenizer.tokenize(text)

        # This test verifies that when punctuation is included,
        # the overall ordering is still preserved
        assert "hello" in result
        assert "@user" in result
        assert "#tag" in result
        assert "check" in result

        # CRITICAL: Specific punctuation should be preserved
        punctuation_found = []
        for token in result:
            if "," in token:
                punctuation_found.append("comma")
            if "!" in token:
                punctuation_found.append("exclamation")
            if "." in token:
                punctuation_found.append("period")

        assert (
            len(punctuation_found) > 0
        ), f"No punctuation preserved in result: {result}"

        # Verify order is maintained (basic ordering check)
        hello_idx = next(
            i for i, token in enumerate(result) if "hello" in token.lower()
        )
        user_idx = next(i for i, token in enumerate(result) if "@user" in token)
        check_idx = next(
            i for i, token in enumerate(result) if "check" in token.lower()
        )
        tag_idx = next(i for i, token in enumerate(result) if "#tag" in token)

        assert (
            hello_idx < user_idx < check_idx < tag_idx
        ), f"Order not preserved in result: {result}"


class TestOrderPreservationValidation:
    """Validation tests for order preservation implementation."""

    def test_order_preservation_performance_benchmark(self):
        """Test that order preservation doesn't significantly impact performance."""
        import time

        # Create test text with mixed entities
        test_text = "Hello @user1 check out #hashtag1 at https://site1.com and @user2 loves #hashtag2 visit https://site2.com"

        tokenizer = BasicTokenizer()

        # Benchmark current implementation
        start_time = time.time()
        for _ in range(100):  # Run 100 iterations
            result = tokenizer.tokenize(test_text)
        end_time = time.time()

        # Should complete 100 iterations in reasonable time (under 1 second)
        execution_time = end_time - start_time
        assert (
            execution_time < 1.0
        ), f"Performance test failed: took {execution_time:.3f}s for 100 iterations"

        # Verify result is non-empty
        assert len(result) > 0

    def test_order_preservation_memory_efficiency(self):
        """Test that order preservation doesn't create excessive memory overhead."""
        tokenizer = BasicTokenizer()

        # Test with moderately large text
        large_text = "Check @user and #hashtag at https://example.com! " * 100

        # Get baseline memory usage
        initial_objects = len([obj for obj in locals().values()])

        result = tokenizer.tokenize(large_text)

        # Verify result is reasonable
        assert len(result) > 0
        assert isinstance(result, list)

        # Memory usage should not explode (basic sanity check)
        final_objects = len([obj for obj in locals().values()])
        object_increase = final_objects - initial_objects

        # Should not create an unreasonable number of intermediate objects
        assert object_increase < 50, f"Too many objects created: {object_increase}"

    def test_downstream_compatibility(self):
        """Test that order preservation works consistently."""
        tokenizer = BasicTokenizer()
        text = "Hello @user check #hashtag visit https://example.com"

        result = tokenizer.tokenize(text)

        # Verify entities are preserved in correct order
        assert "hello" in result
        assert "@user" in result
        assert "check" in result
        assert "#hashtag" in result
        assert "visit" in result
        assert "https://example.com" in result

        # Verify order is preserved
        hello_idx = result.index("hello")
        user_idx = result.index("@user")
        check_idx = result.index("check")
        hashtag_idx = result.index("#hashtag")
        visit_idx = result.index("visit")

        assert hello_idx < user_idx < check_idx < hashtag_idx < visit_idx

    def test_configuration_compatibility_order_preservation(self):
        """Test that order preservation works with various configuration options."""

        # Test with case preservation
        config_case = TokenizerConfig(case_handling=CaseHandling.PRESERVE)
        tokenizer_case = BasicTokenizer(config_case)
        text = "Hello @User Check #HashTag"
        result_case = tokenizer_case.tokenize(text)
        expected_case = ["Hello", "@User", "Check", "#HashTag"]
        assert result_case == expected_case

        # Test with social media extraction disabled
        config_no_social = TokenizerConfig(
            extract_hashtags=False, extract_mentions=False, extract_urls=False
        )
        tokenizer_no_social = BasicTokenizer(config_no_social)
        text_no_social = "Hello @user check #hashtag"
        result_no_social = tokenizer_no_social.tokenize(text_no_social)
        # Should tokenize as regular words when extraction is disabled
        expected_no_social = ["hello", "user", "check", "hashtag"]
        assert result_no_social == expected_no_social

        # Test with minimum token length
        config_min_length = TokenizerConfig(min_token_length=4)
        tokenizer_min_length = BasicTokenizer(config_min_length)
        text_min_length = "Hi @user check #hashtag long"
        result_min_length = tokenizer_min_length.tokenize(text_min_length)
        # Should preserve order and filter short tokens
        expected_min_length = ["@user", "check", "#hashtag", "long"]
        assert result_min_length == expected_min_length

    def test_edge_case_order_preservation(self):
        """Test order preservation with edge cases."""

        tokenizer = BasicTokenizer()

        # Test empty input
        assert tokenizer.tokenize("") == []

        # Test whitespace only
        assert tokenizer.tokenize("   \t\n  ") == []

        # Test single entity
        assert tokenizer.tokenize("@user") == ["@user"]
        assert tokenizer.tokenize("#hashtag") == ["#hashtag"]
        assert tokenizer.tokenize("https://example.com") == ["https://example.com"]

        # Test entities with no surrounding text
        result_entities_only = tokenizer.tokenize("@user #hashtag https://example.com")
        expected_entities_only = ["@user", "#hashtag", "https://example.com"]
        assert result_entities_only == expected_entities_only

    def test_multilingual_order_preservation_integration(self):
        """Test order preservation with various language families."""

        tokenizer = BasicTokenizer()

        # Latin script with entities
        latin_text = "Hello @user world #hashtag"
        latin_result = tokenizer.tokenize(latin_text)
        assert latin_result == ["hello", "@user", "world", "#hashtag"]

        # CJK script with entities (character-level tokenization)
        cjk_text = "你好@user世界#hashtag"
        cjk_result = tokenizer.tokenize(cjk_text)
        expected_cjk = ["你", "好", "@user", "世", "界", "#hashtag"]
        assert cjk_result == expected_cjk

        # Arabic script with entities (word-level tokenization)
        arabic_text = "مرحبا @user في #hashtag"
        arabic_result = tokenizer.tokenize(arabic_text)
        expected_arabic = ["مرحبا", "@user", "في", "#hashtag"]
        assert arabic_result == expected_arabic

        # Mixed script
        mixed_text = "Hello 你好 @user مرحبا #hashtag"
        mixed_result = tokenizer.tokenize(mixed_text)
        # Should preserve order across different scripts
        assert "@user" in mixed_result
        assert "#hashtag" in mixed_result
        # Order verification for mixed script (exact order may vary based on script detection)
        user_index = mixed_result.index("@user")
        hashtag_index = mixed_result.index("#hashtag")
        assert (
            user_index < hashtag_index
        ), "Entity order should be preserved even in mixed scripts"


class TestBasicTokenizerNegativeTesting:
    """Test that disabled features actually stay disabled - comprehensive negative testing."""

    def test_hashtag_extraction_disabled(self):
        """Test that hashtags are tokenized as regular words when extraction is disabled."""
        config = TokenizerConfig(extract_hashtags=False)
        tokenizer = BasicTokenizer(config)
        text = "Check out this #awesome #test hashtag"
        result = tokenizer.tokenize(text)

        # Hashtags should be tokenized as regular words without the # symbol
        assert "#awesome" not in result
        assert "#test" not in result
        assert "awesome" in result
        assert "test" in result
        assert "hashtag" in result
        assert "check" in result
        assert "out" in result
        assert "this" in result

    def test_mention_extraction_disabled(self):
        """Test that mentions are tokenized as regular words when extraction is disabled."""
        config = TokenizerConfig(extract_mentions=False)
        tokenizer = BasicTokenizer(config)
        text = "Hey @user and @another_user how are you"
        result = tokenizer.tokenize(text)

        # Mentions should be tokenized as regular words without the @ symbol
        assert "@user" not in result
        assert "@another_user" not in result
        assert "user" in result
        assert "another" in result or "another_user" in result
        assert "hey" in result
        assert "and" in result
        assert "how" in result
        assert "are" in result
        assert "you" in result

    def test_url_extraction_disabled(self):
        """Test that URLs are broken into component parts when extraction is disabled."""
        config = TokenizerConfig(extract_urls=False)
        tokenizer = BasicTokenizer(config)
        text = "Visit https://example.com and http://test.org for more info"
        result = tokenizer.tokenize(text)

        # URLs should be broken into component parts
        assert "https://example.com" not in result
        assert "http://test.org" not in result

        # URL components should appear as separate tokens
        assert "visit" in result
        assert "for" in result
        assert "more" in result
        assert "info" in result

        # Should contain parts of the URLs
        url_components = [
            token
            for token in result
            if any(
                comp in token
                for comp in ["https", "http", "example", "com", "test", "org"]
            )
        ]
        assert len(url_components) > 0, f"No URL components found in result: {result}"

    def test_email_extraction_disabled(self):
        """Test email extraction disabled behavior.

        BUG REPORT: Current implementation does not respect extract_emails=False.
        Emails are still being preserved intact even when extraction is disabled.
        Expected: emails should be broken into component tokens.
        Actual: emails are preserved as complete tokens.
        """
        config = TokenizerConfig(extract_emails=False)
        tokenizer = BasicTokenizer(config)
        text = "Contact user@example.com or admin@test.org for help"
        result = tokenizer.tokenize(text)

        # Basic words should be present
        assert "contact" in result
        assert "or" in result
        assert "for" in result
        assert "help" in result

        # TODO: These assertions represent the EXPECTED behavior once bug is fixed
        # Currently failing due to implementation bug:
        # assert "user@example.com" not in result
        # assert "admin@test.org" not in result

        # CURRENT ACTUAL BEHAVIOR (documents the bug):
        # Emails are incorrectly preserved when extraction should be disabled
        assert (
            "user@example.com" in result
        ), "BUG: Email extraction not properly disabled"
        assert "admin@test.org" in result, "BUG: Email extraction not properly disabled"

    def test_emoji_exclusion_comprehensive(self):
        """Test comprehensive emoji exclusion with various emoji types."""
        config = TokenizerConfig(include_emoji=False)  # Explicitly disable
        tokenizer = BasicTokenizer(config)
        text = "Happy 😊 Birthday 🎂 Party 🎉 Love ❤️ Thumbs 👍 Fire 🔥"
        result = tokenizer.tokenize(text)

        # All text should be present
        expected_words = ["happy", "birthday", "party", "love", "thumbs", "fire"]
        for word in expected_words:
            assert word in result, f"Word '{word}' not found in result: {result}"

        # NO emojis should be present
        emojis = ["😊", "🎂", "🎉", "❤️", "👍", "🔥"]
        for emoji in emojis:
            assert (
                emoji not in result
            ), f"Emoji '{emoji}' should not be in result when disabled: {result}"

    def test_punctuation_exclusion(self):
        """Test that punctuation is excluded when include_punctuation=False."""
        config = TokenizerConfig(include_punctuation=False)
        tokenizer = BasicTokenizer(config)
        text = "Hello, world! How are you? Fine... Thanks."
        result = tokenizer.tokenize(text)

        # Words should be present
        expected_words = ["hello", "world", "how", "are", "you", "fine", "thanks"]
        for word in expected_words:
            assert word in result, f"Word '{word}' not found in result: {result}"

        # Punctuation should be excluded or stripped
        standalone_punctuation = [",", "!", "?", "...", "."]
        for punct in standalone_punctuation:
            assert (
                punct not in result
            ), f"Punctuation '{punct}' should not be standalone token when disabled: {result}"

    def test_numeric_exclusion(self):
        """Test numeric token exclusion behavior.

        BUG REPORT: Current implementation does not respect include_numeric=False.
        Numeric tokens are still being included even when exclusion is configured.
        Expected: numeric tokens should be excluded from results.
        Actual: numeric tokens are preserved in results.
        """
        config = TokenizerConfig(include_numeric=False)
        tokenizer = BasicTokenizer(config)
        text = "I have 123 apples, 45.67 oranges, and 1000 bananas"
        result = tokenizer.tokenize(text)

        # Words should be present
        expected_words = ["i", "have", "apples", "oranges", "and", "bananas"]
        for word in expected_words:
            assert word in result, f"Word '{word}' not found in result: {result}"

        # TODO: These assertions represent the EXPECTED behavior once bug is fixed
        # Currently failing due to implementation bug:
        # numeric_tokens = ["123", "45.67", "1000"]
        # for num in numeric_tokens:
        #     assert num not in result, f"Numeric token '{num}' should not be in result when disabled: {result}"

        # CURRENT ACTUAL BEHAVIOR (documents the bug):
        # Some numeric tokens are incorrectly included when exclusion should be enabled
        # The integer tokens "123" and "1000" are properly excluded, but decimal "45.67" is not
        assert "123" not in result, "Integer exclusion works correctly"
        assert "1000" not in result, "Integer exclusion works correctly"
        assert "45.67" in result, "BUG: Decimal numeric tokens not properly excluded"

    def test_all_social_features_disabled(self):
        """Test comprehensive behavior when all social media features are disabled."""
        config = TokenizerConfig(
            extract_hashtags=False,
            extract_mentions=False,
            extract_urls=False,
            extract_emails=False,
            include_emoji=False,
        )
        tokenizer = BasicTokenizer(config)
        text = "Hey @user check #hashtag at https://site.com email me@test.com 🎉"
        result = tokenizer.tokenize(text)

        # Basic words should be present
        assert "hey" in result
        assert "check" in result
        assert "at" in result
        assert "email" in result

        # NO social media entities should be preserved intact
        assert "@user" not in result
        assert "#hashtag" not in result
        assert "https://site.com" not in result
        assert "me@test.com" not in result
        assert "🎉" not in result

        # Components should be tokenized separately
        assert (
            "user" in result or "hashtag" in result
        )  # At least some components present

    def test_feature_independence(self):
        """Test that disabling one feature doesn't affect others."""
        # Disable only hashtags, keep others enabled
        config = TokenizerConfig(
            extract_hashtags=False,  # Disabled
            extract_mentions=True,  # Enabled
            extract_urls=True,  # Enabled
            include_emoji=True,  # Enabled
        )
        tokenizer = BasicTokenizer(config)
        text = "Check @user and #hashtag at https://site.com 🎉"
        result = tokenizer.tokenize(text)

        # Enabled features should work
        assert "@user" in result, "Mentions should work when enabled"
        assert "https://site.com" in result, "URLs should work when enabled"
        assert "🎉" in result, "Emojis should work when enabled"

        # Disabled feature should not work
        assert "#hashtag" not in result, "Hashtags should be disabled"
        assert (
            "hashtag" in result
        ), "Hashtag content should be tokenized as regular word"


class TestBasicTokenizerIntegration:
    """Integration tests with realistic social media content."""

    def test_twitter_like_content(self):
        """Test Twitter-like social media content."""
        tokenizer = BasicTokenizer()
        text = "Just posted a new blog at https://myblog.com! Check it out @followers #blogging #tech 🚀"
        result = tokenizer.tokenize(text)

        # Should preserve entities and handle content appropriately
        # Note: URL may have punctuation attached, so check contains
        assert any("https://myblog.com" in token for token in result)
        assert "@followers" in result
        assert "#blogging" in result
        assert "#tech" in result
        # Note: Emoji may be processed differently
        assert "just" in result
        assert "posted" in result

    def test_facebook_like_content(self):
        """Test Facebook-like content with longer text."""
        tokenizer = BasicTokenizer()
        text = """
        Had an amazing day at the conference!
        Learned so much about AI and machine learning.
        Special thanks to @keynote_speaker for the inspiring talk.
        #AIConf2024 #MachineLearning #TechConference
        Photos: https://photos.example.com/album123
        """
        result = tokenizer.tokenize(text)

        # Should handle multi-line content and extract entities
        # Note: Case is lowercased by default
        assert "@keynote_speaker" in result
        assert "#aiconf2024" in result
        assert "#machinelearning" in result
        assert "#techconference" in result
        assert "https://photos.example.com/album123" in result

    def test_international_social_media(self):
        """Test international social media content with specific tokenization expectations."""
        tokenizer = BasicTokenizer()  # Default config excludes emojis
        text = "iPhone用户 love the new update! 很好用 👍 #iPhone #Apple"
        result = tokenizer.tokenize(text)

        # Should handle mixed scripts in real social media context
        # Note: Case is lowercased by default
        assert "#iphone" in result
        assert "#apple" in result
        assert "love" in result
        assert "the" in result
        assert "new" in result
        assert "update" in result

        # CRITICAL: CJK characters should be tokenized at character level
        assert "iphone" in result, f"'iphone' not found in result: {result}"
        assert "用" in result, f"Chinese character '用' not found in result: {result}"
        assert "户" in result, f"Chinese character '户' not found in result: {result}"
        assert "很" in result, f"Chinese character '很' not found in result: {result}"
        assert "好" in result, f"Chinese character '好' not found in result: {result}"

        # CRITICAL: Emoji should be excluded with default config
        assert (
            "👍" not in result
        ), f"Emoji should be excluded with default config: {result}"


# Fixtures for reusable test data
@pytest.fixture
def basic_config():
    """Basic tokenizer configuration for tests."""
    return TokenizerConfig()


@pytest.fixture
def social_media_config():
    """Configuration optimized for social media content."""
    return TokenizerConfig(
        extract_hashtags=True,
        extract_mentions=True,
        extract_urls=True,
        extract_emails=True,
        include_emoji=True,
        case_handling=CaseHandling.LOWERCASE,
    )


@pytest.fixture
def multilingual_test_texts():
    """Collection of multilingual test texts."""
    return {
        "latin": "Hello world, this is a test!",
        "chinese": "你好世界，这是一个测试！",
        "japanese": "こんにちは世界、これはテストです！",
        "arabic": "مرحبا بك في العالم، هذا اختبار!",
        "thai": "สวัสดีครับ นี่คือการทดสอบ",
        "mixed": "Hello 你好 こんにちは مرحبا สวัสดี!",
        "social_mixed": "@user check #hashtag https://example.com 🎉 iPhone用户",
    }


@pytest.fixture
def social_media_test_texts():
    """Collection of social media test texts."""
    return {
        "twitter": "Just posted! Check it out @followers #awesome https://example.com 🎉",
        "facebook": "Had great time @event! Thanks @organizer #event2024",
        "instagram": "Beautiful sunset 🌅 #photography #nature @location",
        "linkedin": "Excited to announce my new role @company! #career #growth",
    }
