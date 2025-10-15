"""
Comprehensive test suite for BasicTokenizer.

This module contains unit tests for the BasicTokenizer implementation,
covering multilingual tokenization, social media entity handling,
configuration options, and edge cases.

Test Organization:
- TestBasicTokenizerMultilingual: Script-specific tokenization (Latin, CJK, Arabic, etc.)
- TestBasicTokenizerSocialMedia: Entity extraction (hashtags, mentions, URLs, emojis)
- TestBasicTokenizerConfig: Configuration options and parameters
- TestBasicTokenizerEdgeCases: Edge cases and error conditions
- TestBasicTokenizerMethods: Method-level validation
- TestBasicTokenizerPerformance: Performance benchmarks
- TestErrorHandling: Error handling and robustness
- TestOrderPreservation: Token order preservation validation (consolidated)
- TestBasicTokenizerNegativeTesting: Disabled feature verification
- TestBasicTokenizerIntegration: Realistic social media scenarios
- TestAbbreviationsAndPunctuation: Special handling for abbreviations
- TestBotDetectionEdgeCases: Bot detection and anomaly handling

Running Tests:
    # Run all tests
    pytest services/tokenizer/basic/test_basic_tokenizer.py

    # Run only unit tests (fast)
    pytest -m unit services/tokenizer/basic/test_basic_tokenizer.py

    # Run only integration tests
    pytest -m integration services/tokenizer/basic/test_basic_tokenizer.py

    # Run specific test class
    pytest services/tokenizer/basic/test_basic_tokenizer.py::TestBasicTokenizerMultilingual
"""

import pytest

from ..core.types import CaseHandling, TokenizerConfig
from .tokenizer import BasicTokenizer


@pytest.mark.unit
class TestBasicTokenizerMultilingual:
    """Test multilingual tokenization capabilities."""

    @pytest.mark.parametrize(
        "text,expected,script_name",
        [
            # Latin script - space-separated
            (
                "Hello world, this is a test!",
                ["hello", "world", "this", "is", "a", "test"],
                "Latin",
            ),
            # Chinese - character-level tokenization
            ("你好世界", ["你", "好", "世", "界"], "Chinese"),
            # Japanese - mixed hiragana and kanji, character-level
            (
                "こんにちは世界",
                ["こ", "ん", "に", "ち", "は", "世", "界"],
                "Japanese",
            ),
            # Arabic - space-separated
            ("مرحبا بك في العالم", ["مرحبا", "بك", "في", "العالم"], "Arabic"),
            # Thai - character-level tokenization
            (
                "สวัสดีครับ",
                ["ส", "ว", "ั", "ส", "ด", "ี", "ค", "ร", "ั", "บ"],
                "Thai",
            ),
            # Korean - space-separated (NOT character-level)
            ("안녕하세요 세계", ["안녕하세요", "세계"], "Korean"),
        ],
    )
    def test_script_tokenization(
        self, default_tokenizer, text, expected, script_name
    ):
        """Test tokenization for different language scripts."""
        result = default_tokenizer.tokenize(text)
        assert (
            result == expected
        ), f"{script_name} tokenization failed: expected {expected}, got {result}"

    def test_korean_mixed_with_latin(self, default_tokenizer):
        """Test Korean mixed with Latin script (special case)."""
        text = "iPhone용 앱을 사용합니다"  # Mixed Korean-English
        result = default_tokenizer.tokenize(text)
        expected = ["iphone", "용", "앱을", "사용합니다"]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_korean_with_social_media(self, default_tokenizer):
        """Test Korean with social media entities."""
        text = "안녕하세요 @user #한글"
        result = default_tokenizer.tokenize(text)
        expected = ["안녕하세요", "@user", "#한글"]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_mixed_script_multilingual(self, default_tokenizer):
        """Test mixed multilingual content with specific tokenization expectations."""
        text = "Hello 你好 こんにちは 안녕하세요 مرحبا สวัสดี"
        result = default_tokenizer.tokenize(text)

        # Should handle script boundaries with specific expected tokenization
        expected = [
            "hello",
            "你",
            "好",
            "こ",
            "ん",
            "に",
            "ち",
            "は",
            "안녕하세요",
            "مرحبا",
            "ส",
            "ว",
            "ั",
            "ส",
            "ด",
            "ี",
        ]
        assert result == expected, f"Expected {expected}, got {result}"


