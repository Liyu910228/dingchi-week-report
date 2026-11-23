"""Password transport and encrypted-at-rest helpers."""

from __future__ import annotations

from .asymmetric import CryptoPayloadError, get_crypto

PASSWORD_CIPHERTEXT_PREFIX = "rsa_oaep_sha256:"


def decrypt_client_password(ciphertext: str) -> str:
    """Decrypt a password received from the frontend into request-local memory."""
    return _validate_plaintext(get_crypto().decrypt(ciphertext))


def encrypt_password_for_storage(password: str) -> str:
    """Encrypt a plaintext password for a database field, avoiding double encryption."""
    plaintext = _validate_plaintext(password)
    if is_password_ciphertext(plaintext):
        return plaintext
    return PASSWORD_CIPHERTEXT_PREFIX + get_crypto().encrypt(plaintext)


def encrypt_client_password_for_storage(ciphertext: str) -> str:
    """Decrypt frontend input in memory and immediately re-encrypt it for storage."""
    return encrypt_password_for_storage(decrypt_client_password(ciphertext))


def decrypt_password_from_storage(value: str) -> str:
    """Decrypt a value previously written by :func:`encrypt_password_for_storage`."""
    if not is_password_ciphertext(value):
        raise CryptoPayloadError("数据库密码字段不是受支持的 RSA 密文格式。")
    return _validate_plaintext(get_crypto().decrypt(value[len(PASSWORD_CIPHERTEXT_PREFIX) :]))


def is_password_ciphertext(value: str) -> bool:
    """Return whether a value carries the versioned encrypted-password prefix."""
    return (
        isinstance(value, str)
        and value.startswith(PASSWORD_CIPHERTEXT_PREFIX)
        and len(value) > len(PASSWORD_CIPHERTEXT_PREFIX)
    )


def _validate_plaintext(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise CryptoPayloadError("密码不能为空。")
    return value
