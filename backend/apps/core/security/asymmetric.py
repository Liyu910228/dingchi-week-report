"""RSA-OAEP helpers used for password transport and storage."""

from __future__ import annotations

import base64
import binascii
from functools import lru_cache
from pathlib import Path

from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from django.conf import settings

RSA_ALGORITHM = "RSA-OAEP-SHA256"


class CryptoConfigurationError(RuntimeError):
    """Raised when the configured RSA key pair cannot be loaded."""


class CryptoPayloadError(ValueError):
    """Raised when an RSA payload is malformed or cannot be decrypted."""


class AsymmetricCrypto:
    """Encrypt with the public key and decrypt with the matching private key."""

    def __init__(self, *, private_key: rsa.RSAPrivateKey, public_key: rsa.RSAPublicKey) -> None:
        self._private_key = private_key
        self._public_key = public_key

    @classmethod
    def from_paths(
        cls,
        *,
        private_key_path: Path,
        public_key_path: Path,
        private_key_password: str | None = None,
    ) -> AsymmetricCrypto:
        private_key_data = _read_key_file(private_key_path)
        public_key_data = _read_key_file(public_key_path)
        password_data = private_key_password.encode("utf-8") if private_key_password else None

        try:
            private_key = serialization.load_pem_private_key(
                private_key_data,
                password=password_data,
            )
            public_key = serialization.load_pem_public_key(public_key_data)
        except (TypeError, ValueError, UnsupportedAlgorithm) as exc:
            raise CryptoConfigurationError("RSA 密钥格式或私钥口令无效。") from exc

        if not isinstance(private_key, rsa.RSAPrivateKey):
            raise CryptoConfigurationError("RSA 私钥文件必须包含 RSA 私钥。")
        if not isinstance(public_key, rsa.RSAPublicKey):
            raise CryptoConfigurationError("RSA 公钥文件必须包含 RSA 公钥。")
        if private_key.public_key().public_numbers() != public_key.public_numbers():
            raise CryptoConfigurationError("RSA 公钥与私钥不匹配。")

        return cls(private_key=private_key, public_key=public_key)

    def public_key_pem(self) -> str:
        """Return a SubjectPublicKeyInfo PEM for browser Web Crypto."""
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("ascii")

    def encrypt(self, plaintext: str) -> str:
        """Encrypt UTF-8 text and return URL-safe base64 without secrets in logs."""
        if not isinstance(plaintext, str) or not plaintext:
            raise CryptoPayloadError("待加密内容不能为空。")

        try:
            ciphertext = self._public_key.encrypt(
                plaintext.encode("utf-8"),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
        except ValueError as exc:
            raise CryptoPayloadError("待加密内容超过 RSA 单次加密长度限制。") from exc
        return base64.urlsafe_b64encode(ciphertext).decode("ascii")

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt URL-safe or standard base64 RSA-OAEP text in memory."""
        if not isinstance(ciphertext, str) or not ciphertext:
            raise CryptoPayloadError("待解密内容不能为空。")

        try:
            ciphertext_data = _decode_base64(ciphertext)
            plaintext_data = self._private_key.decrypt(
                ciphertext_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            return plaintext_data.decode("utf-8")
        except (binascii.Error, UnicodeDecodeError, ValueError) as exc:
            raise CryptoPayloadError("RSA 密文无效或无法解密。") from exc


def _read_key_file(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise CryptoConfigurationError("RSA 密钥文件不可读，请检查配置和挂载。") from exc


def _decode_base64(value: str) -> bytes:
    try:
        encoded = value.encode("ascii")
        encoded += b"=" * (-len(encoded) % 4)
        return base64.b64decode(encoded, altchars=b"-_", validate=True)
    except (UnicodeEncodeError, binascii.Error, ValueError) as exc:
        raise CryptoPayloadError("RSA 密文不是合法的 Base64。") from exc


@lru_cache(maxsize=1)
def get_crypto() -> AsymmetricCrypto:
    """Load and cache the configured key pair for the process lifetime."""
    return AsymmetricCrypto.from_paths(
        private_key_path=Path(settings.CRYPTO_PRIVATE_KEY_PATH),
        public_key_path=Path(settings.CRYPTO_PUBLIC_KEY_PATH),
        private_key_password=settings.CRYPTO_PRIVATE_KEY_PASSWORD or None,
    )