@pytest.mark.unit
class TestBasicTokenizerSocialMedia:
    """Test social media entity handling."""

    def test_hashtag_extraction(self, default_tokenizer):
        """Test hashtag preservation."""
        text = "Check out this #awesome post!"
        result = default_tokenizer.tokenize(text)

        # Should preserve original order: check, out, this, #awesome, post
        expected = ["check", "out", "this", "#awesome", "post"]
        assert result == expected

    def test_mention_extraction(self, default_tokenizer):
        """Test mention preservation."""
        text = "Hey @user how are you?"
        result = default_tokenizer.tokenize(text)

        # Should preserve original order: hey, @user, how, are, you
        expected = ["hey", "@user", "how", "are", "you"]
        assert result == expected

    def test_url_preservation(self, default_tokenizer):
        """Test URL preservation."""
        text = "Visit https://example.com for more info"
        result = default_tokenizer.tokenize(text)

        # Should preserve original order: visit, https://example.com, for, more, info
        expected = ["visit", "https://example.com", "for", "more", "info"]
        assert result == expected

    def test_emoji_exclusion_by_default(self, default_tokenizer):
        """Test emoji exclusion with default configuration (include_emoji=False)."""
        text = "Great job! 🎉 Keep it up! 👍"
        result = default_tokenizer.tokenize(text)

        # Check that text tokens are included
        assert "great" in result
        assert "job" in result
        assert "keep" in result
        assert "it" in result
        assert "up" in result

        # CRITICAL: Emojis should be excluded with default config
        assert "🎉" not in result
        assert "👍" not in result

    def test_emoji_inclusion_when_enabled(self, social_media_tokenizer):
        """Test emoji preservation when explicitly enabled in configuration."""
        text = "Great job! 🎉 Keep it up! 👍"
        result = social_media_tokenizer.tokenize(text)

        # Check that text tokens are included
        assert "great" in result
        assert "job" in result
        assert "keep" in result
        assert "it" in result
        assert "up" in result

        # CRITICAL: Emojis should be preserved when enabled
        assert "🎉" in result
        assert "👍" in result

    def test_complex_social_media_text(self, default_tokenizer):
        """Test complex social media content with default configuration (emoji excluded)."""
        text = "@user check #hashtag https://example.com 🎉 Amazing!"
        result = default_tokenizer.tokenize(text)

        # Should preserve original order: @user, check, #hashtag, https://example.com, amazing
        expected = ["@user", "check", "#hashtag", "https://example.com", "amazing"]
        assert result == expected

        # CRITICAL: Emoji should be excluded with default config
        assert "🎉" not in result

    def test_email_extraction(self, social_media_tokenizer):
        """Test email extraction when enabled."""
        text = "Contact me at user@example.com for details"
        result = social_media_tokenizer.tokenize(text)

        # Should include the email and basic words
        assert "user@example.com" in result
        assert "contact" in result
        assert "me" in result
        assert "for" in result
        assert "details" in result


