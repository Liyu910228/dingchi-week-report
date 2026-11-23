from __future__ import annotations

import pytest
from django.db import IntegrityError

from apps.dictionary.models import DictionaryItem
from apps.dictionary.services.customers import (
    CustomerConflictError,
    CustomerNotFoundError,
    create_customer,
    is_system_admin,
    list_customers,
    soft_delete_customer,
    update_customer,
)


@pytest.mark.django_db
@pytest.mark.parametrize("code", ["C_001", "C.001", "C-001", "客户1", "Ｃ001", "C 001"])
def test_customer_code_rejects_non_ascii_alphanumeric_characters(code) -> None:
    with pytest.raises(ValueError, match="客户编号仅支持"):
        create_customer(payload={"dict_code": code, "dict_name": "客户"})
    assert not DictionaryItem.objects.filter(dict_type="customer").exists()


@pytest.mark.django_db
def test_customer_lengths_match_database_limits() -> None:
    code_limit = DictionaryItem._meta.get_field("dict_code").max_length
    name_limit = DictionaryItem._meta.get_field("dict_name").max_length
    created = create_customer(payload={"dict_code": "A1" * 32, "dict_name": "客" * name_limit})
    assert len(created["dict_code"]) == code_limit
    with pytest.raises(ValueError, match="客户编号仅支持"):
        create_customer(payload={"dict_code": "A" * (code_limit + 1), "dict_name": "客户"})
    with pytest.raises(ValueError, match="客户名称不能超过"):
        create_customer(payload={"dict_code": "C002", "dict_name": "客" * (name_limit + 1)})
    with pytest.raises(ValueError, match="客户名称不能超过"):
        update_customer(
            customer_id=int(created["id"]), payload={"dict_name": "客" * (name_limit + 1)}
        )
    stored = DictionaryItem.objects.get(id=int(created["id"]))
    assert stored.dict_name == "客" * name_limit


@pytest.mark.django_db
def test_is_system_admin_recognises_only_admin_role() -> None:
    assert is_system_admin("system_admin") is True
    assert is_system_admin("president") is False
    assert is_system_admin("delivery_specialist") is False


@pytest.mark.django_db
def test_list_customers_returns_active_and_inactive_rows_in_order() -> None:
    DictionaryItem.objects.create(
        dict_type="customer", dict_code="C001", dict_name="客户一", sort_order=20
    )
    DictionaryItem.objects.create(
        dict_type="customer", dict_code="C002", dict_name="客户二", sort_order=10
    )
    DictionaryItem.objects.create(
        dict_type="customer",
        dict_code="C003",
        dict_name="客户三",
        sort_order=5,
        status="inactive",
    )
    DictionaryItem.objects.create(
        dict_type="customer", dict_code="C004", dict_name="客户四", status="deleted"
    )
    DictionaryItem.objects.create(
        dict_type="role_scope", dict_code="self", dict_name="无关字典"
    )

    items = list_customers()
    assert [item["dict_code"] for item in items] == ["C003", "C002", "C001"]
    assert all(item["id"].isdigit() for item in items)
    assert all(item["dict_type"] == "customer" for item in items)


@pytest.mark.django_db
def test_create_customer_validates_required_fields_and_format() -> None:
    with pytest.raises(ValueError, match="客户编号和客户名称不能为空。"):
        create_customer(payload={"dict_code": "", "dict_name": ""})
    with pytest.raises(ValueError, match="客户编号仅支持"):
        create_customer(payload={"dict_code": "!bad", "dict_name": "客户"})
    with pytest.raises(ValueError, match="客户编号仅支持"):
        create_customer(payload={"dict_code": "-bad", "dict_name": "客户"})
    with pytest.raises(ValueError, match="客户编号仅支持"):
        create_customer(payload={"dict_code": "a" * 65, "dict_name": "客户"})
    with pytest.raises(ValueError, match="客户名称不能超过"):
        create_customer(payload={"dict_code": "C001", "dict_name": "x" * 129})
    with pytest.raises(ValueError, match="客户说明不能超过"):
        create_customer(
            payload={"dict_code": "C001", "dict_name": "客户", "description": "x" * 256}
        )
    with pytest.raises(ValueError, match="排序值必须是非负整数"):
        create_customer(payload={"dict_code": "C001", "dict_name": "客户", "sort_order": -1})


