"""Stable dictionary capabilities for other backend business modules."""

from __future__ import annotations

from typing import Any

from .services.items import get_active_items, has_active_code


def list_active_dictionary_items(dict_type: str) -> list[dict[str, Any]]:
    """List selectable options for a dictionary type."""
    return get_active_items(dict_type=dict_type)


def is_active_dictionary_code(dict_type: str, dict_code: str) -> bool:
    """Check whether a dictionary code is active."""
    return has_active_code(dict_type=dict_type, dict_code=dict_code)