@pytest.mark.unit
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
        # CRITICAL: Specific punctuation should be preserved as separate tokens
        assert "," in result, "Comma should be preserved as a separate token"
        assert "!" in result, "Exclamation should be preserved as a separate token"

        # Verify punctuation is actually included in the tokenization
        has_punctuation = any(
            any(char in ".,!?;:" for char in token) for token in result
        )
        assert has_punctuation, f"No punctuation found in result: {result}"

    def test_numeric_inclusion(self):
        """Test numeric token handling."""
        config = TokenizerConfig(include_numeric=True)
        tokenizer = BasicTokenizer(config)
        text = "I have 123 apples and 45.67 oranges plus 6th item"
        result = tokenizer.tokenize(text)

        # Should include basic word tokens
        assert "i" in result
        assert "have" in result
        assert "apples" in result
        assert "and" in result
        assert "oranges" in result

        # CRITICAL: Specific numeric tokens should be preserved
        assert "123" in result, f"Integer '123' not found in result: {result}"
        assert (
            "45.67" in result
        ), f"Decimal '45.67' not properly tokenized in result: {result}"
        assert "6th" in result, f"Ordinal '6th' not found in result: {result}"

    def test_ordinal_number_preservation(self):
        """Test ordinal numbers are preserved as single tokens."""
        config = TokenizerConfig(include_numeric=True)
        tokenizer = BasicTokenizer(config)
        text = "The 6th amendment and 21st century trends"
        result = tokenizer.tokenize(text)

        # Check ordinals are preserved
        assert "6th" in result, f"Expected '6th' in {result}"
        assert "21st" in result, f"Expected '21st' in {result}"
        assert "amendment" in result
        assert "century" in result

    def test_large_numbers_with_thousand_separators(self):
        """Test large numbers with multiple thousand separators."""
        config = TokenizerConfig(include_numeric=True)
        tokenizer = BasicTokenizer(config)
        text = "We counted 200,000 ballots and found 1,234,567 votes"
        result = tokenizer.tokenize(text)

        # Check large numbers are preserved with separators
        assert "200,000" in result, f"Expected '200,000' in {result}"
        assert "1,234,567" in result, f"Expected '1,234,567' in {result}"
        assert "ballots" in result
        assert "votes" in result

    def test_currency_symbols_with_numbers(self):
        """Test currency symbols with various number formats."""
        config = TokenizerConfig(include_numeric=True)
        tokenizer = BasicTokenizer(config)
        text = "Prices are $100 €200.50 £50 ¥1000 ₹500.75"
        result = tokenizer.tokenize(text)

        # Check currency amounts are preserved
        assert "prices" in result
        assert "are" in result
        assert "$100" in result, f"Expected '$100' in {result}"
        assert (
            "€200.50" in result or "€200,50" in result
        ), f"Expected '€200.50' or '€200,50' in {result}"
        assert "£50" in result, f"Expected '£50' in {result}"
        assert "¥1000" in result, f"Expected '¥1000' in {result}"
        assert (
            "₹500.75" in result or "₹500,75" in result
        ), f"Expected '₹500.75' or '₹500,75' in {result}"

    def test_percentages(self):
        """Test percentage token handling."""
        config = TokenizerConfig(include_numeric=True)
        tokenizer = BasicTokenizer(config)
        text = "Growth is 50% and completion is 100% target"
        result = tokenizer.tokenize(text)

        # Check percentages are preserved
        assert "growth" in result
        assert "is" in result
        assert "50%" in result, f"Expected '50%' in {result}"
        assert "and" in result
        assert "completion" in result
        assert "is" in result
        assert "100%" in result, f"Expected '100%' in {result}"
        assert "target" in result

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
            extract_hashtags=False, extract_mentions=True, include_urls=False
        )
        tokenizer = BasicTokenizer(config)
        text = "@user check #hashtag https://example.com"
        result = tokenizer.tokenize(text)

        # Only mentions should be preserved
        assert "@user" in result
        assert "check" in result

        # CRITICAL: Disabled features should behave according to their type
        assert "#hashtag" not in result  # Should be tokenized as "hashtag"
        assert "hashtag" in result
        assert "https://example.com" not in result  # Should be completely excluded

        # URLs should be completely excluded when include_urls=False, not tokenized as parts
        url_components = [
            token
            for token in result
            if any(comp in token.lower() for comp in ["https", "example", "com"])
        ]
        assert len(url_components) == 0, f"URLs should be completely excluded: {result}"


@pytest.mark.unit
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
        text = "Hello\u00a0world\u2000test"  # Non-breaking space and em space
        result = tokenizer.tokenize(text)

        expected = ["hello", "world", "test"]
        assert result == expected


@pytest.mark.unit
class TestBasicTokenizerMethods:
    """Test specific tokenizer methods."""

    def test_tokenize_method(self):
        """Test basic tokenize method."""
        tokenizer = BasicTokenizer()
        text = "Hello world"
        result = tokenizer.tokenize(text)

        # Should return specific expected tokens, not just check types
        expected = ["hello", "world"]
        assert result == expected


