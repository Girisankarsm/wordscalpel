"""
core.py — Surgical, occurrence-based word manipulation.

Public API (6 functions)
------------------------
    count(text, word)                       → int
    find(text, word, context=20)            → list[dict]
    positions(text, word)                   → list[tuple]

    remove(text, word, n=None)              → str
    replace(text, word, repl, n=None)       → str
    swap(text, word_a, word_b)              → str

The ``n`` parameter follows a single convention across remove/replace:
    n=None        → all occurrences
    n=int         → that specific occurrence (1-based)
    n=(start,end) → that inclusive range (1-based)
"""

from __future__ import annotations

from wordscalpel.utils import find_all_spans, validate_text
from wordscalpel.exceptions import (
    OccurrenceNotFoundError,
    InvalidRangeError,
    EmptyInputError,
)


# ─────────────────────────────────────────────────────────────
#  Internal helpers
# ─────────────────────────────────────────────────────────────

def _spans(text: str, word: str, case_sensitive: bool) -> list[tuple[int, int]]:
    validate_text(text)
    return find_all_spans(text, word, case_sensitive)


def _resolve_n(
    spans: list[tuple[int, int]],
    word: str,
    n: int | tuple[int, int] | None,
) -> list[tuple[int, int]]:
    """
    Resolve the ``n`` parameter to a concrete list of target spans.

    n=None        → every span
    n=int         → single span at index n-1
    n=(start,end) → slice spans[start-1:end]
    """
    total = len(spans)

    if n is None:
        return spans

    if isinstance(n, tuple):
        s, e = n
        if s < 1 or e < s:
            raise InvalidRangeError(s, e, total)
        if s > total or e > total:
            raise InvalidRangeError(s, e, total)
        return spans[s - 1 : e]

    # n is a plain int
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    if n > total:
        raise OccurrenceNotFoundError(word, n, total)
    return [spans[n - 1]]


def _delete(text: str, spans: list[tuple[int, int]], smart_space: bool = False) -> str:
    chars = list(text)
    for s, e in reversed(spans):
        if smart_space:
            left_space = s > 0 and text[s-1] in ' \t'
            right_space = e < len(text) and text[e] in ' \t'
            
            if left_space and right_space:
                e += 1  # swallow right space
            elif right_space and (s == 0 or text[s-1] == '\n'):
                e += 1  # swallow right space
            elif left_space and (e == len(text) or text[e] == '\n'):
                # swallow left space ONLY if it isn't pure indentation
                is_indent = True
                for i in range(s-1, -1, -1):
                    if text[i] == '\n':
                        break
                    if text[i] not in ' \t':
                        is_indent = False
                        break
                if not is_indent:
                    s -= 1
        del chars[s:e]
    return "".join(chars)


def _substitute(
    text: str, spans: list[tuple[int, int]], repl: str, smart_space: bool = False
) -> str:
    if repl == "" and smart_space:
        return _delete(text, spans, smart_space=True)
        
    result, offset = text, 0
    for s, e in spans:
        s += offset
        e += offset
        result = result[:s] + repl + result[e:]
        offset += len(repl) - (e - s)
    return result


# ─────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────

def count(text: str, word: str, case_sensitive: bool = True) -> int:
    """
    Return how many times *word* appears as a whole word in *text*.

    Args:
        text: Input string.
        word: Word to count.
        case_sensitive: Default ``True``.

    Returns:
        Integer count.

    Raises:
        EmptyInputError: If *text* is empty.

    Example:
        >>> count("the cat and the dog", "the")
        2
    """
    return len(_spans(text, word, case_sensitive))


def find(
    text: str,
    word: str,
    case_sensitive: bool = True,
    context: int = 20,
) -> list[dict]:
    """
    Return rich metadata for every occurrence of *word*.

    Each item is a dict::

        {"n": int, "start": int, "end": int, "snippet": str}

    Args:
        text: Input string.
        word: Word to find.
        case_sensitive: Default ``True``.
        context: Characters of surrounding text to include in each snippet.

    Raises:
        EmptyInputError: If *text* is empty.

    Example:
        >>> find("foo bar foo", "foo")
        [{"n": 1, "start": 0, "end": 3, "snippet": "foo bar foo"},
         {"n": 2, "start": 8, "end": 11, "snippet": "bar foo"}]
    """
    all_spans = _spans(text, word, case_sensitive)
    results = []
    for i, (s, e) in enumerate(all_spans, start=1):
        snip_s = max(0, s - context)
        snip_e = min(len(text), e + context)
        results.append({"n": i, "start": s, "end": e, "snippet": text[snip_s:snip_e]})
    return results


def positions(
    text: str, word: str, case_sensitive: bool = True
) -> list[tuple[int, int]]:
    """
    Return ``(start, end)`` character positions for every occurrence of *word*.

    Args:
        text: Input string.
        word: Word to find.
        case_sensitive: Default ``True``.

    Raises:
        EmptyInputError: If *text* is empty.

    Example:
        >>> positions("the cat and the dog", "the")
        [(0, 3), (12, 15)]
    """
    return _spans(text, word, case_sensitive)


