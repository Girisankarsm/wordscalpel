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
#  I/O helpers & Streaming Engine
# ─────────────────────────────────────────────────────────────

def _read(path: str) -> str:
    """Read full file (legacy / for file_find)."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()
    if not content.strip():
        raise EmptyInputError(f"file '{path}'")
    return content

def _map_n(global_n: int | tuple[int, int] | None, offset: int, line_count: int) -> int | tuple[int, int] | None:
    """Map a global occurrence target into a local line occurrence target."""
    if global_n is None:
        return None
        
    if isinstance(global_n, int):
        if offset < global_n <= offset + line_count:
            return global_n - offset # 1-based local index
        return -1 # skip
        
    if isinstance(global_n, tuple):
        start, end = global_n
        line_start = max(start, offset + 1)
        line_end = min(end, offset + line_count)
        if line_start <= line_end:
            return (line_start - offset, line_end - offset)
        return -1
        
    return -1

def _process_stream(
    path: str, dest: str, 
    operation: str, word: str, repl: str = "",
    word_b: str = "",
    n: int | tuple[int, int] | None = None,
    case_sensitive: bool = True,
    normalize: bool = True,
    boundary_mode: str = "strict",
    dry_run: bool = False
) -> dict:
    """Process a file line-by-line for memory-safe O(1) mutations."""
    import tempfile
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
        
    os.makedirs(os.path.dirname(os.path.abspath(dest)) or ".", exist_ok=True)
    temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(dest)), text=True)
    
    if dry_run:
        import sys
        sys.stdout.write(f"--- [DRY RUN] {path} ---\n")
        sys.stdout.write(f"+++ [DRY RUN] {dest} ---\n")
    
    original_count = 0
    result_count = 0
    
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as out_fh, \
             open(path, "r", encoding="utf-8") as in_fh:
                 
            # Guard empty files
            first_line = in_fh.read(1)
            if not first_line:
                raise EmptyInputError(f"file '{path}'")
            # reset pointer
            in_fh.seek(0)
            
            for line in in_fh:
                line_count = count(line, word, case_sensitive)
                
                if operation == "swap":
                    if line_count > 0 or count(line, word_b, case_sensitive) > 0:
                        new_line = swap(line, word, word_b, case_sensitive, normalize)
                        if dry_run:
                            import sys
                            sys.stdout.write(f"\033[31m- {line}\033[0m")
                            sys.stdout.write(f"\033[32m+ {new_line}\033[0m")
                        else:
                            out_fh.write(new_line)
                    else:
                        if not dry_run: out_fh.write(line)
                    continue
                    
                if line_count == 0:
                    if not dry_run: out_fh.write(line)
                    continue
                    
                mapped_n = _map_n(n, original_count, line_count)
                original_count += line_count
                
                if mapped_n == -1:
                    if not dry_run: out_fh.write(line)
                    result_count += line_count
                else:
                    if operation == "remove":
                        new_line = remove(line, word, n=mapped_n, case_sensitive=case_sensitive, normalize=normalize, boundary_mode=boundary_mode)
                    else:
                        new_line = replace(line, word, repl, n=mapped_n, case_sensitive=case_sensitive, normalize=normalize, boundary_mode=boundary_mode)
                        
                    result_count += count(new_line, word, case_sensitive)
                    if dry_run:
                        import sys
                        sys.stdout.write(f"\033[31m- {line}\033[0m")
                        sys.stdout.write(f"\033[32m+ {new_line}\033[0m")
                    else:
                        out_fh.write(new_line)
                        
        if not dry_run:
            os.replace(temp_path, dest)
    except Exception:
        os.unlink(temp_path)
        raise
        
    if operation == "swap":
        return {"out": dest}
    return {"original_count": original_count, "result_count": result_count, "out": dest}


# ─────────────────────────────────────────────────────────────
#  Read-only helpers
# ─────────────────────────────────────────────────────────────

def file_count(path: str, word: str, case_sensitive: bool = True) -> int:
    """Count occurrences of *word* in a file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    total = 0
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            total += count(line, word, case_sensitive)
    return total


def file_find(
    path: str, word: str, case_sensitive: bool = True, context: int = 20
) -> list[dict]:
    """Return rich occurrence metadata for *word* in a file."""
    return find(_read(path), word, case_sensitive, context)


def file_positions(
    path: str, word: str, case_sensitive: bool = True
) -> list[tuple[int, int]]:
    """Return ``(start, end)`` positions for every occurrence in a file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    all_pos = []
    current_offset = 0
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line_pos = positions(line, word, case_sensitive)
            if line_pos:
                all_pos.extend([(s + current_offset, e + current_offset) for s, e in line_pos])
            current_offset += len(line)
    return all_pos


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
    boundary_mode: str = "strict",
    dry_run: bool = False,
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
    dest = out or path
    return _process_stream(
        path, dest, "remove", word, n=n, 
        case_sensitive=case_sensitive, normalize=normalize, boundary_mode=boundary_mode, dry_run=dry_run
    )


def file_replace(
    path: str,
    word: str,
    repl: str,
    n: int | tuple[int, int] | None = None,
    out: str | None = None,
    case_sensitive: bool = True,
    normalize: bool = True,
    boundary_mode: str = "strict",
    dry_run: bool = False,
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
    dest = out or path
    return _process_stream(
        path, dest, "replace", word, repl=repl, n=n, 
        case_sensitive=case_sensitive, normalize=normalize, boundary_mode=boundary_mode, dry_run=dry_run
    )


def file_swap(
    path: str,
    word_a: str,
    word_b: str,
    out: str | None = None,
    case_sensitive: bool = True,
    normalize: bool = True,
    dry_run: bool = False,
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
    dest = out or path
    return _process_stream(
        path, dest, "swap", word_a, word_b=word_b, 
        case_sensitive=case_sensitive, normalize=normalize, dry_run=dry_run
    )


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
    boundary_mode: str = "strict",
    dry_run: bool = False,
) -> dict:
    """
    Unified gateway — kept for CLI and backwards compatibility.

    Prefer ``file_remove``, ``file_replace``, or ``file_swap`` for new code.
    """
    _n = (start_n, end_n) if (start_n and end_n) else n

    if operation in ("remove", "remove_range"):
        return file_remove(input_path, word, n=_n, out=output_path, case_sensitive=case_sensitive, normalize=normalize, boundary_mode=boundary_mode, dry_run=dry_run)

    elif operation in ("replace", "replace_range"):
        return file_replace(input_path, word, replacement, n=_n, out=output_path, case_sensitive=case_sensitive, normalize=normalize, boundary_mode=boundary_mode, dry_run=dry_run)

    elif operation == "swap":
        if swap_with is None:
            raise ValueError("swap operation requires swap_with.")
        return file_swap(input_path, word, swap_with, out=output_path, case_sensitive=case_sensitive, normalize=normalize, dry_run=dry_run)

    else:
        valid = ("remove", "remove_range", "replace", "replace_range", "swap")
        raise ValueError(f"Unknown operation '{operation}'. Valid: {valid}")


# Backwards-compatible aliases
file_count_occurrences = file_count
file_find_all          = file_find
file_get_positions     = file_positions
