"""
benchmarks/benchmark.py — Performance tests for wordscalpel.

Run with:  python benchmarks/benchmark.py
"""

import sys
import os
import time
import tempfile
import tracemalloc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import wordscalpel as ws
from wordscalpel.file_ops import process_file, file_count_occurrences


def generate_text(size_mb: int) -> str:
    """Generate a text string of approximately size_mb megabytes."""
    base = "error warning info debug notice critical alert emergency " * 100
    repetitions = (size_mb * 1024 * 1024) // len(base.encode("utf-8")) + 1
    return (base * repetitions)[: size_mb * 1024 * 1024]


def benchmark_string(label: str, text: str, word: str):
    print(f"\n{'─'*50}")
    print(f"  {label}  |  {len(text)/1024/1024:.1f} MB  |  word='{word}'")
    print(f"{'─'*50}")

    # count
    t0 = time.perf_counter()
    count = ws.count_occurrences(text, word)
    print(f"  count_occurrences      : {time.perf_counter()-t0:.4f}s  →  {count} hits")

    # get_positions
    t0 = time.perf_counter()
    positions = ws.get_positions(text, word)
    print(f"  get_positions          : {time.perf_counter()-t0:.4f}s  →  {len(positions)} spans")

    # remove first occurrence
    t0 = time.perf_counter()
    ws.remove_occurrence(text, word, 1)
    print(f"  remove_occurrence(1)   : {time.perf_counter()-t0:.4f}s")

    # remove all
    tracemalloc.start()
    t0 = time.perf_counter()
    ws.remove_all_occurrences(text, word)
    elapsed = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"  remove_all_occurrences : {elapsed:.4f}s  |  peak mem: {peak/1024/1024:.1f} MB")


def benchmark_file(label: str, size_mb: int, word: str):
    print(f"\n{'─'*50}")
    print(f"  FILE: {label}  |  {size_mb} MB  |  word='{word}'")
    print(f"{'─'*50}")

    text = generate_text(size_mb)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(text)
        input_path = f.name

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        output_path = f.name

    try:
        t0 = time.perf_counter()
        count = file_count_occurrences(input_path, word)
        print(f"  file_count_occurrences : {time.perf_counter()-t0:.4f}s  →  {count} hits")

        t0 = time.perf_counter()
        result = process_file(input_path, output_path, word, n=1, operation="remove")
        print(f"  process_file(remove,1) : {time.perf_counter()-t0:.4f}s")

        t0 = time.perf_counter()
        result = process_file(input_path, output_path, word, operation="remove")
        print(f"  process_file(remove all): {time.perf_counter()-t0:.4f}s  →  removed {result['original_count']} hits")
    finally:
        os.unlink(input_path)
        os.unlink(output_path)


def main():
    print("=" * 50)
    print("  wordscalpel benchmark")
    print("=" * 50)

    for size_mb in [1, 5, 10]:
        text = generate_text(size_mb)
        benchmark_string(f"{size_mb}MB string", text, "error")

    for size_mb in [1, 10]:
        benchmark_file(f"{size_mb}MB file", size_mb, "error")

    print(f"\n{'='*50}")
    print("  Benchmark complete.")
    print("=" * 50)


if __name__ == "__main__":
    main()
