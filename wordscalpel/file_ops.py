"""
file_ops.py — File-level operations mirroring the core API.

Every core function has a ``file_*`` counterpart that reads from and writes
to disk. The ``n`` parameter follows the same convention:

    n=None        → all occurrences
    n=int         → nth occurrence (1-based)
    n=(start,end) → inclusive range (1-based)
"""

from __future__ import annotations

import os

from wordscalpel.exceptions import EmptyInputError
from wordscalpel.core import count, find, positions, remove, replace, swap


# ─────────────────────────────────────────────────────────────
#  I/O helpers
# ─────────────────────────────────────────────────────────────

def _read(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()
    if not content.strip():
        raise EmptyInputError(f"file '{path}'")
    return content


def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


# ─────────────────────────────────────────────────────────────
#  Read-only helpers
# ─────────────────────────────────────────────────────────────

def file_count(path: str, word: str, case_sensitive: bool = True) -> int:
    """Count occurrences of *word* in a file."""
    return count(_read(path), word, case_sensitive)


def file_find(
    path: str, word: str, case_sensitive: bool = True, context: int = 20
) -> list[dict]:
    """Return rich occurrence metadata for *word* in a file."""
    return find(_read(path), word, case_sensitive, context)


def file_positions(
    path: str, word: str, case_sensitive: bool = True
) -> list[tuple[int, int]]:
    """Return ``(start, end)`` positions for every occurrence in a file."""
    return positions(_read(path), word, case_sensitive)


# ─────────────────────────────────────────────────────────────
#  Mutating helpers
# ─────────────────────────────────────────────────────────────

def file_remove(
    path: str,
    word: str,
    n: int | tuple[int, int] | None = None,
    out: str | None = None,
    case_sensitive: bool = True,
    normalize: bool = True,
) -> dict:
    """
    Remove occurrences of *word* from a file.

    Args:
        path: Input file path.
        word: Word to remove.
        n: ``None`` → all, ``int`` → nth, ``(s,e)`` → range.
        out: Output path. Defaults to overwriting *path*.
        case_sensitive: Default ``True``.
        normalize: Default ``True``. Cleans up extra spaces after operation.

    Returns:
        ``{"original_count": int, "result_count": int, "out": str}``
    """
    content  = _read(path)
    original = count(content, word, case_sensitive)
    result   = remove(content, word, n=n, case_sensitive=case_sensitive, normalize=normalize)
    dest     = out or path
    _write(dest, result)
    return {"original_count": original, "result_count": count(result, word, case_sensitive), "out": dest}


def file_replace(
    path: str,
    word: str,
    repl: str,
    n: int | tuple[int, int] | None = None,
    out: str | None = None,
    case_sensitive: bool = True,
    normalize: bool = True,
) -> dict:
    """
    Replace occurrences of *word* with *repl* in a file.

    Args:
        path: Input file path.
        word: Word to replace.
        repl: Replacement string.
        n: ``None`` → all, ``int`` → nth, ``(s,e)`` → range.
        out: Output path. Defaults to overwriting *path*.
        case_sensitive: Default ``True``.
        normalize: Default ``True``. Cleans up extra spaces after operation.

    Returns:
        ``{"original_count": int, "result_count": int, "out": str}``
    """
    content  = _read(path)
    original = count(content, word, case_sensitive)
    result   = replace(content, word, repl, n=n, case_sensitive=case_sensitive, normalize=normalize)
    dest     = out or path
    _write(dest, result)
    return {"original_count": original, "result_count": count(result, word, case_sensitive), "out": dest}


def file_swap(
    path: str,
    word_a: str,
    word_b: str,
    out: str | None = None,
    case_sensitive: bool = True,
    normalize: bool = True,
) -> dict:
    """
    Swap *word_a* ↔ *word_b* throughout a file.

    Args:
        path: Input file path.
        word_a: First word.
        word_b: Second word.
        out: Output path. Defaults to overwriting *path*.
        case_sensitive: Default ``True``.
        normalize: Default ``True``. Cleans up extra spaces after operation.

    Returns:
        ``{"out": str}``
    """
    content = _read(path)
    result  = swap(content, word_a, word_b, case_sensitive, normalize=normalize)
    dest    = out or path
    _write(dest, result)
    return {"out": dest}


# ─────────────────────────────────────────────────────────────
#  Unified gateway (kept for CLI + backwards compat)
# ─────────────────────────────────────────────────────────────

def process_file(
    input_path: str,
    output_path: str,
    word: str,
    operation: str = "remove",
    *,
    n: int | None = None,
    replacement: str = "",
    start_n: int | None = None,
    end_n: int | None = None,
    swap_with: str | None = None,
    case_sensitive: bool = True,
    normalize: bool = True,
) -> dict:
    """
    Unified gateway — kept for CLI and backwards compatibility.

    Prefer ``file_remove``, ``file_replace``, or ``file_swap`` for new code.
    """
    _n = (start_n, end_n) if (start_n and end_n) else n

    if operation in ("remove", "remove_range"):
        return file_remove(input_path, word, n=_n, out=output_path, case_sensitive=case_sensitive, normalize=normalize)

    elif operation in ("replace", "replace_range"):
        return file_replace(input_path, word, replacement, n=_n, out=output_path, case_sensitive=case_sensitive, normalize=normalize)

    elif operation == "swap":
        if swap_with is None:
            raise ValueError("swap operation requires swap_with.")
        return file_swap(input_path, word, swap_with, out=output_path, case_sensitive=case_sensitive, normalize=normalize)

    else:
        valid = ("remove", "remove_range", "replace", "replace_range", "swap")
        raise ValueError(f"Unknown operation '{operation}'. Valid: {valid}")


# Backwards-compatible aliases
file_count_occurrences = file_count
file_find_all          = file_find
file_get_positions     = file_positions
