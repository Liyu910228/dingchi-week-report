from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from apps.core.security.asymmetric import AsymmetricCrypto
from apps.core.security.fields import EncryptedPasswordField
from apps.core.security.passwords import (
    PASSWORD_CIPHERTEXT_PREFIX,
    decrypt_client_password,
    decrypt_password_from_storage,
    encrypt_client_password_for_storage,
    encrypt_password_for_storage,
)


def _create_crypto(tmp_path: Path) -> AsymmetricCrypto:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_key_path = tmp_path / "private_key.pem"
    public_key_path = tmp_path / "public_key.pem"
    private_key_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    public_key_path.write_bytes(
        private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    return AsymmetricCrypto.from_paths(
        private_key_path=private_key_path,
        public_key_path=public_key_path,
    )


def test_rsa_oaep_round_trip(tmp_path: Path) -> None:
    crypto = _create_crypto(tmp_path)

    ciphertext = crypto.encrypt("password-密码-123")

    assert ciphertext != "password-密码-123"
    assert crypto.decrypt(ciphertext) == "password-密码-123"
    assert "BEGIN PUBLIC KEY" in crypto.public_key_pem()


def test_password_storage_helper_and_model_field(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    crypto = _create_crypto(tmp_path)
    monkeypatch.setattr("apps.core.security.passwords.get_crypto", lambda: crypto)

    client_ciphertext = crypto.encrypt("client-password")
    stored_ciphertext = encrypt_password_for_storage("client-password")
    client_stored_ciphertext = encrypt_client_password_for_storage(client_ciphertext)
    field = EncryptedPasswordField()

    assert decrypt_client_password(client_ciphertext) == "client-password"
    assert stored_ciphertext.startswith(PASSWORD_CIPHERTEXT_PREFIX)
    assert decrypt_password_from_storage(stored_ciphertext) == "client-password"
    assert decrypt_password_from_storage(client_stored_ciphertext) == "client-password"
    prepared_value = field.get_prep_value("client-password")
    assert prepared_value is not None
    assert prepared_value.startswith(PASSWORD_CIPHERTEXT_PREFIX)
    assert field.from_db_value(prepared_value, None, None) == "client-password"
