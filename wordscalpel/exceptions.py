"""
exceptions.py — Custom exception hierarchy for wordscalpel.

All exceptions inherit from WordscalpelError so callers can catch the whole
family with a single ``except WordscalpelError`` clause, or handle individual
cases more precisely.
"""


class WordscalpelError(Exception):
    """Base class for all wordscalpel exceptions."""


class OccurrenceNotFoundError(WordscalpelError):
    """Raised when the requested nth occurrence does not exist in the text."""

    def __init__(self, word: str, n: int, total: int) -> None:
        self.word  = word
        self.n     = n
        self.total = total
        super().__init__(
            f"Occurrence {n} of '{word}' not found. "
            f"The text contains {total} occurrence(s)."
        )


class InvalidRangeError(WordscalpelError):
    """Raised when a (start_n, end_n) range is invalid or exceeds available occurrences."""

    def __init__(self, start: int, end: int, total: int) -> None:
        self.start = start
        self.end   = end
        self.total = total
        super().__init__(
            f"Range [{start}, {end}] is invalid. "
            f"The text contains {total} occurrence(s)."
        )


class EmptyInputError(WordscalpelError):
    """Raised when the input text or file is empty or whitespace-only."""

    def __init__(self, source: str = "input") -> None:
        super().__init__(
            f"The {source} is empty or contains only whitespace. "
            "Please provide valid content."
        )
