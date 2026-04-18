import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from wordscalpel.core import (
    count_occurrences,
    remove_occurrence,
    replace_occurrence,
    remove_all_occurrences,
)
from wordscalpel.exceptions import EmptyInputError, OccurrenceNotFoundError


class TestEdgeCases:

    # ── Punctuation adjacency ──────────────────────────────────────────────────

    def test_word_with_comma(self):
        assert count_occurrences("error, error, error", "error") == 3

    def test_word_with_period(self):
        assert count_occurrences("end. The end. The end.", "end") == 3

    def test_word_with_exclamation(self):
        assert count_occurrences("go! go! go!", "go") == 3

    def test_word_with_quotes(self):
        assert count_occurrences('"hello" and "hello"', "hello") == 2

    def test_partial_word_not_matched(self):
        # "there" should not match "the"
        assert count_occurrences("there is the thing", "the") == 1

    def test_substring_not_matched(self):
        assert count_occurrences("football is fun", "foot") == 0

    # ── Unicode ───────────────────────────────────────────────────────────────

    def test_unicode_word(self):
        assert count_occurrences("naïve naïve approach", "naïve") == 2

    def test_emoji_adjacent(self):
        # emoji are non-alphanumeric, word should still match
        text = "hello 👋 hello 👋"
        assert count_occurrences(text, "hello") == 2

    # ── Single word text ──────────────────────────────────────────────────────

    def test_single_word_text(self):
        assert count_occurrences("hello", "hello") == 1

    def test_remove_only_occurrence(self):
        result = remove_occurrence("hello", "hello", 1)
        assert result == ""

    # ── Repeated identical characters ─────────────────────────────────────────

    def test_all_same_word(self):
        text = "a a a a a"
        assert count_occurrences(text, "a") == 5

    def test_remove_middle_of_five(self):
        result = remove_occurrence("a a a a a", "a", 3)
        parts = result.split()
        assert len(parts) == 4

    # ── Large string performance ───────────────────────────────────────────────

    def test_large_string(self):
        text = ("error warning info debug " * 10000).strip()
        assert count_occurrences(text, "error") == 10000

    def test_large_string_remove_first(self):
        text = ("word " * 5000).strip()
        result = remove_occurrence(text, "word", 1)
        assert count_occurrences(result, "word") == 4999

    # ── Replace edge cases ────────────────────────────────────────────────────

    def test_replace_with_longer_word(self):
        result = replace_occurrence("go go go", "go", "running", 2)
        assert result == "go running go"

    def test_replace_with_empty_string(self):
        result = replace_occurrence("foo bar foo", "foo", "", 1)
        assert result.startswith("bar")

    def test_normalize_preserves_newlines(self):
        result = remove_occurrence("\n foo bar \n", "bar", 1)
        # Should NOT strip the newlines or inner boundaries
        assert result == "\n foo \n"

    def test_smart_space_preserves_internal_structure(self):
        # Swallows exactly the adjacent bounds, but leaves the user's manual tabs/spaces alone!
        result = remove_occurrence("a \t  foo \t b", "foo", 1)
        assert result == "a \t  \t b"

    def test_normalize_empty_result(self):
        result = remove_occurrence("a a", "a", n=None)  # remove all 'a's
        assert result == ""  # should not be " "

    def test_replace_all_preserves_non_target(self):
        result = replace_occurrence("cat bat cat", "cat", "dog", 1)
        assert "bat" in result
        assert result.count("cat") == 1

    # ── Error message quality ─────────────────────────────────────────────────

    def test_error_message_contains_word(self):
        with pytest.raises(OccurrenceNotFoundError) as exc_info:
            remove_occurrence("hello world", "hello", 5)
        assert "hello" in str(exc_info.value)
        assert "5" in str(exc_info.value)
        assert "1" in str(exc_info.value)  # total

    def test_empty_error_message_contains_source(self):
        with pytest.raises(EmptyInputError) as exc_info:
            count_occurrences("", "word")
        assert "text" in str(exc_info.value).lower()
