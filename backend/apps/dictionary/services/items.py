"""Use cases for reading static dictionary options."""

from __future__ import annotations

import re
from typing import Any

from ..dao import active_code_exists, list_active_items

_dict_type_pattern = re.compile(r"^[a-z][a-z0-9_]*$")


class InvalidDictionaryTypeError(ValueError):
    """Raised when a caller supplies a malformed dictionary type."""

    code = "INVALID_DICTIONARY_TYPE"


def get_active_items(*, dict_type: str) -> list[dict[str, Any]]:
    """Return the active dictionary options for a validated type."""
    _validate_dict_type(dict_type)
    items = list_active_items(dict_type=dict_type)
    for item in items:
        item["id"] = str(item["id"])
    return items


def has_active_code(*, dict_type: str, dict_code: str) -> bool:
    """Return whether a code can be used by a business configuration."""
    _validate_dict_type(dict_type)
    return active_code_exists(dict_type=dict_type, dict_code=dict_code)


def _validate_dict_type(dict_type: str) -> None:
    if not dict_type or len(dict_type) > 64 or not _dict_type_pattern.fullmatch(dict_type):
        raise InvalidDictionaryTypeError("字典类型必须使用小写字母、数字和下划线。")
