import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from wordscalpel.core import (
    count_occurrences,
    find_all,
    get_positions,
    remove_occurrence,
    remove_occurrence_range,
    remove_all_occurrences,
    replace_occurrence,
    replace_occurrence_range,
    replace_all_occurrences,
    swap_words,
)
from wordscalpel.exceptions import (
    WordscalpelError,
    OccurrenceNotFoundError,
    InvalidRangeError,
    EmptyInputError,
)


# ── count_occurrences ──────────────────────────────────────────────────────────

class TestCountOccurrences:
    def test_basic(self):
        assert count_occurrences("the cat and the dog", "the") == 2

    def test_zero(self):
        assert count_occurrences("hello world", "foo") == 0

    def test_case_sensitive(self):
        assert count_occurrences("The the THE", "the") == 1

    def test_case_insensitive(self):
        assert count_occurrences("The the THE", "the", case_sensitive=False) == 3

    def test_empty_raises(self):
        with pytest.raises(EmptyInputError):
            count_occurrences("", "word")

    def test_whitespace_only_raises(self):
        with pytest.raises(EmptyInputError):
            count_occurrences("   ", "word")

    def test_unicode(self):
        assert count_occurrences("café café latte", "café") == 2

    def test_exception_is_wordscalpel_error(self):
        with pytest.raises(WordscalpelError):
            count_occurrences("", "word")


# ── find_all ───────────────────────────────────────────────────────────────────

class TestFindAll:
    def test_returns_correct_count(self):
        results = find_all("the cat and the dog", "the")
        assert len(results) == 2

    def test_dict_keys(self):
        results = find_all("foo foo", "foo")
        assert set(results[0].keys()) == {"n", "start", "end", "snippet"}

    def test_n_is_1_based(self):
        results = find_all("foo foo foo", "foo")
        assert [r["n"] for r in results] == [1, 2, 3]

    def test_start_end_correct(self):
        results = find_all("the cat and the dog", "the")
        assert results[0]["start"] == 0
        assert results[0]["end"] == 3
        assert results[1]["start"] == 12
        assert results[1]["end"] == 15

    def test_snippet_contains_word(self):
        results = find_all("hello world hello", "hello")
        for r in results:
            assert "hello" in r["snippet"]

    def test_no_match_returns_empty(self):
        assert find_all("hello world", "xyz") == []

    def test_custom_context(self):
        results = find_all("a b c d e f g h i j", "e", context=2)
        assert len(results[0]["snippet"]) <= 4 + len("e")

    def test_empty_raises(self):
        with pytest.raises(EmptyInputError):
            find_all("", "word")


# ── get_positions ──────────────────────────────────────────────────────────────

class TestGetPositions:
    def test_basic(self):
        positions = get_positions("the cat and the dog", "the")
        assert positions == [(0, 3), (12, 15)]

    def test_no_match(self):
        assert get_positions("hello world", "foo") == []

    def test_punctuation_adjacent(self):
        positions = get_positions("word, word. word!", "word")
        assert len(positions) == 3


# ── remove_occurrence ──────────────────────────────────────────────────────────

class TestRemoveOccurrence:
    def test_remove_first(self):
        assert remove_occurrence("the cat and the dog", "the", 1) == "cat and the dog"

    def test_remove_second(self):
        assert remove_occurrence("the cat and the dog", "the", 2) == "the cat and dog"

    def test_remove_with_punctuation(self):
        result = remove_occurrence("error, error, error", "error", 2)
        assert result.count("error") == 2

    def test_n_exceeds_count_raises(self):
        with pytest.raises(OccurrenceNotFoundError) as exc_info:
            remove_occurrence("one two three", "one", 5)
        assert exc_info.value.n == 5
        assert exc_info.value.total == 1

    def test_n_zero_raises(self):
        with pytest.raises(ValueError):
            remove_occurrence("hello hello", "hello", 0)

    def test_n_negative_raises(self):
        with pytest.raises(ValueError):
            remove_occurrence("hello hello", "hello", -1)

    def test_empty_text_raises(self):
        with pytest.raises(EmptyInputError):
            remove_occurrence("", "word", 1)

    def test_case_insensitive(self):
        result = remove_occurrence("Hello hello HELLO", "hello", 2, case_sensitive=False)
        total = result.lower().count("hello")
        assert total == 2


# ── remove_occurrence_range ────────────────────────────────────────────────────

