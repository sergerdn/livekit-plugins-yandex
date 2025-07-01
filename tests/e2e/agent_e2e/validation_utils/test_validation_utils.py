#!/usr/bin/env python3
"""Infrastructure Tests for Validation Utils.

Tests for the validation utility functions used in agent E2E tests. This validates the
validation infrastructure itself.
"""

import logging

import pytest

from .validation_utils import (
    validate_expected_transcription,
    validate_russian_transcription,
)

logger = logging.getLogger(__name__)


@pytest.mark.e2e
class TestValidationUtils:
    """Test the validation utility functions."""

    def test_validate_russian_transcription_basic(self) -> None:
        """Test basic Russian transcription validation."""
        logger.info("Testing basic Russian transcription validation")

        # Test valid Russian text
        valid_russian = "Привет, как дела?"
        assert validate_russian_transcription(valid_russian)

        # Test with keywords
        weather_text = "Сегодня хорошая погода"
        assert validate_russian_transcription(weather_text, ["погода"])

        # Test invalid text (no Cyrillic)
        invalid_text = "Hello, how are you?"
        assert not validate_russian_transcription(invalid_text)

        # Test empty text
        assert not validate_russian_transcription("")
        assert not validate_russian_transcription("   ")

        logger.info("Basic Russian transcription validation working correctly")

    def test_validate_russian_transcription_keywords(self) -> None:
        """Test Russian transcription validation with keywords."""
        logger.info("Testing Russian transcription validation with keywords")

        # Test with a single keyword
        text = "Я изучаю русский язык"
        assert validate_russian_transcription(text, ["русский"])
        assert validate_russian_transcription(text, ["язык"])
        assert not validate_russian_transcription(text, ["английский"])

        # Test with multiple keywords
        assert validate_russian_transcription(text, ["русский", "язык"])
        assert validate_russian_transcription(text, ["изучаю", "русский"])
        assert not validate_russian_transcription(text, ["английский", "французский"])

        # Test case-insensitive
        assert validate_russian_transcription(text, ["РУССКИЙ"])
        assert validate_russian_transcription(text, ["Язык"])

        logger.info("Russian transcription keyword validation working correctly")

    def test_validate_russian_transcription_edge_cases(self) -> None:
        """Test Russian transcription validation edge cases."""
        logger.info("Testing Russian transcription validation edge cases")

        # Test mixed languages
        mixed_text = "Hello привет world мир"
        assert validate_russian_transcription(mixed_text)  # Has Cyrillic
        assert validate_russian_transcription(mixed_text, ["привет"])
        # Note: Current implementation finds keywords case-insensitively, so "hello" is found
        assert validate_russian_transcription(mixed_text, ["hello"])  # Latin keyword found

        # Test numbers and punctuation
        text_with_numbers = "У меня 5 книг и 10 ручек"
        assert validate_russian_transcription(text_with_numbers)
        assert validate_russian_transcription(text_with_numbers, ["книг"])

        # Test special characters
        text_with_special = "Привет! Как дела? Всё хорошо."
        assert validate_russian_transcription(text_with_special)
        assert validate_russian_transcription(text_with_special, ["хорошо"])

        logger.info("Russian transcription edge case validation working correctly")

    def test_validate_expected_transcription_basic(self) -> None:
        """Test basic expected transcription validation."""
        logger.info("Testing basic expected transcription validation")

        # Test exact match
        actual = "привет как дела"
        expected = "привет как дела"
        keywords = ["привет", "дела"]
        description = "greeting"

        assert validate_expected_transcription(actual, expected, keywords, description)

        # Test partial match
        actual = "привет как дела меня зовут анна"
        expected = "привет как дела"
        assert validate_expected_transcription(actual, expected, keywords, description)

        # Test no match
        actual = "сегодня хорошая погода"
        assert not validate_expected_transcription(actual, expected, keywords, description)

        logger.info("Basic expected transcription validation working correctly")

    def test_validate_expected_transcription_word_overlap(self) -> None:
        """Test expected transcription validation with word overlap."""
        logger.info("Testing expected transcription validation with word overlap")

        # Test 100% overlap
        actual = "привет как дела"
        expected = "привет как дела"
        keywords = ["привет", "дела"]
        description = "exact match"

        assert validate_expected_transcription(actual, expected, keywords, description)

        # Test 50% overlap (should pass)
        actual = "привет как погода"  # 2/3 words match
        expected = "привет как дела"
        assert validate_expected_transcription(actual, expected, keywords, description)

        # Test less than 50% overlap (should fail)
        actual = "сегодня хорошая погода"  # 0/3 word match
        assert not validate_expected_transcription(actual, expected, keywords, description)

        # Test with extra words (should still pass if core words match)
        actual = "ну привет как дела у тебя"  # 3/3 core words match
        assert validate_expected_transcription(actual, expected, keywords, description)

        logger.info("Expected transcription word overlap validation working correctly")

    def test_validate_expected_transcription_keywords(self) -> None:
        """Test expected transcription validation with keyword requirements."""
        logger.info("Testing expected transcription validation with keywords")

        # Test with all keywords present
        actual = "привет как дела меня зовут анна"
        expected = "привет как дела"
        keywords = ["привет", "дела"]
        description = "greeting with name"

        assert validate_expected_transcription(actual, expected, keywords, description)

        # Test with missing keywords (but still has word overlap)
        actual = "как дела меня зовут анна"  # Missing "привет" but has "дела"
        # This should still pass due to word overlap (2/3 = 66% > 50%)
        assert validate_expected_transcription(actual, expected, keywords, description)

        # Test with partial keywords that are present
        keywords_partial = ["дела"]  # Only one keyword that's actually in the text
        assert validate_expected_transcription(actual, expected, keywords_partial, description)

        # Test case-insensitive keywords
        keywords_upper = ["ПРИВЕТ", "ДЕЛА"]
        actual_mixed = "Привет как ДЕЛА"
        assert validate_expected_transcription(actual_mixed, expected, keywords_upper, description)

        logger.info("Expected transcription keyword validation working correctly")

    def test_validate_expected_transcription_edge_cases(self) -> None:
        """Test expected transcription validation edge cases."""
        logger.info("Testing expected transcription validation edge cases")

        # Test empty inputs
        assert not validate_expected_transcription("", "test", ["test"], "empty actual")
        assert not validate_expected_transcription("test", "", ["test"], "empty expected")
        assert not validate_expected_transcription("test", "test", [], "empty keywords")

        # Test non-Cyrillic text (should fail)
        actual = "hello how are you"
        expected = "hello how are you"
        keywords = ["hello", "you"]
        description = "english text"

        assert not validate_expected_transcription(actual, expected, keywords, description)

        # Test mixed content
        actual = "привет hello как дела"
        expected = "привет как дела"
        keywords = ["привет", "дела"]
        description = "mixed languages"

        assert validate_expected_transcription(actual, expected, keywords, description)

        logger.info("Expected transcription edge case validation working correctly")

    def test_validation_utils_integration(self) -> None:
        """Test integration between validation utilities."""
        logger.info("Testing validation utilities integration")

        # Test that expected transcription validation uses Russian validation internally
        actual = "привет как дела"
        expected = "привет как дела"
        keywords = ["привет", "дела"]
        description = "integration test"

        # This should pass both Russian validation and expected validation
        assert validate_russian_transcription(actual, keywords)
        assert validate_expected_transcription(actual, expected, keywords, description)

        # Test with invalid Russian text
        actual_invalid = "hello how are you"
        assert not validate_russian_transcription(actual_invalid, ["hello"])
        assert not validate_expected_transcription(
            actual_invalid, "hello how are you", ["hello"], "invalid"
        )

        logger.info("Validation utilities integration working correctly")
