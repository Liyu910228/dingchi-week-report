"""Admin-managed OCR credentials with encrypted storage and safe serialization."""

from __future__ import annotations

import json
from typing import Any

from django.db import transaction

from ..models import AIOCRKey
from .model_config import mask_api_key

PROVIDERS = {AIOCRKey.PROVIDER_PADDLEOCR, AIOCRKey.PROVIDER_MINERU, AIOCRKey.PROVIDER_BAIDU}


def _baidu_bundle(payload: dict[str, Any], api_key: str) -> str:
    app_id = payload.get("app_id")
    secret_key = payload.get("secret_key")
    if not isinstance(app_id, str) or not app_id.strip().isdigit():
        raise ValueError("百度 OCR 的 AppID 必须是数字。")
    if len(app_id.strip()) > 40:
        raise ValueError("AppID 长度不正确。")
    if not isinstance(secret_key, str) or not secret_key.strip():
        raise ValueError("百度 OCR 的 Secret Key 不能为空。")
    if len(secret_key.strip()) > 128:
        raise ValueError("Secret Key 长度不能超过 128 个字符。")
    return json.dumps(
        {"app_id": app_id.strip(), "api_key": api_key, "secret_key": secret_key.strip()},
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _display_secret(row: AIOCRKey) -> str:
    value = str(row.api_key or "")
    if row.provider == AIOCRKey.PROVIDER_BAIDU:
        try:
            return str(json.loads(value).get("api_key") or "")
        except (ValueError, AttributeError):
            return ""
    return value


def _app_id(row: AIOCRKey) -> str:
    if row.provider != AIOCRKey.PROVIDER_BAIDU:
        return ""
    try:
        return str(json.loads(str(row.api_key or "")).get("app_id") or "")
    except ValueError:
        return ""


def serialize_ocr_key(row: AIOCRKey) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "provider": row.provider,
        "label": row.label,
        "app_id": _app_id(row),
        "api_key_masked": mask_api_key(_display_secret(row)),
        "is_enabled": row.is_enabled,
        "last_used_at": row.last_used_at.isoformat() if row.last_used_at else None,
        "last_status": row.last_status,
        "last_error": row.last_error,
        "use_count": row.use_count,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def list_ocr_keys() -> list[dict[str, Any]]:
    return [serialize_ocr_key(row) for row in AIOCRKey.objects.all()]


def _clean_label(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("Key 备注必须是字符串。")
    value = value.strip()
    if len(value) > 80:
        raise ValueError("Key 备注不能超过 80 个字符。")
    return value


def _clean_enabled(value: Any) -> bool:
    if not isinstance(value, bool):
        raise ValueError("is_enabled 必须是布尔值。")
    return value


@transaction.atomic
def create_ocr_key(payload: dict[str, Any], user_id: int) -> dict[str, Any]:
    provider = payload.get("provider")
    if provider not in PROVIDERS:
        raise ValueError("OCR 平台仅支持 paddleocr、mineru 或 baidu。")
    api_key = payload.get("api_key")
    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("API Key 不能为空。")
    api_key = api_key.strip()
    if len(api_key) > 1000:
        raise ValueError("API Key 长度不能超过 1000 个字符。")
    credential = _baidu_bundle(payload, api_key) if provider == AIOCRKey.PROVIDER_BAIDU else api_key
    for existing in AIOCRKey.objects.filter(provider=provider):
        if str(existing.api_key) == credential:
            raise ValueError("该平台的 API Key 已存在。")
    row = AIOCRKey.objects.create(
        provider=provider,
        label=_clean_label(payload.get("label")),
        api_key=credential,
        is_enabled=_clean_enabled(payload.get("is_enabled", True)),
        created_by_id=user_id,
    )
    return serialize_ocr_key(row)


def _get_key(key_id: str | int) -> AIOCRKey:
    try:
        return AIOCRKey.objects.get(id=int(key_id))
    except (ValueError, TypeError, AIOCRKey.DoesNotExist) as exc:
        raise ValueError("OCR Key 不存在或已删除。") from exc


@transaction.atomic
def update_ocr_key(key_id: str | int, payload: dict[str, Any]) -> dict[str, Any]:
    row = _get_key(key_id)
    if "label" in payload:
        row.label = _clean_label(payload["label"])
    if "is_enabled" in payload:
        row.is_enabled = _clean_enabled(payload["is_enabled"])
    row.save(update_fields=["label", "is_enabled", "updated_at"])
    return serialize_ocr_key(row)


@transaction.atomic
def delete_ocr_key(key_id: str | int) -> None:
    _get_key(key_id).delete()
