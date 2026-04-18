"""
wordscalpel — Surgical, occurrence-based word manipulation for strings and files.

Quick start
-----------
    >>> import wordscalpel as ws

    >>> ws.count("foo foo foo", "foo")
    3

    >>> ws.remove("foo foo foo", "foo", n=2)
    'foo  foo'

    >>> ws.replace("foo foo foo", "foo", "bar", n=(1, 2))
    'bar bar foo'

    >>> ws.swap("cat chased the dog", "cat", "dog")
    'dog chased the cat'
"""

from wordscalpel.core import (
    count,
    find,
    positions,
    remove,
    replace,
    swap,
    # backwards-compatible aliases
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
from wordscalpel.file_ops import (
    process_file,
    file_count,
    file_find,
    file_positions,
    file_remove,
    file_replace,
    file_swap,
)
from wordscalpel.exceptions import (
    WordscalpelError,
    OccurrenceNotFoundError,
    InvalidRangeError,
    EmptyInputError,
)

__version__ = "2.0.0"
__author__  = "wordscalpel contributors"
__license__ = "MIT"

__all__ = [
    # ── core ──────────────────────────────
    "count",
    "find",
    "positions",
    "remove",
    "replace",
    "swap",
    # ── file ops ──────────────────────────
    "process_file",
    "file_count",
    "file_find",
    "file_positions",
    "file_remove",
    "file_replace",
    "file_swap",
    # ── exceptions ────────────────────────
    "WordscalpelError",
    "OccurrenceNotFoundError",
    "InvalidRangeError",
    "EmptyInputError",
]