@pytest.mark.unit
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


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling and robustness."""

    def test_extremely_long_input(self):
        """Test handling of very long input (stress test, not timing)."""
        tokenizer = BasicTokenizer()

        # Create 100,000 word text (~500KB)
        text = " ".join(["word"] * 100_000)
        result = tokenizer.tokenize(text)

        # Should handle without crashing
        assert len(result) == 100_000
        assert all(token == "word" for token in result)

    def test_control_characters(self):
        """Test handling of control characters."""
        tokenizer = BasicTokenizer()

        # Text with control characters (tab, newline, null, etc.)
        text = "word1\x00word2\x01word3\x1fword4"
        result = tokenizer.tokenize(text)

        # Should handle gracefully (filter or preserve depending on implementation)
        assert isinstance(result, list)
        # At minimum, "word" parts should be extractable
        assert any("word" in token for token in result)

    def test_none_text_handling(self):
        """Test explicit None handling."""
        tokenizer = BasicTokenizer()

        # Should handle None gracefully
        try:
            result = tokenizer.tokenize(None)  # type: ignore
            # If it doesn't raise, should return empty list
            assert result == []
        except (TypeError, AttributeError):
            # Also acceptable to raise an error
            pass

    def test_complex_unicode_edge_cases(self):
        """Test complex Unicode edge cases."""
        tokenizer = BasicTokenizer()

        # Zero-width joiner (emoji sequences)
        text = "family👨‍👩‍👧‍👦emoji"
        result = tokenizer.tokenize(text)
        assert "family" in result

        # Non-breaking spaces (U+00A0) - acts as word separator
        text = "word\u00a0test"
        result = tokenizer.tokenize(text)
        assert "word" in result
        assert "test" in result

        # Right-to-left mark (U+200F)
        text = "hello\u200fworld"
        result = tokenizer.tokenize(text)
        assert isinstance(result, list)


@pytest.mark.unit
class TestOrderPreservation:
    """Test token order preservation across different scenarios.

    Order preservation ensures tokens appear in their original text order,
    critical for maintaining context in social media analysis.

    Coverage:
    - Basic mixed content (text + entities)
    - Entities at boundaries (start/end)
    - Consecutive entities
    - Multilingual text with entities
    - Complex realistic scenarios
    - Edge cases (empty, single entity)
    - Configuration compatibility
    """

    def test_simple_mixed_content_order(self, default_tokenizer):
        """Test simple mixed content preserves order."""
        text = "Hello @user world"
        result = default_tokenizer.tokenize(text)

        # Should preserve original order: hello, @user, world
        expected = ["hello", "@user", "world"]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_entities_at_boundaries_order(self, default_tokenizer):
        """Test entities at text boundaries preserve order."""
        text = "@start middle content #end"
        result = default_tokenizer.tokenize(text)

        # Should preserve original order
        expected = ["@start", "middle", "content", "#end"]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_consecutive_entities_order(self, default_tokenizer):
        """Test consecutive entities preserve order."""
        text = "Check @user1 @user2 #tag1 #tag2 content"
        result = default_tokenizer.tokenize(text)

        # Should preserve original order
        expected = ["check", "@user1", "@user2", "#tag1", "#tag2", "content"]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_multilingual_mixed_order(self, default_tokenizer):
        """Test multilingual content with entities preserves order."""
        text = "iPhone用户 loves #apple products"
        result = default_tokenizer.tokenize(text)

        # Should preserve original order with character-level CJK tokenization
        expected = ["iphone", "用", "户", "loves", "#apple", "products"]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_complex_social_media_order(self, default_tokenizer):
        """Test complex realistic social media content preserves order."""
        text = "Just launched @company's new #product! Check it out at https://launch.example.com 🚀"
        result = default_tokenizer.tokenize(text)

        # Should preserve original order (emoji is excluded with default config)
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

    def test_edge_case_order_preservation(self, default_tokenizer):
        """Test order preservation with edge cases."""
        # Test empty input
        assert default_tokenizer.tokenize("") == []

        # Test whitespace only
        assert default_tokenizer.tokenize("   \t\n  ") == []

        # Test single entity
        assert default_tokenizer.tokenize("@user") == ["@user"]
        assert default_tokenizer.tokenize("#hashtag") == ["#hashtag"]
        assert default_tokenizer.tokenize("https://example.com") == ["https://example.com"]

        # Test entities with no surrounding text
        result_entities_only = default_tokenizer.tokenize("@user #hashtag https://example.com")
        expected_entities_only = ["@user", "#hashtag", "https://example.com"]
        assert result_entities_only == expected_entities_only

    def test_configuration_compatibility_order_preservation(self, preserve_case_tokenizer):
        """Test that order preservation works with various configuration options."""
        # Test with case preservation
        text = "Hello @User Check #HashTag"
        result = preserve_case_tokenizer.tokenize(text)
        expected = ["Hello", "@User", "Check", "#HashTag"]
        assert result == expected, f"Expected {expected}, got {result}"

        # Test with social media extraction disabled
        config_no_social = TokenizerConfig(
            extract_hashtags=False, extract_mentions=False, include_urls=False
        )
        tokenizer_no_social = BasicTokenizer(config_no_social)
        text_no_social = "Hello @user check #hashtag"
        result_no_social = tokenizer_no_social.tokenize(text_no_social)
        # Should tokenize as regular words when extraction is disabled
        expected_no_social = ["hello", "user", "check", "hashtag"]
        assert result_no_social == expected_no_social, f"Expected {expected_no_social}, got {result_no_social}"

        # Test with minimum token length
        config_min_length = TokenizerConfig(min_token_length=4)
        tokenizer_min_length = BasicTokenizer(config_min_length)
        text_min_length = "Hi @user check #hashtag long"
        result_min_length = tokenizer_min_length.tokenize(text_min_length)
        # Should preserve order and filter short tokens
        expected_min_length = ["@user", "check", "#hashtag", "long"]
        assert result_min_length == expected_min_length, f"Expected {expected_min_length}, got {result_min_length}"


@pytest.mark.unit
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
        """Test that URLs are completely excluded when extraction is disabled."""
        config = TokenizerConfig(include_urls=False)
        tokenizer = BasicTokenizer(config)
        text = "Visit https://example.com and http://test.org for more info"
        result = tokenizer.tokenize(text)

        # URLs should be completely excluded, not broken into parts
        assert "https://example.com" not in result
        assert "http://test.org" not in result

        # Basic words should still be present
        assert "visit" in result
        assert "and" in result
        assert "for" in result
        assert "more" in result
        assert "info" in result

        # URLs should be completely excluded - no URL components should appear
        url_components = [
            token
            for token in result
            if any(
                comp in token.lower()
                for comp in ["https", "http", "example.com", "test.org"]
            )
        ]
        assert (
            len(url_components) == 0
        ), f"URL components should not appear when include_urls=False: {result}"

    def test_email_extraction_disabled(self):
        """Test email extraction disabled behavior.

        With the fixed implementation, emails should be completely excluded when include_emails=False.
        """
        config = TokenizerConfig(include_emails=False)
        tokenizer = BasicTokenizer(config)
        text = "Contact user@example.com or admin@test.org for help"
        result = tokenizer.tokenize(text)

        # Basic words should be present
        assert "contact" in result
        assert "or" in result
        assert "for" in result
        assert "help" in result

        # Emails should be completely excluded from results
        assert "user@example.com" not in result
        assert "admin@test.org" not in result

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

        Verifies that when include_numeric=False, all numeric tokens (integers, decimals, etc.)
        are properly excluded from tokenization results.
        """
        config = TokenizerConfig(include_numeric=False)
        tokenizer = BasicTokenizer(config)
        text = "I have 123 apples, 45.67 oranges, and 1000 bananas"
        result = tokenizer.tokenize(text)

        # Words should be present
        expected_words = ["i", "have", "apples", "oranges", "and", "bananas"]
        for word in expected_words:
            assert word in result, f"Word '{word}' not found in result: {result}"

        # All numeric tokens should be excluded when include_numeric=False
        numeric_tokens = ["123", "45.67", "1000"]
        for num in numeric_tokens:
            assert (
                num not in result
            ), f"Numeric token '{num}' should not be in result when disabled: {result}"

    def test_all_social_features_disabled(self):
        """Test comprehensive behavior when all social media features are disabled."""
        config = TokenizerConfig(
            extract_hashtags=False,
            extract_mentions=False,
            include_urls=False,
            include_emails=False,
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

        # For hashtags and mentions with extraction disabled, components are tokenized separately
        assert "user" in result  # @ mention becomes regular word
        assert "hashtag" in result  # # hashtag becomes regular word

        # URLs and emails should be completely excluded, not tokenized as components

    def test_feature_independence(self):
        """Test that disabling one feature doesn't affect others."""
        # Disable only hashtags, keep others enabled
        config = TokenizerConfig(
            extract_hashtags=False,  # Disabled
            extract_mentions=True,  # Enabled
            include_urls=True,  # Enabled
            include_emoji=True,  # Enabled
        )
        tokenizer = BasicTokenizer(config)
        text = "Check @user and #hashtag at https://site.com 🎉"
        result = tokenizer.tokenize(text)

        # Should preserve original order with specific expected result
        expected = ["check", "@user", "and", "hashtag", "at", "https://site.com", "🎉"]
        assert result == expected

        # Verify specific feature behavior
        assert "@user" in result, "Mentions should work when enabled"
        assert "https://site.com" in result, "URLs should work when enabled"
        assert "🎉" in result, "Emojis should work when enabled"
        assert "#hashtag" not in result, "Hashtags should be disabled"
        assert (
            "hashtag" in result
        ), "Hashtag content should be tokenized as regular word"


@pytest.mark.integration
class TestBasicTokenizerIntegration:
    """Integration tests with realistic social media content."""

    def test_twitter_like_content(self):
        """Test Twitter-like social media content."""
        tokenizer = BasicTokenizer()
        text = "Just posted a new blog at https://myblog.com! Check it out @followers #blogging #tech 🚀"
        result = tokenizer.tokenize(text)

        # Should tokenize with specific expected result (emoji excluded with default config)
        expected = [
            "just",
            "posted",
            "a",
            "new",
            "blog",
            "at",
            "https://myblog.com",
            "check",
            "it",
            "out",
            "@followers",
            "#blogging",
            "#tech",
        ]
        assert result == expected

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


@pytest.mark.unit
class TestAbbreviationsAndPunctuation:
    """Test abbreviation handling and punctuation edge cases."""

    def test_abbreviations_basic(self):
        """Test basic abbreviation tokenization - abbreviations should stay intact."""
        tokenizer = BasicTokenizer()
        text = "The c.e.o.s met yesterday"
        result = tokenizer.tokenize(text)

        # Abbreviations should be preserved as single tokens
        expected = ["the", "c.e.o.s", "met", "yesterday"]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_abbreviations_with_trailing_period(self):
        """Test abbreviation with trailing sentence period."""
        tokenizer = BasicTokenizer()
        text = "I live in U.S. now"
        result = tokenizer.tokenize(text)

        # Abbreviation should be preserved, period is part of the abbreviation
        expected = ["i", "live", "in", "u.s.", "now"]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_multiple_abbreviations(self):
        """Test multiple abbreviations in the same sentence."""
        tokenizer = BasicTokenizer()
        text = "U.S. and U.K. relations"
        result = tokenizer.tokenize(text)

        # Both abbreviations should be preserved
        expected = ["u.s.", "and", "u.k.", "relations"]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_ellipses_without_punctuation(self):
        """Test ellipses handling - ellipses should be filtered out by default."""
        tokenizer = BasicTokenizer()
        text = "Wait for it..."
        result = tokenizer.tokenize(text)

        # Ellipses should be removed with default config (include_punctuation=False)
        expected = ["wait", "for", "it"]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_chinese_tokenization_regression(self):
        """Test that Chinese character tokenization still works correctly (regression check)."""
        tokenizer = BasicTokenizer()
        text = "你好世界"
        result = tokenizer.tokenize(text)

        # Chinese should still be tokenized character by character
        expected = ["你", "好", "世", "界"]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_contractions_regression(self):
        """Test that contractions are still handled correctly (regression check)."""
        tokenizer = BasicTokenizer()
        text = "I don't think it's ready"
        result = tokenizer.tokenize(text)

        # Contractions should be preserved as single tokens
        expected = ["i", "don't", "think", "it's", "ready"]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_abbreviations_and_contractions_together(self):
        """Test complex sentence with both abbreviations and contractions."""
        tokenizer = BasicTokenizer()
        text = "U.S. citizens don't always agree"
        result = tokenizer.tokenize(text)

        # Both abbreviations and contractions should be preserved
        expected = ["u.s.", "citizens", "don't", "always", "agree"]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_hyphenated_compound_words(self):
        """Test hyphenated compound words are preserved as single tokens."""
        tokenizer = BasicTokenizer()
        text = "self-aware co-founder twenty-one"
        result = tokenizer.tokenize(text)
        expected = ["self-aware", "co-founder", "twenty-one"]
        assert result == expected, f"Expected {expected}, got {result}"

    def test_hyphenated_words_with_context(self):
        """Test hyphenated words in natural sentence context."""
        tokenizer = BasicTokenizer()
        text = "The self-aware AI is state-of-the-art technology"
        result = tokenizer.tokenize(text)

        # Check hyphenated compounds are preserved
        assert "self-aware" in result, f"Expected 'self-aware' in {result}"
        assert "state-of-the-art" in result, f"Expected 'state-of-the-art' in {result}"
        assert "ai" in result
        assert "technology" in result


@pytest.mark.unit
class TestBotDetectionEdgeCases:
    """Edge cases for bot detection and social media anomalies."""

    def test_repeated_characters_preserved(self):
        """Bot-like repeated characters should be preserved."""
        tokenizer = BasicTokenizer()
        text = "WOWWWWW amazing!!!!!!!"
        result = tokenizer.tokenize(text)
        # Should preserve repeated patterns
        assert "wowwwww" in result
        assert "amazing" in result

    def test_mixed_script_brand_names(self):
        """Mixed Latin+CJK in brand names should stay together."""
        tokenizer = BasicTokenizer()
        text = "iPhone用户 loves it"
        result = tokenizer.tokenize(text)
        assert "iphone" in result
        assert "用" in result
        assert "户" in result
        assert "loves" in result
        assert "it" in result

    def test_cashtag_vs_currency(self):
        """Cashtags should be distinguished from currency."""
        tokenizer = BasicTokenizer()
        text = "$AAPL hit $100 today"
        result = tokenizer.tokenize(text)
        assert "$aapl" in result  # Cashtag (lowercased)
        assert "$100" in result  # Currency
        assert "hit" in result
        assert "today" in result

    def test_cashtag_extraction_disabled(self):
        """When extract_cashtags=False, should split into components."""
        config = TokenizerConfig(extract_cashtags=False)
        tokenizer = BasicTokenizer(config)
        text = "$NVDA to the moon"
        result = tokenizer.tokenize(text)
        assert "$nvda" not in result
        assert "nvda" in result  # Should be separate word

    def test_emoji_with_skin_tone_modifier(self):
        """Complex emoji with modifiers."""
        config = TokenizerConfig(include_emoji=True)
        tokenizer = BasicTokenizer(config)
        text = "thumbs up 👍🏽 and 👍🏿"
        result = tokenizer.tokenize(text)
        assert "👍🏽" in result or "👍" in result  # Modifier may separate
        assert "thumbs" in result

    def test_multiple_consecutive_punctuation(self):
        """Multiple punctuation marks in sequence."""
        tokenizer = BasicTokenizer()
        text = "What???!!! Really???"
        result = tokenizer.tokenize(text)
        assert "what" in result
        assert "really" in result
        # Punctuation excluded by default

    def test_mixed_emoji_and_text(self):
        """Emoji interspersed with text."""
        config = TokenizerConfig(include_emoji=True)
        tokenizer = BasicTokenizer(config)
        text = "🔥fire🔥 sale"
        result = tokenizer.tokenize(text)
        assert "fire" in result
        assert "sale" in result
        assert "🔥" in result

    def test_url_with_authentication(self):
        """URL with embedded credentials."""
        tokenizer = BasicTokenizer()
        text = "check https://user:pass@example.com for details"
        result = tokenizer.tokenize(text)
        assert "https://user:pass@example.com" in result
        assert "check" in result

    def test_url_with_query_params(self):
        """URL with complex query string."""
        tokenizer = BasicTokenizer()
        text = "visit https://site.com/path?key=value&foo=bar now"
        result = tokenizer.tokenize(text)
        assert (
            "https://site.com/path?key=value&foo=bar" in result
            or "https://site.com/path" in result
        )
        assert "visit" in result
        assert "now" in result

    def test_repeated_punctuation_with_spaces(self):
        """Spaced punctuation patterns."""
        tokenizer = BasicTokenizer()
        text = "wait . . . what"
        result = tokenizer.tokenize(text)
        assert "wait" in result
        assert "what" in result

    def test_mixed_rtl_ltr_text(self):
        """Arabic (RTL) mixed with English (LTR)."""
        tokenizer = BasicTokenizer()
        text = "مرحبا hello world"
        result = tokenizer.tokenize(text)
        assert "مرحبا" in result
        assert "hello" in result
        assert "world" in result

    def test_script_transition_mid_token(self):
        """Script changes within a token."""
        tokenizer = BasicTokenizer()
        text = "visit北京today"
        result = tokenizer.tokenize(text)
        # Should handle gracefully, exact behavior depends on implementation
        assert len(result) > 0


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
        include_urls=True,
        include_emails=True,
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
