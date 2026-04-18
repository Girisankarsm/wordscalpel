import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from wordscalpel.file_ops import (
    process_file,
    file_count_occurrences,
    file_find_all,
    file_get_positions,
)
from wordscalpel.exceptions import EmptyInputError, OccurrenceNotFoundError


@pytest.fixture
def sample_file(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text(
        "the quick brown fox jumps over the lazy dog and the fox ran away"
    )
    return str(f)


@pytest.fixture
def output_file(tmp_path):
    return str(tmp_path / "output.txt")


# ── process_file ───────────────────────────────────────────────────────────────

class TestProcessFile:
    def test_remove_nth(self, sample_file, output_file):
        result = process_file(sample_file, output_file, "the", n=2, operation="remove")
        assert result["original_count"] == 3
        assert result["result_count"] == 2

    def test_remove_all(self, sample_file, output_file):
        result = process_file(sample_file, output_file, "the", operation="remove")
        assert result["result_count"] == 0

    def test_remove_range(self, sample_file, output_file):
        result = process_file(
            sample_file, output_file, "the",
            operation="remove_range", start_n=1, end_n=2,
        )
        assert result["result_count"] == 1

    def test_replace_nth(self, sample_file, output_file):
        process_file(
            sample_file, output_file, "fox",
            n=1, operation="replace", replacement="cat",
        )
        content = open(output_file).read()
        assert "cat" in content

    def test_replace_all(self, sample_file, output_file):
        process_file(
            sample_file, output_file, "fox",
            operation="replace", replacement="cat",
        )
        content = open(output_file).read()
        assert "fox" not in content
        assert content.count("cat") == 2

    def test_replace_range(self, sample_file, output_file):
        # "the" appears 3 times; replace occurrences 1–2
        process_file(
            sample_file, output_file, "the",
            operation="replace_range", replacement="a",
            start_n=1, end_n=2,
        )
        content = open(output_file).read()
        assert content.count("the") == 1

    def test_swap(self, sample_file, output_file):
        process_file(
            sample_file, output_file, "fox",
            operation="swap", swap_with="dog",
        )
        content = open(output_file).read()
        # original had 2 fox, 1 dog → result should have 1 fox, 2 dog
        assert content.count("fox") == 1
        assert content.count("dog") == 2

    def test_result_dict_has_standard_keys(self, sample_file, output_file):
        result = process_file(sample_file, output_file, "the", operation="remove")
        assert "original_count" in result
        assert "result_count" in result
        assert "out" in result

    def test_file_not_found(self, output_file):
        with pytest.raises(FileNotFoundError):
            process_file("nonexistent.txt", output_file, "word")

    def test_empty_file_raises(self, tmp_path, output_file):
        empty = tmp_path / "empty.txt"
        empty.write_text("")
        with pytest.raises(EmptyInputError):
            process_file(str(empty), output_file, "word")

    def test_unknown_operation(self, sample_file, output_file):
        with pytest.raises(ValueError):
            process_file(sample_file, output_file, "the", operation="explode")

    def test_swap_missing_swap_with(self, sample_file, output_file):
        with pytest.raises(ValueError):
            process_file(sample_file, output_file, "fox", operation="swap")

    def test_swap_missing_swap_with_raises(self, sample_file, output_file):
        with pytest.raises(ValueError):
            process_file(sample_file, output_file, "the", operation="swap")


# ── file_count_occurrences ─────────────────────────────────────────────────────

class TestFileCountOccurrences:
    def test_count(self, sample_file):
        assert file_count_occurrences(sample_file, "the") == 3

    def test_count_zero(self, sample_file):
        assert file_count_occurrences(sample_file, "xyz") == 0

    def test_case_insensitive(self, tmp_path):
        f = tmp_path / "mixed.txt"
        f.write_text("The the THE")
        assert file_count_occurrences(str(f), "the", case_sensitive=False) == 3


# ── file_find_all ──────────────────────────────────────────────────────────────

class TestFileFindAll:
    def test_returns_list(self, sample_file):
        results = file_find_all(sample_file, "fox")
        assert isinstance(results, list)
        assert len(results) == 2

    def test_dict_structure(self, sample_file):
        results = file_find_all(sample_file, "fox")
        assert set(results[0].keys()) == {"n", "start", "end", "snippet"}

    def test_no_match_empty(self, sample_file):
        assert file_find_all(sample_file, "elephant") == []


# ── file_get_positions ─────────────────────────────────────────────────────────

class TestFileGetPositions:
    def test_positions(self, sample_file):
        positions = file_get_positions(sample_file, "fox")
        assert len(positions) == 2

    def test_no_match(self, sample_file):
        assert file_get_positions(sample_file, "elephant") == []
