"""软删除唯一键及职位挂载检查回归测试。"""

import pytest

from apps.accounts.models import UserAccount, UserRole
from apps.accounts.services.auth import UserConflictError, create_user, delete_user
from apps.accounts.services.organization import RoleConflictError, create_role, delete_role
from apps.core.security.asymmetric import get_crypto
from apps.dictionary.models import DictionaryItem


def role():
    DictionaryItem.objects.get_or_create(
        dict_type="role_scope", dict_code="self", defaults={"dict_name": "本人"}
    )
    return create_role(payload={"role_code": "reusable", "role_name": "重复使用"})


def user(position):
    return create_user(
        payload={
            "username": "reusable.user",
            "display_name": "测试用户",
            "password": get_crypto().encrypt("test-password-123"),
            "role_codes": [position.role_code],
        }
    )


@pytest.mark.django_db
def test_user_can_be_recreated_repeatedly_without_reusing_identity():
    position = role()
    previous = []
    for _ in range(3):
        account = user(position)
        assert account.id not in [row.id for row in previous]
        assert account.employee_no not in [row.employee_no for row in previous]
        if previous:
            assert not UserRole.objects.filter(user_id=account.id, status="inactive").exists()
        delete_user(user_id=account.id, acting_user_id=-1)
        account.refresh_from_db()
        assert account.username == "reusable.user"
        assert account.deletion_key == account.id
        previous.append(account)
    assert UserAccount.objects.filter(username="reusable.user", status="deleted").count() == 3


@pytest.mark.django_db
@pytest.mark.parametrize("status", ["active", "inactive"])
def test_live_user_keeps_username_reserved(status):
    position = role()
    account = user(position)
    account.status = status
    account.save()
    with pytest.raises(UserConflictError, match="登录账号已存在"):
        user(position)


@pytest.mark.django_db
@pytest.mark.parametrize("status", ["active", "inactive"])
def test_role_with_assigned_user_cannot_be_deleted(status):
    position = role()
    account = user(position)
    account.status = status
    account.save()
    with pytest.raises(RoleConflictError, match="已挂载用户"):
        delete_role(role_id=position.id, acting_role_code="system_admin")
    position.refresh_from_db()
    assert position.status == "active"
    assert UserRole.objects.get(user_id=account.id, role_id=position.id).status == "active"


@pytest.mark.django_db
def test_role_can_be_recreated_after_deleted_user_or_unassignment():
    original = role()
    account = user(original)
    delete_user(user_id=account.id, acting_user_id=-1)
    ids = set()
    for _ in range(3):
        delete_role(role_id=original.id, acting_role_code="system_admin")
        original.refresh_from_db()
        assert original.deletion_key == original.id
        ids.add(original.id)
        original = create_role(payload={"role_code": "reusable", "role_name": "新职位"})
        assert original.id not in ids
    UserRole.objects.create(user_id=account.id, role_id=original.id, status="active")
    # 即使历史关联仍存在，已删除用户不阻止删除。
    delete_role(role_id=original.id, acting_role_code="system_admin")


@pytest.mark.django_db
def test_unassigned_user_does_not_block_role_deletion():
    position = role()
    account = user(position)
    UserRole.objects.filter(user_id=account.id, role_id=position.id).update(status="inactive")
    delete_role(role_id=position.id, acting_role_code="system_admin")
