"""客户配置按职位授权且编辑保存后可恢复。"""

import pytest

from apps.accounts.models import Role
from apps.accounts.public import reporting_positions
from apps.accounts.services import auth
from apps.accounts.services.customer_assignments import (
    set_role_customers,
    set_user_customers,
    user_assignments,
)
from apps.dictionary.models import DictionaryItem
from apps.weekly_report.tests.services.test_monthly_plan_workflow import people as people
from apps.weekly_report.tests.services.test_multi_position import multi as multi

pytestmark = pytest.mark.django_db


def test_user_customer_configuration_persist_and_role_candidates(multi):
    owner, _ = multi
    first = DictionaryItem.objects.create(dict_type="customer", dict_code="a", dict_name="甲客户")
    second = DictionaryItem.objects.create(dict_type="customer", dict_code="b", dict_name="乙客户")
    role = Role.objects.get(role_code="delivery")
    set_role_customers(role.id, [str(first.id), str(second.id)])
    auth.update_user(
        user=owner, payload={"role_customer_ids": {"delivery": [str(second.id), str(first.id)]}}
    )
    assert user_assignments(owner.id)["delivery"] == [str(second.id), str(first.id)]
    assert auth.serialize_user(owner)["role_customer_ids"]["delivery"] == [
        str(second.id),
        str(first.id),
    ]
    assert next(p for p in reporting_positions(owner.id) if p["role_code"] == "delivery")[
        "customers"
    ] == [{"id": str(second.id), "name": "乙客户"}, {"id": str(first.id), "name": "甲客户"}]
    with pytest.raises(ValueError):
        set_user_customers(owner.id, {"sales": [str(first.id)]})
    assert user_assignments(owner.id)["delivery"] == [str(second.id), str(first.id)]
    set_role_customers(role.id, [str(first.id)])
    assert user_assignments(owner.id)["delivery"] == [str(first.id)]
    set_user_customers(owner.id, {})
    assert all(not p["customers"] for p in reporting_positions(owner.id))


def test_reject_invalid_inactive_and_unassigned_customers(multi):
    owner, _ = multi
    inactive = DictionaryItem.objects.create(
        dict_type="customer", dict_code="off", dict_name="停用", status="inactive"
    )
    with pytest.raises(ValueError):
        set_role_customers(Role.objects.get(role_code="delivery").id, [str(inactive.id)])
    with pytest.raises(ValueError):
        set_user_customers(owner.id, {"unassigned": []})