@pytest.mark.django_db
def test_create_customer_rejects_duplicate_code() -> None:
    DictionaryItem.objects.create(
        dict_type="customer", dict_code="C001", dict_name="客户一"
    )
    with pytest.raises(CustomerConflictError):
        create_customer(payload={"dict_code": "C001", "dict_name": "客户一复刻"})


@pytest.mark.django_db
def test_create_customer_reports_conflict_on_integrity_error(monkeypatch) -> None:
    from apps.dictionary.services import customers as customers_module

    def _raise(*args, **kwargs):
        raise IntegrityError("duplicate")

    monkeypatch.setattr(customers_module, "insert_item", _raise)
    with pytest.raises(CustomerConflictError):
        create_customer(
            payload={"dict_code": "C001", "dict_name": "客户", "sort_order": 0}
        )


@pytest.mark.django_db
def test_create_customer_persists_row() -> None:
    created = create_customer(
        payload={"dict_code": "C001", "dict_name": "客户一", "sort_order": 5}
    )
    assert created["dict_code"] == "C001"
    assert created["dict_name"] == "客户一"
    assert created["status"] == "active"
    assert created["sort_order"] == 5
    assert DictionaryItem.objects.filter(dict_type="customer", dict_code="C001").exists()


@pytest.mark.django_db
def test_update_customer_rejects_missing_or_wrong_type() -> None:
    DictionaryItem.objects.create(
        dict_type="role_scope", dict_code="self", dict_name="本人"
    )
    with pytest.raises(CustomerNotFoundError):
        update_customer(customer_id=999_999_999, payload={"dict_name": "新名"})
    scope_item = DictionaryItem.objects.get(dict_code="self")
    with pytest.raises(CustomerNotFoundError):
        update_customer(customer_id=scope_item.id, payload={"dict_name": "新名"})


@pytest.mark.django_db
def test_update_customer_validates_and_applies_fields() -> None:
    created = create_customer(
        payload={"dict_code": "C001", "dict_name": "客户一", "sort_order": 0}
    )
    with pytest.raises(ValueError, match="客户名称不能为空"):
        update_customer(customer_id=int(created["id"]), payload={"dict_name": "  "})
    with pytest.raises(ValueError, match="客户状态只能是"):
        update_customer(
            customer_id=int(created["id"]), payload={"status": "deleted"}
        )
    with pytest.raises(ValueError, match="排序值必须是非负整数"):
        update_customer(
            customer_id=int(created["id"]), payload={"sort_order": -1}
        )
    updated = update_customer(
        customer_id=int(created["id"]),
        payload={
            "dict_name": "客户一-更新",
            "sort_order": 9,
            "status": "inactive",
            "description": "备注",
        },
    )
    assert updated["dict_name"] == "客户一-更新"
    assert updated["sort_order"] == 9
    assert updated["status"] == "inactive"
    assert updated["description"] == "备注"
    assert updated["dict_code"] == "C001"  # not modified


@pytest.mark.django_db
def test_update_customer_no_op_returns_existing() -> None:
    created = create_customer(
        payload={"dict_code": "C001", "dict_name": "客户一", "sort_order": 1}
    )
    updated = update_customer(customer_id=int(created["id"]), payload={})
    assert updated == created


@pytest.mark.django_db
def test_soft_delete_customer_marks_deleted_and_hides() -> None:
    created = create_customer(
        payload={"dict_code": "C001", "dict_name": "客户一", "sort_order": 0}
    )
    result = soft_delete_customer(customer_id=int(created["id"]))
    assert result["status"] == "deleted"
    assert result["id"] == created["id"]
    assert list_customers() == []
    with pytest.raises(CustomerNotFoundError):
        soft_delete_customer(customer_id=int(created["id"]))
