# wordscalpel 🔪

Surgical, occurrence-based word manipulation for strings and files.

Log sanitization, document redaction, and content pipelines often need precise word-level control that Python's stdlib doesn't provide. **`wordscalpel`** solves that, now with intelligent space normalization!

[![PyPI version](https://badge.fury.io/py/wordscalpel.svg)](https://pypi.org/project/wordscalpel/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install wordscalpel
```

---

## ⚡️ Python API (v2.0)

For `v2.0`, the API was drastically simplified while backwards-compatibility was retained. Intelligent space normalization prevents dangling spaces when deleting words inside code/log files.

```python
import wordscalpel as ws

text = "the cat sat on the mat near the hat"

# Count occurrences
ws.count(text, "the")           # → 3

# Find with rich context
ws.find(text, "the", context=10) # Provides exact character metadata

# Remove occurrences (Default: intelligently cleans extra spaces!)
ws.remove(text, "the")                  # Remove all: "cat sat on mat near hat"
ws.remove(text, "the", n=2)             # Remove 2nd occurrence
ws.remove(text, "the", n=(1, 2))        # Remove range (1st and 2nd)

# Replace occurrences
ws.replace(text, "the", "a")            # Replace all
ws.replace(text, "the", "a", n=2)       # Replace 2nd occurrence
ws.replace(text, "the", "a", n=(1, 2))  # Replace range (1st and 2nd)

# Swap words simultaneously (avoids double-replace traps)
ws.swap("cat chased the dog", "cat", "dog") # → "dog chased the cat"

# Un-normalized raw mode (protects exact space-counts)
ws.remove("a b a c", "a", normalize=False)  # → " b  c "
```

## 📄 File Operations

Every core function has a `file_*` counterpart that safely mutates files on disk while retaining space layout structure!

```python
from wordscalpel.file_ops import file_count, file_remove, file_replace, file_swap

# Count in file
file_count("input.txt", "error")

# Remove 2nd occurrence and save
file_remove("input.txt", "error", n=2, out="output.txt")

# Replace all
file_replace("input.txt", "error", "warning")

# Swap variables
file_swap("input.py", "user_id", "client_id")
```

## 💻 CLI Tools

```bash
# Remove 2nd occurrence of "error" from a file
wordscalpel remove --word "error" --n 2 --file input.txt --output out.txt

# Remove a specific range
wordscalpel remove --word "error" --range 2 5 --file input.txt

# Replace all occurrences
wordscalpel replace --word "foo" --with "bar" --all --file input.txt 

# Swap two words universally
wordscalpel swap --word "cat" --swap-with "dog" --file input.txt

# Count occurrences
wordscalpel count --word "error" --file input.txt

# Extract occurrences with 20px context string limits
wordscalpel find --word "Exception" --context 20 --file input.txt

# Pipe from stdin instantly
echo "hello world hello" | wordscalpel remove --word "hello" --n 1
```

## 🛡️ Error Handling

```python
from wordscalpel.exceptions import WordscalpelError, OccurrenceNotFoundError

try:
    ws.remove("hello world", "hello", n=5)
except OccurrenceNotFoundError as e:
    print(e)  # Occurrence 5 of 'hello' not found. Total occurrences found: 1
```

## Running Tests
```bash
pip install pytest
python3 -m pytest tests/ -v
```

## License
MIT
