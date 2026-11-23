"""Django model fields for encrypted credentials."""

from __future__ import annotations

from typing import Any

from django.db import models

from .passwords import (
    decrypt_password_from_storage,
    encrypt_password_for_storage,
    is_password_ciphertext,
)


class EncryptedPasswordField(models.TextField):
    """Store credentials as versioned RSA ciphertext and expose plaintext in memory."""

    description = "RSA-OAEP-SHA256 encrypted password"

    def get_prep_value(self, value: Any) -> str | None:
        if value is None:
            return None
        return encrypt_password_for_storage(str(value))

    def from_db_value(self, value: Any, expression: Any, connection: Any) -> str | None:
        del expression, connection
        if value is None:
            return None
        string_value = str(value)
        if is_password_ciphertext(string_value):
            return decrypt_password_from_storage(string_value)
        return string_value

    def to_python(self, value: Any) -> str | None:
        if value is None or (isinstance(value, str) and not is_password_ciphertext(value)):
            return value
        if isinstance(value, str):
            return decrypt_password_from_storage(value)
        return str(value)
