# wordscalpel 🔪

> Surgical, occurrence-based word manipulation for strings and files.

Log sanitization, document redaction, and content pipelines often need precise word-level control that Python's stdlib doesn't provide. `wordscalpel` solves that.

---

## Installation

```bash
pip install wordscalpel
# or from source:
git clone https://github.com/yourname/wordscalpel
cd wordscalpel && pip install -e .
```

---

## Quick Start

```python
import wordscalpel as ws

text = "the cat sat on the mat near the hat"

# Count occurrences
ws.count_occurrences(text, "the")           # → 3

# Get character positions
ws.get_positions(text, "the")               # → [(0,3), (15,18), (28,31)]

# Remove the 2nd occurrence
ws.remove_occurrence(text, "the", 2)        # → "the cat sat on  mat near the hat"

# Remove occurrences 1 through 2
ws.remove_occurrence_range(text, "the", 1, 2)

# Remove all occurrences
ws.remove_all_occurrences(text, "the")

# Replace the 2nd occurrence
ws.replace_occurrence(text, "the", "a", 2) # → "the cat sat on a mat near the hat"

# Replace all occurrences
ws.replace_all_occurrences(text, "the", "a")

# Case-insensitive mode
ws.count_occurrences("The the THE", "the", case_sensitive=False)  # → 3
```

---

## File Operations

```python
from wordscalpel.file_ops import process_file, file_count_occurrences

# Count in file
file_count_occurrences("input.txt", "error")

# Remove 2nd occurrence and save
process_file("input.txt", "output.txt", "error", n=2, operation="remove")

# Replace all
process_file("input.txt", "output.txt", "error", operation="replace", replacement="warning")

# Remove range
process_file("input.txt", "output.txt", "error", operation="remove_range", start_n=2, end_n=4)
```

---

## CLI

```bash
# Remove 2nd occurrence of "error" from a file
wordscalpel remove --word "error" --n 2 --file input.txt --output out.txt

# Remove all occurrences
wordscalpel remove --word "error" --all --file input.txt --output out.txt

# Replace all occurrences
wordscalpel replace --word "foo" --with "bar" --all --file input.txt --output out.txt

# Replace 1st occurrence
wordscalpel replace --word "foo" --with "bar" --n 1 --file input.txt --output out.txt

# Count occurrences
wordscalpel count --word "error" --file input.txt

# Show character positions
wordscalpel positions --word "error" --file input.txt

# Case-insensitive
wordscalpel count --word "error" --file input.txt --ignore-case

# Pipe from stdin
echo "hello world hello" | wordscalpel remove --word "hello" --n 1
```

---

## Error Handling

```python
from wordscalpel.exceptions import OccurrenceNotFoundError, InvalidRangeError, EmptyInputError

try:
    ws.remove_occurrence("hello world", "hello", 5)
except OccurrenceNotFoundError as e:
    print(e)  # Occurrence 5 of 'hello' not found. Total occurrences found: 1

try:
    ws.remove_occurrence_range("a a a", "a", 2, 10)
except InvalidRangeError as e:
    print(e)  # Range [2, 10] is invalid. Total occurrences found: 3

try:
    ws.count_occurrences("", "word")
except EmptyInputError as e:
    print(e)  # The text is empty.
```

---

## API Reference

| Function | Description |
|---|---|
| `count_occurrences(text, word, case_sensitive)` | Count word occurrences |
| `get_positions(text, word, case_sensitive)` | Get (start, end) spans |
| `remove_occurrence(text, word, n, case_sensitive)` | Remove nth occurrence |
| `remove_occurrence_range(text, word, start, end, case_sensitive)` | Remove range |
| `remove_all_occurrences(text, word, case_sensitive)` | Remove all |
| `replace_occurrence(text, word, replacement, n, case_sensitive)` | Replace nth |
| `replace_all_occurrences(text, word, replacement, case_sensitive)` | Replace all |
| `process_file(in, out, word, n, operation, ...)` | File-level operations |
| `file_count_occurrences(path, word, case_sensitive)` | Count in file |
| `file_get_positions(path, word, case_sensitive)` | Positions in file |

---

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

## Running Benchmarks

```bash
python benchmarks/benchmark.py
```

---

## License

MIT