class TestRemoveOccurrenceRange:
    def test_remove_middle_range(self):
        result = remove_occurrence_range("a a a a a", "a", 2, 4)
        remaining = [c for c in result if c == "a"]
        assert len(remaining) == 2

    def test_remove_all_via_range(self):
        result = remove_occurrence_range("x x x", "x", 1, 3)
        assert "x" not in result

    def test_invalid_start_raises(self):
        with pytest.raises(InvalidRangeError):
            remove_occurrence_range("a a a", "a", 0, 2)

    def test_end_exceeds_total_raises(self):
        with pytest.raises(InvalidRangeError):
            remove_occurrence_range("a a a", "a", 1, 10)

    def test_end_before_start_raises(self):
        with pytest.raises(InvalidRangeError):
            remove_occurrence_range("a a a", "a", 3, 1)


# ── remove_all_occurrences ─────────────────────────────────────────────────────

class TestRemoveAllOccurrences:
    def test_removes_all(self):
        result = remove_all_occurrences("the cat and the dog and the bird", "the")
        assert "the" not in result.split()

    def test_no_match_unchanged(self):
        text = "hello world"
        assert remove_all_occurrences(text, "foo") == text


# ── replace_occurrence ─────────────────────────────────────────────────────────

class TestReplaceOccurrence:
    def test_replace_first(self):
        assert replace_occurrence("foo foo foo", "foo", "bar", 1) == "bar foo foo"

    def test_replace_second(self):
        assert replace_occurrence("foo foo foo", "foo", "bar", 2) == "foo bar foo"

    def test_replace_third(self):
        assert replace_occurrence("foo foo foo", "foo", "bar", 3) == "foo foo bar"

    def test_not_found_raises(self):
        with pytest.raises(OccurrenceNotFoundError):
            replace_occurrence("hello world", "foo", "bar", 1)

    def test_empty_replacement(self):
        assert replace_occurrence("hello hello", "hello", "", 1) == "hello"

    def test_empty_text_raises(self):
        with pytest.raises(EmptyInputError):
            replace_occurrence("", "word", "x", 1)


# ── replace_occurrence_range ───────────────────────────────────────────────────

class TestReplaceOccurrenceRange:
    def test_replaces_middle_range(self):
        result = replace_occurrence_range("a a a a a", "a", "X", 2, 4)
        assert result == "a X X X a"

    def test_replaces_single(self):
        result = replace_occurrence_range("foo foo foo", "foo", "bar", 2, 2)
        assert result == "foo bar foo"

    def test_replaces_all_via_range(self):
        result = replace_occurrence_range("x x x", "x", "Y", 1, 3)
        assert result == "Y Y Y"

    def test_invalid_range_raises(self):
        with pytest.raises(InvalidRangeError):
            replace_occurrence_range("a a a", "a", "X", 2, 10)

    def test_empty_text_raises(self):
        with pytest.raises(EmptyInputError):
            replace_occurrence_range("", "word", "x", 1, 2)


# ── replace_all_occurrences ────────────────────────────────────────────────────

class TestReplaceAllOccurrences:
    def test_replaces_all(self):
        result = replace_all_occurrences("foo and foo and foo", "foo", "bar")
        assert result == "bar and bar and bar"

    def test_no_match_unchanged(self):
        text = "hello world"
        assert replace_all_occurrences(text, "xyz", "abc") == text

    def test_case_insensitive(self):
        result = replace_all_occurrences("Foo foo FOO", "foo", "bar", case_sensitive=False)
        assert result == "bar bar bar"


# ── swap_words ─────────────────────────────────────────────────────────────────

class TestSwapWords:
    def test_basic_swap(self):
        result = swap_words("cat chased the dog", "cat", "dog")
        assert result == "dog chased the cat"

    def test_swap_multiple(self):
        result = swap_words("cat and dog and cat and dog", "cat", "dog")
        assert result == "dog and cat and dog and cat"

    def test_no_double_replace(self):
        # "a" → "b" should not make those b's get swapped back to "a"
        result = swap_words("a b a b", "a", "b")
        assert result == "b a b a"

    def test_one_word_absent(self):
        # Only word_a present — should replace all with word_b
        result = swap_words("cat and cat", "cat", "dog")
        assert result == "dog and dog"

    def test_neither_present_unchanged(self):
        text = "hello world"
        assert swap_words(text, "foo", "bar") == text

    def test_identical_words_raises(self):
        with pytest.raises(ValueError):
            swap_words("hello hello", "hello", "hello")

    def test_case_insensitive_swap(self):
        result = swap_words("Cat chased the Dog", "cat", "dog", case_sensitive=False)
        assert "dog" in result.lower() or "cat" in result.lower()

    def test_empty_text_raises(self):
        with pytest.raises(EmptyInputError):
            swap_words("", "cat", "dog")
