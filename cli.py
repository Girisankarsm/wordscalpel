#!/usr/bin/env python3
"""
cli.py — Command-line interface for wordscalpel.

Usage examples
--------------
  # Count occurrences in a file
  wordscalpel count --word error --file app.log

  # Find all with surrounding context
  wordscalpel find --word error --file app.log

  # Remove the 2nd occurrence (stdin → stdout)
  echo "foo foo foo" | wordscalpel remove --word foo --n 2

  # Remove a range from a file in-place
  wordscalpel remove --word error --range 2 5 --file app.log

  # Replace every occurrence in a file, write to new file
  wordscalpel replace --word foo --with bar --all --file in.txt --output out.txt

  # Replace a range
  wordscalpel replace --word foo --with bar --range 1 3 --file in.txt

  # Swap two words throughout a file
  wordscalpel swap --word cat --with dog --file story.txt

  # Show character positions
  wordscalpel positions --word error --file app.log
"""

from __future__ import annotations

import argparse
import sys

import wordscalpel as ws
from wordscalpel.exceptions import WordscalpelError


# ─────────────────────────────────────────────────────────────
#  Subcommand handlers
# ─────────────────────────────────────────────────────────────

def cmd_count(args: argparse.Namespace) -> None:
    if args.file:
        count = ws.file_count_occurrences(
            args.file, args.word, not args.ignore_case
        )
    else:
        count = ws.count_occurrences(
            _stdin(), args.word, not args.ignore_case
        )
    print(f"'{args.word}' appears {count} time(s).")


def cmd_find(args: argparse.Namespace) -> None:
    text = _read_source(args)
    matches = ws.find_all(text, args.word, not args.ignore_case, context=args.context)
    if not matches:
        print(f"No occurrences of '{args.word}' found.")
        return
    for m in matches:
        print(f"  #{m['n']:>3}  chars {m['start']}–{m['end']}  …{m['snippet']}…")


def cmd_positions(args: argparse.Namespace) -> None:
    text = _read_source(args)
    positions = ws.get_positions(text, args.word, not args.ignore_case)
    if not positions:
        print(f"No occurrences of '{args.word}' found.")
        return
    for i, (s, e) in enumerate(positions, 1):
        print(f"  #{i:>3}  chars {s}–{e}")


def cmd_remove(args: argparse.Namespace) -> None:
    cs = not args.ignore_case

    if args.file:
        out = args.output or args.file
        op, kw = _remove_op_kwargs(args)
        result = ws.process_file(
            args.file, out, args.word, operation=op, case_sensitive=cs, **kw
        )
        removed = result["original_count"] - result["result_count"]
        print(f"Removed {removed} occurrence(s). Output: {result['output_path']}")
    else:
        text = _stdin()
        print(_remove_inline(text, args.word, args, cs))


def cmd_replace(args: argparse.Namespace) -> None:
    cs          = not args.ignore_case
    replacement = getattr(args, "with") or ""

    if args.file:
        out = args.output or args.file
        op, kw = _replace_op_kwargs(args, replacement)
        result = ws.process_file(
            args.file, out, args.word, operation=op, case_sensitive=cs, **kw
        )
        changed = result["original_count"] - result["result_count"]
        print(f"Replaced {result['original_count'] - result['result_count']} occurrence(s). "
              f"Output: {result['output_path']}")
    else:
        text = _stdin()
        print(_replace_inline(text, args.word, replacement, args, cs))


def cmd_swap(args: argparse.Namespace) -> None:
    swap_with = getattr(args, "with")
    cs = not args.ignore_case

    if args.file:
        out = args.output or args.file
        result = ws.process_file(
            args.file, out, args.word,
            operation="swap", swap_with=swap_with, case_sensitive=cs,
        )
        print(f"Swapped '{args.word}' ↔ '{swap_with}'. Output: {result['output_path']}")
    else:
        print(ws.swap_words(_stdin(), args.word, swap_with, cs))


# ─────────────────────────────────────────────────────────────
#  Internal helpers
# ─────────────────────────────────────────────────────────────

def _stdin() -> str:
    return sys.stdin.read()


def _read_source(args: argparse.Namespace) -> str:
    if args.file:
        from wordscalpel.file_ops import _read_file
        return _read_file(args.file)
    return _stdin()


def _remove_op_kwargs(args: argparse.Namespace) -> tuple[str, dict]:
    if args.range:
        return "remove_range", {"start_n": args.range[0], "end_n": args.range[1]}
    if args.all:
        return "remove", {}
    return "remove", {"n": args.n}


