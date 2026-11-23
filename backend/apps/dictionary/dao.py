"""Data access for the single-table static dictionary."""

from __future__ import annotations

from typing import Any

from .models import DictionaryItem

_ITEM_FIELDS = (
    "id",
    "dict_type",
    "dict_code",
    "dict_name",
    "dict_value",
    "description",
    "status",
    "sort_order",
)


def list_active_items(*, dict_type: str) -> list[dict[str, Any]]:
    """Return active options for one dictionary type using Django ORM."""
    return list(
        DictionaryItem.objects.filter(dict_type=dict_type, status="active")
        .order_by("sort_order", "id")
        .values(*_ITEM_FIELDS)
    )


def active_code_exists(*, dict_type: str, dict_code: str) -> bool:
    """Check that a code is currently selectable in a dictionary type."""
    return DictionaryItem.objects.filter(
        dict_type=dict_type,
        dict_code=dict_code,
        status="active",
    ).exists()


def list_items_by_type(*, dict_type: str, include_deleted: bool = False) -> list[dict[str, Any]]:
    """Return dictionary items for a type, excluding soft-deleted rows by default."""
    queryset = DictionaryItem.objects.filter(dict_type=dict_type)
    if not include_deleted:
        queryset = queryset.exclude(status="deleted")
    return list(queryset.order_by("sort_order", "id").values(*_ITEM_FIELDS))


def find_item_by_id(item_id: int) -> dict[str, Any] | None:
    """Return a single dictionary item row by primary key, or None."""
    return DictionaryItem.objects.filter(id=item_id).values(*_ITEM_FIELDS).first()


def item_code_exists(
    *,
    dict_type: str,
    dict_code: str,
    exclude_id: int | None = None,
) -> bool:
    """Check whether a (dict_type, dict_code) pair is already used."""
    queryset = DictionaryItem.objects.filter(dict_type=dict_type, dict_code=dict_code).exclude(
        status="deleted"
    )
    if exclude_id is not None:
        queryset = queryset.exclude(id=exclude_id)
    return queryset.exists()


def insert_item(
    *,
    dict_type: str,
    dict_code: str,
    dict_name: str,
    sort_order: int,
    status: str = "active",
    description: str = "",
    dict_value: str = "",
) -> dict[str, Any]:
    """Create a dictionary row and return the persisted values."""
    item = DictionaryItem.objects.create(
        dict_type=dict_type,
        dict_code=dict_code,
        dict_name=dict_name,
        dict_value=dict_value,
        description=description,
        status=status,
        sort_order=sort_order,
    )
    return DictionaryItem.objects.filter(id=item.id).values(*_ITEM_FIELDS).first() or {}


def update_item(*, item_id: int, fields: dict[str, Any]) -> dict[str, Any]:
    """Update the given fields on a dictionary row and return the persisted values."""
    DictionaryItem.objects.filter(id=item_id).update(**fields, updated_at=_now())
    return DictionaryItem.objects.filter(id=item_id).values(*_ITEM_FIELDS).first() or {}


def soft_delete_item(*, item_id: int) -> dict[str, Any]:
    """Mark a dictionary row as deleted and return the persisted values."""
    DictionaryItem.objects.filter(id=item_id).exclude(status="deleted").update(
        status="deleted", updated_at=_now()
    )
    return DictionaryItem.objects.filter(id=item_id).values(*_ITEM_FIELDS).first() or {}


def _now() -> Any:
    """Return the current timestamp without importing django.utils at module load."""
    from django.utils import timezone

    return timezone.now()
