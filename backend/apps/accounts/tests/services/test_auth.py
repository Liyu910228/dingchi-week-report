"""Tests for the change_password service used by the self-service dialog."""

from __future__ import annotations

import pytest

from apps.accounts.models import Role, UserAccount, UserRole
from apps.accounts.services.auth import change_password
from apps.core.security.asymmetric import get_crypto

PASSWORD_OLD = "old-secret-1"
PASSWORD_NEW = "new-secret-8"
ROLE_CODE = "password_change_role"


def _encrypt(password: str) -> str:
    """Produce a transport ciphertext the same way the browser would."""
    return get_crypto().encrypt(password)


def _create_user_with_role() -> tuple[UserAccount, Role]:
    role = Role.objects.create(
        role_code=ROLE_CODE,
        role_name="改密测试角色",
        scope="self",
        status="active",
    )
    user = UserAccount.objects.create(
        username="password.user",
        employee_no="DC900001",
        display_name="改密用户",
        password_ciphertext=PASSWORD_OLD,
    )
    UserRole.objects.create(user_id=user.id, role_id=role.id, is_default=True)
    return user, role


@pytest.mark.django_db
def test_change_password_replaces_stored_password() -> None:
    user, _ = _create_user_with_role()

    change_password(
        user=user,
        old_password_ciphertext=_encrypt(PASSWORD_OLD),
        new_password_ciphertext=_encrypt(PASSWORD_NEW),
        current_role_code=ROLE_CODE,
    )

    refreshed = UserAccount.objects.get(pk=user.pk)
    # from_db_value 已把存储密文解回请求内明文，这里直接比对即可。
    assert str(refreshed.password_ciphertext) == PASSWORD_NEW


@pytest.mark.django_db
def test_change_password_returns_new_session() -> None:
    """改密成功后应同时返回带新令牌的会话，实现无感续期。"""
    user, _ = _create_user_with_role()

    session = change_password(
        user=user,
        old_password_ciphertext=_encrypt(PASSWORD_OLD),
        new_password_ciphertext=_encrypt(PASSWORD_NEW),
        current_role_code=ROLE_CODE,
    )

    assert session["token_type"] == "Bearer"
    assert session["access_token"]
    assert session["user"]["username"] == user.username
    assert session["active_role"]["role_code"] == ROLE_CODE
    assert session["expires_in"] > 0
    assert session["roles"][0]["role_code"] == ROLE_CODE


@pytest.mark.django_db
def test_change_password_rejects_wrong_old_password() -> None:
    user, _ = _create_user_with_role()

    with pytest.raises(ValueError, match="旧密码不正确"):
        change_password(
            user=user,
            old_password_ciphertext=_encrypt("wrong-password"),
            new_password_ciphertext=_encrypt(PASSWORD_NEW),
            current_role_code=ROLE_CODE,
        )


@pytest.mark.django_db
def test_change_password_rejects_same_password() -> None:
    user, _ = _create_user_with_role()

    with pytest.raises(ValueError, match="不能与旧密码相同"):
        change_password(
            user=user,
            old_password_ciphertext=_encrypt(PASSWORD_OLD),
            new_password_ciphertext=_encrypt(PASSWORD_OLD),
            current_role_code=ROLE_CODE,
        )


@pytest.mark.django_db
def test_change_password_rejects_short_new_password() -> None:
    user, _ = _create_user_with_role()

    with pytest.raises(ValueError, match="至少 8 位"):
        change_password(
            user=user,
            old_password_ciphertext=_encrypt(PASSWORD_OLD),
            new_password_ciphertext=_encrypt("short"),
            current_role_code=ROLE_CODE,
        )


@pytest.mark.django_db
def test_change_password_rejects_unassigned_current_role() -> None:
    """当前角色不在用户已分配集合中时应返回 AUTHENTICATION_FAILED。"""
    user, _ = _create_user_with_role()

    with pytest.raises(Exception, match="当前角色不可用"):
        change_password(
            user=user,
            old_password_ciphertext=_encrypt(PASSWORD_OLD),
            new_password_ciphertext=_encrypt(PASSWORD_NEW),
            current_role_code="not_assigned_role",
        )
