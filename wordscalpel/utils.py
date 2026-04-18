import re


def build_word_pattern(word: str, case_sensitive: bool = True) -> re.Pattern:
    """
    Build a regex pattern that matches a whole word, ignoring surrounding punctuation.

    Args:
        word: The word to search for.
        case_sensitive: Whether the match should be case-sensitive.

    Returns:
        Compiled regex pattern.
    """
    escaped = re.escape(word)
    # Match word surrounded by non-alphanumeric chars or string boundaries
    pattern = r'(?<![a-zA-Z0-9])' + escaped + r'(?![a-zA-Z0-9])'
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile(pattern, flags)


def find_all_spans(text: str, word: str, case_sensitive: bool = True) -> list:
    """
    Find all (start, end) spans of a word in the text.

    Args:
        text: The input string.
        word: The word to find.
        case_sensitive: Whether matching should be case-sensitive.

    Returns:
        List of (start, end) tuples.
    """
    pattern = build_word_pattern(word, case_sensitive)
    return [match.span() for match in pattern.finditer(text)]


def validate_text(text: str) -> None:
    """
    Validate that the text is not empty.

    Args:
        text: Input string to validate.

    Raises:
        EmptyInputError: If the text is empty or whitespace-only.
    """
    from wordscalpel.exceptions import EmptyInputError
    if not text or not text.strip():
        raise EmptyInputError("text")