def remove(
    text: str,
    word: str,
    n: int | tuple[int, int] | None = None,
    case_sensitive: bool = True,
    normalize: bool = True,
) -> str:
    """
    Remove occurrences of *word* from *text*.

    The ``n`` parameter controls which occurrences are targeted:

    - ``n=None``      — remove **all** occurrences  *(default)*
    - ``n=2``         — remove the **2nd** occurrence
    - ``n=(2, 4)``    — remove occurrences **2 through 4** (inclusive)

    Args:
        text: Input string.
        word: Word to remove.
        n: Targeting selector (see above).
        case_sensitive: Default ``True``.

    Returns:
        Modified string.

    Raises:
        EmptyInputError: If *text* is empty.
        ValueError: If ``n`` is an int < 1.
        OccurrenceNotFoundError: If the specified occurrence doesn't exist.
        InvalidRangeError: If the range is out of bounds.

    Examples:
        >>> remove("foo foo foo", "foo")          # all
        '  '
        >>> remove("foo foo foo", "foo", n=2)     # 2nd only
        'foo  foo'
        >>> remove("foo foo foo", "foo", n=(1,2)) # 1st and 2nd
        '  foo'
    """
    all_spans = _spans(text, word, case_sensitive)
    target    = _resolve_n(all_spans, word, n)
    return _delete(text, target, smart_space=normalize)


def replace(
    text: str,
    word: str,
    repl: str,
    n: int | tuple[int, int] | None = None,
    case_sensitive: bool = True,
    normalize: bool = True,
) -> str:
    """
    Replace occurrences of *word* with *repl*.

    The ``n`` parameter controls which occurrences are targeted:

    - ``n=None``      — replace **all** occurrences  *(default)*
    - ``n=2``         — replace the **2nd** occurrence
    - ``n=(2, 4)``    — replace occurrences **2 through 4** (inclusive)

    Args:
        text: Input string.
        word: Word to replace.
        repl: Replacement string.
        n: Targeting selector (see above).
        case_sensitive: Default ``True``.

    Returns:
        Modified string.

    Raises:
        EmptyInputError: If *text* is empty.
        ValueError: If ``n`` is an int < 1.
        OccurrenceNotFoundError: If the specified occurrence doesn't exist.
        InvalidRangeError: If the range is out of bounds.

    Examples:
        >>> replace("foo foo foo", "foo", "bar")          # all
        'bar bar bar'
        >>> replace("foo foo foo", "foo", "bar", n=2)     # 2nd only
        'foo bar foo'
        >>> replace("foo foo foo", "foo", "bar", n=(1,2)) # 1st and 2nd
        'bar bar foo'
    """
    all_spans = _spans(text, word, case_sensitive)
    target    = _resolve_n(all_spans, word, n)
    return _substitute(text, target, repl, smart_space=normalize)


def swap(
    text: str,
    word_a: str,
    word_b: str,
    case_sensitive: bool = True,
    normalize: bool = True,
) -> str:
    """
    Simultaneously swap every occurrence of *word_a* with *word_b* and vice-versa.

    Both substitutions happen in a single pass — no word is double-replaced.

    Args:
        text: Input string.
        word_a: First word.
        word_b: Second word.
        case_sensitive: Default ``True``.

    Returns:
        Modified string.

    Raises:
        EmptyInputError: If *text* is empty.
        ValueError: If *word_a* and *word_b* are identical.

    Example:
        >>> swap("cat chased the dog", "cat", "dog")
        'dog chased the cat'
    """
    validate_text(text)
    if word_a == word_b:
        raise ValueError("word_a and word_b must be different.")

    tagged = (
        [(s, e, "A") for s, e in find_all_spans(text, word_a, case_sensitive)]
        + [(s, e, "B") for s, e in find_all_spans(text, word_b, case_sensitive)]
    )
    if not tagged:
        return text

    result, offset = text, 0
    for s, e, tag in sorted(tagged, key=lambda x: x[0]):
        s += offset
        e += offset
        new = word_b if tag == "A" else word_a
        result = result[:s] + new + result[e:]
        offset += len(new) - (e - s)
    return result


# ─────────────────────────────────────────────────────────────
#  Backwards-compatible aliases (not in __all__)
# ─────────────────────────────────────────────────────────────

count_occurrences        = count
find_all                 = find
get_positions            = positions

def remove_occurrence(text, word, n, case_sensitive=True, normalize=True):
    return remove(text, word, n=n, case_sensitive=case_sensitive, normalize=normalize)

def remove_occurrence_range(text, word, start_n, end_n, case_sensitive=True, normalize=True):
    return remove(text, word, n=(start_n, end_n), case_sensitive=case_sensitive, normalize=normalize)

def remove_all_occurrences(text, word, case_sensitive=True, normalize=True):
    return remove(text, word, case_sensitive=case_sensitive, normalize=normalize)

def replace_occurrence(text, word, replacement, n, case_sensitive=True, normalize=True):
    return replace(text, word, replacement, n=n, case_sensitive=case_sensitive, normalize=normalize)

def replace_occurrence_range(text, word, replacement, start_n, end_n, case_sensitive=True, normalize=True):
    return replace(text, word, replacement, n=(start_n, end_n), case_sensitive=case_sensitive, normalize=normalize)

def replace_all_occurrences(text, word, replacement, case_sensitive=True, normalize=True):
    return replace(text, word, replacement, case_sensitive=case_sensitive, normalize=normalize)

swap_words = swap
