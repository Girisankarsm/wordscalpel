# Changelog

All notable changes to `wordscalpel` will be documented in this file.
This project follows [Semantic Versioning](https://semver.org/).

---

## [1.0.0] - 2024-01-01

### Added
- `count_occurrences()` — count how many times a word appears
- `get_positions()` — get character spans of all occurrences
- `remove_occurrence()` — remove the nth occurrence
- `remove_occurrence_range()` — remove a range of occurrences
- `remove_all_occurrences()` — remove every occurrence
- `replace_occurrence()` — replace the nth occurrence
- `replace_all_occurrences()` — replace every occurrence
- `process_file()` — apply any operation to a file
- `file_count_occurrences()` — count occurrences in a file
- `file_get_positions()` — get positions from a file
- CLI with `remove`, `replace`, `count`, `positions` commands
- Custom exceptions: `OccurrenceNotFoundError`, `InvalidRangeError`, `EmptyInputError`
- Full pytest test suite with edge case coverage
- Benchmark suite for 1MB, 5MB, 10MB inputs