def _replace_op_kwargs(args: argparse.Namespace, replacement: str) -> tuple[str, dict]:
    if args.range:
        return "replace_range", {
            "replacement": replacement,
            "start_n": args.range[0],
            "end_n": args.range[1],
        }
    if args.all:
        return "replace", {"replacement": replacement}
    return "replace", {"n": args.n, "replacement": replacement}


def _remove_inline(text: str, word: str, args: argparse.Namespace, cs: bool) -> str:
    if args.range:
        return ws.remove_occurrence_range(text, word, args.range[0], args.range[1], cs)
    if args.all:
        return ws.remove_all_occurrences(text, word, cs)
    return ws.remove_occurrence(text, word, args.n, cs)


def _replace_inline(
    text: str, word: str, replacement: str, args: argparse.Namespace, cs: bool
) -> str:
    if args.range:
        return ws.replace_occurrence_range(
            text, word, replacement, args.range[0], args.range[1], cs
        )
    if args.all:
        return ws.replace_all_occurrences(text, word, replacement, cs)
    return ws.replace_occurrence(text, word, replacement, args.n, cs)


# ─────────────────────────────────────────────────────────────
#  Argument parser
# ─────────────────────────────────────────────────────────────

def _common_args(p: argparse.ArgumentParser, *, has_output: bool = False) -> None:
    """Attach --word, --file, --ignore-case (and optionally --output) to a subparser."""
    p.add_argument("--word",        required=True, help="Target word")
    p.add_argument("--file",        metavar="PATH", help="Input file (omit to read stdin)")
    p.add_argument("--ignore-case", action="store_true", help="Case-insensitive matching")
    if has_output:
        p.add_argument("--output", metavar="PATH",
                       help="Output file (default: overwrite --file)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wordscalpel",
        description="Surgical, occurrence-based word manipulation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--version", action="version", version=f"wordscalpel {ws.__version__}"
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    # ── count ─────────────────────────────────────────────────
    p_count = sub.add_parser("count", help="Count word occurrences")
    _common_args(p_count)

    # ── find ──────────────────────────────────────────────────
    p_find = sub.add_parser("find", help="Show each occurrence with surrounding context")
    _common_args(p_find)
    p_find.add_argument("--context", type=int, default=20, metavar="N",
                        help="Characters of context on each side (default: 20)")

    # ── positions ─────────────────────────────────────────────
    p_pos = sub.add_parser("positions", help="Show character positions of each occurrence")
    _common_args(p_pos)

    # ── remove ────────────────────────────────────────────────
    p_rm = sub.add_parser("remove", help="Remove word occurrence(s)")
    _common_args(p_rm, has_output=True)
    grp_rm = p_rm.add_mutually_exclusive_group()
    grp_rm.add_argument("--n",     type=int, default=1, metavar="N",
                        help="Occurrence index to remove (default: 1)")
    grp_rm.add_argument("--all",   action="store_true", help="Remove all occurrences")
    grp_rm.add_argument("--range", type=int, nargs=2, metavar=("START", "END"),
                        help="Remove occurrences START through END (inclusive)")

    # ── replace ───────────────────────────────────────────────
    p_rep = sub.add_parser("replace", help="Replace word occurrence(s)")
    _common_args(p_rep, has_output=True)
    p_rep.add_argument("--with", dest="with", default="", metavar="TEXT",
                       help="Replacement string")
    grp_rep = p_rep.add_mutually_exclusive_group()
    grp_rep.add_argument("--n",     type=int, default=1, metavar="N",
                         help="Occurrence index to replace (default: 1)")
    grp_rep.add_argument("--all",   action="store_true", help="Replace all occurrences")
    grp_rep.add_argument("--range", type=int, nargs=2, metavar=("START", "END"),
                         help="Replace occurrences START through END (inclusive)")

    # ── swap ──────────────────────────────────────────────────
    p_swap = sub.add_parser("swap", help="Swap two words throughout the text")
    _common_args(p_swap, has_output=True)
    p_swap.add_argument("--with", dest="with", required=True, metavar="WORD",
                        help="The word to swap with --word")

    return parser


# ─────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────

def main() -> None:
    parser = build_parser()
    args   = parser.parse_args()

    dispatch = {
        "count":     cmd_count,
        "find":      cmd_find,
        "positions": cmd_positions,
        "remove":    cmd_remove,
        "replace":   cmd_replace,
        "swap":      cmd_swap,
    }

    try:
        dispatch[args.command](args)
    except WordscalpelError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as exc:
        print(f"File error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"Unexpected error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
