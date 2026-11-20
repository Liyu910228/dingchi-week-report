"""Admin-managed OCR credentials with encrypted storage and safe serialization."""

from __future__ import annotations

from typing import Any

from django.db import transaction

from ..models import AIOCRKey
from .model_config import mask_api_key

PROVIDERS = {AIOCRKey.PROVIDER_PADDLEOCR, AIOCRKey.PROVIDER_MINERU}


def serialize_ocr_key(row: AIOCRKey) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "provider": row.provider,
        "label": row.label,
        "api_key_masked": mask_api_key(str(row.api_key or "")),
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
        raise ValueError("OCR 平台仅支持 paddleocr 或 mineru。")
    api_key = payload.get("api_key")
    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("API Key 不能为空。")
    api_key = api_key.strip()
    if len(api_key) > 1000:
        raise ValueError("API Key 长度不能超过 1000 个字符。")
    for existing in AIOCRKey.objects.filter(provider=provider):
        if str(existing.api_key) == api_key:
            raise ValueError("该平台的 API Key 已存在。")
    row = AIOCRKey.objects.create(
        provider=provider,
        label=_clean_label(payload.get("label")),
        api_key=api_key,
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
