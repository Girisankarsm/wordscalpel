"""
plugins.py — Extensible adapter registry for custom formats.

Users can attach custom parsers (like XML or YAML) that seamlessly route 
through the central `ws.process()` flow.
"""

from typing import Callable, Any, Dict

# Central registry for all structural processing adapters
_ADAPTERS: Dict[str, Callable] = {}


def register_adapter(name: str) -> Callable:
    """
    Decorator to register a custom wordscalpel data adapter.

    Example:
        @register_adapter("yaml")
        def process_yaml(data: str, operation: str, word: str, **kwargs) -> str:
            # parse, mutate, rebuild
            return new_yaml
    """
    def decorator(func: Callable) -> Callable:
        _ADAPTERS[name] = func
        return func
    return decorator


def process(
    data: Any,
    operation: str,
    word: str,
    adapter: str,
    **kwargs
) -> Any:
    """
    Unified entry point for structural modifications using registered adapters.
    
    Args:
        data: The input format (file path, raw JSON, Python dict, etc.).
        operation: 'remove', 'replace', 'swap', or 'count'.
        word: The target word to operate on.
        adapter: The format identifier (e.g., 'json', 'csv', 'obj', 'xml').
        **kwargs: Standard parameters (n, repl, word_b, case_sensitive, normalize, etc.)
    """
    if adapter not in _ADAPTERS:
        raise ValueError(
            f"Adapter '{adapter}' not recognized. "
            f"Available integrated adapters: {list(_ADAPTERS.keys())}"
        )
    return _ADAPTERS[adapter](data, operation, word, **kwargs)
