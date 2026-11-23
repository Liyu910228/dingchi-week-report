"""Use cases for the customer dictionary administration page."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from django.db import IntegrityError, transaction

from ..dao import (
    find_item_by_id,
    insert_item,
    item_code_exists,
    list_items_by_type,
    soft_delete_item,
    update_item,
)

CUSTOMER_DICT_TYPE = "customer"
_CUSTOMER_CODE_PATTERN = re.compile(r"[A-Za-z0-9]{1,64}")
_CUSTOMER_STATUSES = {"active", "inactive"}


class CustomerNotFoundError(ValueError):
    """The requested customer is missing or has already been deleted."""

    code = "CUSTOMER_NOT_FOUND"


class CustomerConflictError(ValueError):
    """The requested customer operation would violate a uniqueness rule."""

    code = "CUSTOMER_CONFLICT"


def is_system_admin(role_code: str) -> bool:
    """Return whether the active role may manage system settings."""
    return role_code == "system_admin"


def list_customers() -> list[dict[str, Any]]:
    """Return all non-deleted customer rows ordered by sort_order then id."""
    return [_serialize(item) for item in list_items_by_type(dict_type=CUSTOMER_DICT_TYPE)]


@transaction.atomic
def create_customer(*, payload: Mapping[str, Any]) -> dict[str, Any]:
    """Create a new customer dictionary row after validating the payload."""
    code = str(payload.get("dict_code") or "").strip()
    name = str(payload.get("dict_name") or "").strip()
    sort_order = _parse_sort_order(payload.get("sort_order", 0))
    description = str(payload.get("description") or "").strip()
    _validate_create(code=code, name=name, description=description)
    if item_code_exists(dict_type=CUSTOMER_DICT_TYPE, dict_code=code):
        raise CustomerConflictError("客户编号已存在，请使用其他编号。")
    try:
        created = insert_item(
            dict_type=CUSTOMER_DICT_TYPE,
            dict_code=code,
            dict_name=name,
            sort_order=sort_order,
            status="active",
            description=description,
        )
    except IntegrityError as exc:
        raise CustomerConflictError("客户编号已存在，请使用其他编号。") from exc
    return _serialize(created)


@transaction.atomic
def update_customer(*, customer_id: int, payload: Mapping[str, Any]) -> dict[str, Any]:
    """Update an existing customer dictionary row by primary key."""
    existing = find_item_by_id(customer_id)
    if (
        existing is None
        or existing["dict_type"] != CUSTOMER_DICT_TYPE
        or existing["status"] == "deleted"
    ):
        raise CustomerNotFoundError("客户不存在或已被删除。")

    fields: dict[str, Any] = {}
    if "dict_name" in payload:
        name = str(payload.get("dict_name") or "").strip()
        _validate_name(name)
        fields["dict_name"] = name
    if "sort_order" in payload:
        fields["sort_order"] = _parse_sort_order(payload["sort_order"])
    if "status" in payload:
        status = str(payload.get("status") or "").strip()
        _validate_status(status)
        fields["status"] = status
    if "description" in payload:
        description = str(payload.get("description") or "").strip()
        _validate_description(description)
        fields["description"] = description

    if not fields:
        return _serialize(existing)
    return _serialize(update_item(item_id=customer_id, fields=fields))


@transaction.atomic
def soft_delete_customer(*, customer_id: int) -> dict[str, Any]:
    """Soft-delete a customer row and return the persisted values."""
    existing = find_item_by_id(customer_id)
    if (
        existing is None
        or existing["dict_type"] != CUSTOMER_DICT_TYPE
        or existing["status"] == "deleted"
    ):
        raise CustomerNotFoundError("客户不存在或已被删除。")
    return _serialize(soft_delete_item(item_id=customer_id))


def _serialize(item: Mapping[str, Any]) -> dict[str, Any]:
    return {**item, "id": str(item["id"])}


def _validate_create(*, code: str, name: str, description: str) -> None:
    if not code or not name:
        raise ValueError("客户编号和客户名称不能为空。")
    if not _CUSTOMER_CODE_PATTERN.fullmatch(code):
        raise ValueError(
            "客户编号仅支持英文字母和数字，长度为 1–64 个字符。"
        )
    _validate_name(name)
    _validate_description(description)


def _validate_name(name: str) -> None:
    if not name:
        raise ValueError("客户名称不能为空。")
    if len(name) > 128:
        raise ValueError("客户名称不能超过 128 个字符。")


def _validate_status(status: str) -> None:
    if status not in _CUSTOMER_STATUSES:
        raise ValueError("客户状态只能是 active 或 inactive。")


def _validate_description(description: str) -> None:
    if len(description) > 255:
        raise ValueError("客户说明不能超过 255 个字符。")


def _parse_sort_order(value: Any) -> int:
    try:
        sort_order = int(value or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError("排序值必须是非负整数。") from exc
    if sort_order < 0:
        raise ValueError("排序值必须是非负整数。")
    return sort_order
