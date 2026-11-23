"""Explicitly generate the RSA key pair used by password encryption.

This script is intentionally never called by Django startup, health checks, or
container entrypoints. Run it once during local setup or during a controlled
key-rotation operation.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import BestAvailableEncryption, NoEncryption
from django.conf import settings


def _load_settings() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    import django

    django.setup()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生成 DingChi Week Report RSA 密钥对")
    parser.add_argument(
        "--private-key",
        default=str(settings.CRYPTO_PRIVATE_KEY_PATH),
        help="私钥输出路径，默认读取 CRYPTO_PRIVATE_KEY_PATH",
    )
    parser.add_argument(
        "--public-key",
        default=str(settings.CRYPTO_PUBLIC_KEY_PATH),
        help="公钥输出路径，默认读取 CRYPTO_PUBLIC_KEY_PATH",
    )
    parser.add_argument(
        "--key-size",
        type=int,
        default=settings.CRYPTO_KEY_SIZE,
        help="密钥位数，默认读取 CRYPTO_KEY_SIZE",
    )
    parser.add_argument("--force", action="store_true", help="允许覆盖已有密钥文件")
    return parser


def _write_key(path: Path, content: bytes, *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"密钥文件已存在：{path}；如需覆盖请显式使用 --force")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def main() -> None:
    _load_settings()
    args = _build_parser().parse_args()
    if args.key_size < 2048:
        raise ValueError("RSA 密钥位数不能小于 2048")

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=args.key_size)
    private_key_password = settings.CRYPTO_PRIVATE_KEY_PASSWORD
    encryption = (
        BestAvailableEncryption(private_key_password.encode("utf-8"))
        if private_key_password
        else NoEncryption()
    )
    private_key_data = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption,
    )
    public_key_data = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    private_path = Path(args.private_key).resolve()
    public_path = Path(args.public_key).resolve()
    _write_key(private_path, private_key_data, force=args.force)
    try:
        _write_key(public_path, public_key_data, force=args.force)
    except Exception:
        if not args.force and private_path.exists():
            private_path.unlink()
        raise
    print(f"已生成 RSA 私钥：{private_path}")
    print(f"已生成 RSA 公钥：{public_path}")


if __name__ == "__main__":
    main()
