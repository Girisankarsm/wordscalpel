"""
adapters.py — Structured data processing (JSON, CSV, Python Objects).

Provides safe conversion gateways so wordscalpel operations apply strictly
to text values within complex structural formats without breaking syntax.
"""

from __future__ import annotations

import csv
import json
import os
from typing import Any

from wordscalpel.core import count, remove, replace, swap
from wordscalpel.file_ops import _map_n
from wordscalpel.plugins import register_adapter

class _StatefulObjProcessor:
    """Traverses an object and applies tracked word operations across string values."""
    def __init__(
        self,
        operation: str,
        word: str,
        repl: str = "",
        word_b: str = "",
        n: int | tuple[int, int] | None = None,
        case_sensitive: bool = True,
        normalize: bool = True
    ):
        self.operation = operation
        self.word = word
        self.repl = repl
        self.word_b = word_b
        self.n = n
        self.case_sensitive = case_sensitive
        self.normalize = normalize
        self.seen_count = 0

    def traverse(self, obj: Any) -> Any:
        if isinstance(obj, str):
            c = count(obj, self.word, self.case_sensitive)
            if self.operation == "swap":
                if c > 0 or count(obj, self.word_b, self.case_sensitive) > 0:
                    return swap(obj, self.word, self.word_b, self.case_sensitive, self.normalize)
                return obj

            if c == 0:
                return obj

            mapped_n = _map_n(self.n, self.seen_count, c)
            self.seen_count += c

            if mapped_n == -1:
                return obj

            if self.operation == "remove":
                return remove(obj, self.word, n=mapped_n, case_sensitive=self.case_sensitive, normalize=self.normalize)
            elif self.operation == "replace":
                return replace(obj, self.word, self.repl, n=mapped_n, case_sensitive=self.case_sensitive, normalize=self.normalize)
            
            return obj

        if isinstance(obj, list):
            return [self.traverse(item) for item in obj]

        if isinstance(obj, dict):
            # Keys are left untouched, only values are sanitized
            return {k: self.traverse(v) for k, v in obj.items()}

        return obj


# ─────────────────────────────────────────────────────────────
#  Python Object Gateways
# ─────────────────────────────────────────────────────────────

@register_adapter("obj")
def process_obj_adapter(obj: Any, operation: str, word: str, **kwargs) -> Any:
    """Central gateway for object tree manipulation via the plugin router."""
    if operation == "count":
        p = _StatefulObjProcessor("count", word, **kwargs)
        # Traverse does not return count structurally. For counts, we run a custom path.
        # Wait, if count is requested centrally, we can return the seen_count after traversing it!
        p.traverse(obj)
        return p.seen_count
    else:
        p = _StatefulObjProcessor(operation, word, **kwargs)
        return p.traverse(obj)

def remove_obj(obj: Any, word: str, n: int | tuple[int, int] | None = None, case_sensitive: bool = True, normalize: bool = True) -> Any:
    """Recursively clean occurrences of word from all string values in dict/list."""
    p = _StatefulObjProcessor("remove", word, n=n, case_sensitive=case_sensitive, normalize=normalize)
    return p.traverse(obj)

def replace_obj(obj: Any, word: str, repl: str, n: int | tuple[int, int] | None = None, case_sensitive: bool = True, normalize: bool = True) -> Any:
    """Recursively replace occurrences of word in all string values in dict/list."""
    p = _StatefulObjProcessor("replace", word, repl=repl, n=n, case_sensitive=case_sensitive, normalize=normalize)
    return p.traverse(obj)


# ─────────────────────────────────────────────────────────────
#  JSON String Gateways
# ─────────────────────────────────────────────────────────────

@register_adapter("json")
def process_json_adapter(json_str: str, operation: str, word: str, **kwargs) -> str:
    """Safely parse JSON, traverse globally, and rebuild JSON."""
    data = json.loads(json_str)
    # Re-route to the obj adapter handling!
    processed = process_obj_adapter(data, operation, word, **kwargs)
    
    # If the user requested count, we don't rebuild json. Just return the integer.
    if operation == "count":
        return processed
        
    return json.dumps(processed)

def remove_json(json_str: str, word: str, n: int | tuple[int, int] | None = None, case_sensitive: bool = True, normalize: bool = True, **json_kwargs) -> str:
    """Safely parse JSON, remove word from its strings globally, and rebuild JSON."""
    data = json.loads(json_str)
    processed = remove_obj(data, word, n=n, case_sensitive=case_sensitive, normalize=normalize)
    return json.dumps(processed, **json_kwargs)


def replace_json(json_str: str, word: str, repl: str, n: int | tuple[int, int] | None = None, case_sensitive: bool = True, normalize: bool = True, **json_kwargs) -> str:
    """Safely parse JSON, replace word in its strings globally, and rebuild JSON."""
    data = json.loads(json_str)
    processed = replace_obj(data, word, repl, n=n, case_sensitive=case_sensitive, normalize=normalize)
    return json.dumps(processed, **json_kwargs)


# ─────────────────────────────────────────────────────────────
#  CSV Streaming Gateways
# ─────────────────────────────────────────────────────────────

@register_adapter("csv")
def process_csv_adapter(
    data: dict[str, str], # Uses a dict wrapper mapping keys for CSV arguments
    operation: str, word: str, **kwargs
) -> None:
    """
    Stream a CSV line-by-line, targeting operations either to a specific column globally,
    or across all cells. Memory remains O(1) safe.
    
    Expected `data` struct format: {"in_path": "input.csv", "out_path": "output.csv"}
    """
    import tempfile
    
    in_path = data.get("in_path")
    if not in_path:
        raise ValueError("Missing 'in_path' in data payload for CSV adapter.")
    out_path = data.get("out_path", in_path)
    column = kwargs.pop("column", None)
    repl = kwargs.pop("repl", "")
    n = kwargs.pop("n", None)
    case_sensitive = kwargs.pop("case_sensitive", True)
    normalize = kwargs.pop("normalize", True)
    
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    temp_fd, temp_file = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(out_path)), text=True)

    p = _StatefulObjProcessor(operation, word, repl=repl, n=n, case_sensitive=case_sensitive, normalize=normalize)

    try:
        with open(in_path, mode="r", encoding="utf-8", newline="") as infile, \
             os.fdopen(temp_fd, mode="w", encoding="utf-8", newline="") as outfile:
            
            reader = csv.reader(infile)
            writer = csv.writer(outfile)

            header = None
            col_index = None

            if isinstance(column, str):
                header = next(reader, None)
                if header is None:
                    raise ValueError(f"CSV file '{in_path}' is empty, cannot resolve column name.")
                writer.writerow(header)
                try:
                    col_index = header.index(column)
                except ValueError:
                    raise ValueError(f"Column '{column}' not found in CSV header.")
            elif isinstance(column, int):
                col_index = column

            for row in reader:
                if col_index is not None:
                    if col_index < len(row):
                        row[col_index] = p.traverse(row[col_index])
                    writer.writerow(row)
                else:
                    writer.writerow(p.traverse(row))

        os.replace(temp_file, out_path)
    except Exception:
        os.unlink(temp_file)
        raise

def process_csv(in_path: str, out_path: str, operation: str, word: str, **kwargs) -> None:
    """Convenience functional wrapper for the CSV adapter."""
    process_csv_adapter({"in_path": in_path, "out_path": out_path}, operation, word, **kwargs)
