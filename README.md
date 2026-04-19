<div align="center">
  <h1>wordscalpel 🔪</h1>
  <p><strong>A streaming, occurrence-aware, structure-safe text transformation engine with configurable boundary semantics.</strong></p>

  [![PyPI version](https://badge.fury.io/py/wordscalpel.svg)](https://pypi.org/project/wordscalpel/)
  [![Python Versions](https://img.shields.io/pypi/pyversions/wordscalpel.svg)](https://pypi.org/project/wordscalpel/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

  <p>
    <strong>Designed for large-scale, structure-safe text transformations with streaming support.</strong>
  </p>
  <p>
    <em>Log sanitization, document redaction, and content pipelines often need precise structure-aware control that Python's standard library doesn't provide. <br><code>wordscalpel</code> solves that permanently.</em>
  </p>
</div>

---

## ⚡️ Why `wordscalpel`?

Standard Python `.replace()` and Regex are blind—they either replace everything, the first occurrence, or require complex error-prone patterns. `wordscalpel` allows you to target **exact integer occurrences or ranges**, swap terms cleanly, and stream 10GB files without breaking a sweat.

### 🆚 How it compares

| Feature | `wordscalpel` | Standard `.replace()` | Regex (`re.sub`) | `sed` (CLI) |
| :--- | :---: | :---: | :---: | :---: |
| **Replace $N$th occurrence** | ✅ Native | ❌ No | ⚠️ Complex logic | ⚠️ Awkward syntax |
| **Replace occurrence ranges** | ✅ Native | ❌ No | ❌ No | ⚠️ Very hard |
| **Simultaneous A↔B Swap** | ✅ Native | ❌ Breaks on overlap | ⚠️ Custom functions | ⚠️ Difficult |
| **Smart Space Cleanup** | ✅ Native | ❌ No | ⚠️ Manual patterns | ⚠️ Manual patterns |
| **O(1) Memory Streaming** | ✅ Native | ❌ Loads entire string | ❌ Loads entire string | ✅ Yes |
| **Indentation Safe** | ✅ Yes | ❌ Blind wipe | ⚠️ Manual Lookbehinds | ⚠️ Blind wipe |

### 🎯 Core Capabilities
*   **Intelligent Space Normalization:** Safely swallows extra bounding spaces upon deletion to preserve code alignments, without breaking text structure or indentation.
*   **O(1) Streaming Engine:** Never loads massive `.log` or `.sql` files into memory; files are operated on dynamically chunk-by-chunk for unmatched speed.
*   **Configurable Safety Levels:** Synchronous word-swapping and flexible boundary modes predictably prevent collision traps and unintended syntax breaks.
*   **Zero Dependencies**: Built entirely using the Python standard library.

### 🛡️ Structured Capability Matrix

`wordscalpel` handles formats with precise awareness of structural memory scale constraints:

| Format   | Streaming Engine | Memory Safe | Notes |
| :------- | :--------------: | :---------: | :---- |
| **Text Files (.log, .txt)** | ✅ Yes | ✅ Yes | O(1) Memory row-by-row stream. Perfect for standard massive files. |
| **CSV**          | ✅ Yes | ✅ Yes | O(1) streaming using standard Python `csv` module row-by-row parsing. |
| **JSON**         | ❌ No  | ⚠️ Varies | Uses `json.loads`. Safe for metadata chunks, but loads structure into memory. |
| **Python Objects** | N/A | ⚠️ Varies | Safely recurses through loaded active memory objects. |

---

## 📦 Installation

```bash
pip install wordscalpel
```

---

## 💻 CLI Tools

Use the `wordscalpel` binary right from your terminal without opening Python! Note that every command safely supports `--dry-run` to print colorized terminal diffs of changes without mutating disk files.

```bash
# 1. Remove the EXACT 2nd occurrence of 'error' from a log
wordscalpel remove --word "error" --n 2 --file server.log --output out.log

# 2. Re-write the first 5 occurrences (Preview changes safely via dry-run)
wordscalpel replace --word "DEBUG" --with "INFO" --range 1 5 --file server.log --dry-run

# 3. Swap variables simultaneously everywhere
wordscalpel swap --word "cat" --swap-with "dog" --file input.txt

# 4. Extract instances with beautiful surrounding context arrays (-c chars)
wordscalpel find --word "Exception" --context 20 --file server.log
```

---

## 🐍 Python API (v2.0)

Using the newly refined minimal API, text operations are universally effortless.

```python
import wordscalpel as ws

text = "the cat sat on the mat near the hat"

# 🔍 Inspection
ws.count(text, "the")               # → 3
ws.find(text, "the", context=10)    # → Metadata and surrounding substrings

# ✂️ Smart Removal (Intelligently drops adjacent spaces natively)
ws.remove(text, "the", n=2)         # → "the cat sat on mat near the hat"
ws.remove(text, "the", n=(1, 2))    # Remove 1st and 2nd

# 🔁 Swaps & Replacements
ws.replace(text, "the", "a", n=2)   # → "the cat sat on a mat near the hat"
ws.swap("cat chased dog", "cat", "dog") # → "dog chased cat"
```

### 🛡️ Configurable Boundary Semantics
Boundary modes define how wordscalpel interacts precisely with surrounding punctuation.

- `strict` (default):
  Safe, literal word removal. No punctuation or structure is modified.

- `safe`:
  Removes only trailing safe punctuation (`: , . ; ! ?`). Fully structure-safe.

- `balanced`:
  Removes paired punctuation only when perfectly mirrored (e.g., `(ERROR)`).
  ⚠️ May affect syntax in structured code (e.g., commas, arguments).

- `aggressive`:
  Removes all adjacent punctuation without validation.
  ⚠️ Unsafe for code. Intended for raw text/log cleanup only.

### Advanced Control (Space Targeting)
```python
# Un-normalized raw mode (protects exact consecutive space-counts)
ws.remove("a b a c", "a", normalize=False)  # → " b  c "
```

---

## 🔌 Plugin Architecture (Extensibility)

`wordscalpel` is an ecosystem. You can register custom data format adapters internally without modifying the library!

```python
import wordscalpel as ws
import yaml

@ws.register_adapter("yaml")
def process_yaml(data: str, operation: str, word: str, **kwargs):
    parsed = yaml.safe_load(data)
    # Securely invoke our internal recursive object traverser
    processed = ws.remove_obj(parsed, word, **kwargs)
    return yaml.dump(processed)

# Now it flows securely through the main engine routing
ws.process(open("config.yml").read(), "remove", "password", adapter="yaml")
```

---

## 📄 File Stream Operations

Every core function has a `file_*` counterpart that safely mutates massive files on disk using efficient O(1) memory pipelines.

```python
from wordscalpel.file_ops import file_count, file_remove, file_replace, file_swap

# ONE KILLER DEMO: Safely scrub 15,000 deep targets off a 5GB 
# streaming file without loading it to RAM or affecting JSON brackets
file_remove("massive_production_export.log", "PASSWORD_HASH", n=(10000, 25000))

# Change specific variable definitions safely inline
file_replace("input.py", "deprecated_var", "new_var", n=2)
```

---

## 🛡️ Error Safety (Exceptions)
Strict adherence to safe typing and predictable error catching:

```python
from wordscalpel.exceptions import WordscalpelError, OccurrenceNotFoundError

try:
    ws.remove("hello world", "hello", n=5)
except OccurrenceNotFoundError as e:
    print(e)  # "Occurrence 5 of 'hello' not found. Total occurrences found: 1"
```

## Running Tests
Developed via TDD. 100% Core coverage.
```bash
pip install pytest
pytest tests/ -v
```

## License
MIT
