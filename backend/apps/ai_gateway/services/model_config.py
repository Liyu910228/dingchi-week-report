"""Database-backed OpenAI-compatible model settings with safe secret handling."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import OperationalError, ProgrammingError, transaction
from django.utils import timezone
from openai import AsyncOpenAI, OpenAIError

from ..models import AIModelConfig


@dataclass(frozen=True, slots=True)
class EffectiveAIConfig:
    model: str
    base_url: str
    api_key: str = field(repr=False)
    vision_model: str = ""
    source: str = "environment"
    revision: str = "environment"

    @property
    def vision_model_or_main(self) -> str:
        return self.vision_model or self.model

    @property
    def fingerprint(self) -> tuple[str, str, str, str]:
        return (self.model, self.vision_model, self.base_url, self.api_key)


class AIConnectionTestError(RuntimeError):
    pass


def _environment_config() -> EffectiveAIConfig:
    return EffectiveAIConfig(
        model=str(getattr(settings, "AI_MODEL", "") or "").strip(),
        vision_model=str(getattr(settings, "AI_VISION_MODEL", "") or "").strip(),
        base_url=str(getattr(settings, "AI_BASE_URL", "") or "").strip(),
        api_key=str(getattr(settings, "AI_API_KEY", "") or "").strip(),
    )


def _config_row() -> AIModelConfig | None:
    try:
        return AIModelConfig.objects.order_by("-updated_at", "-id").first()
    except (OperationalError, ProgrammingError):
        # Keep startup and health checks functional before the first migration.
        return None


def load_effective_config() -> EffectiveAIConfig:
    row = _config_row()
    if row is not None and not row.is_enabled:
        return EffectiveAIConfig(
            model="",
            base_url="",
            api_key="",
            source="database",
            revision=str(row.updated_at.timestamp()),
        )
    if row is not None and row.model and row.api_key:
        return EffectiveAIConfig(
            model=row.model.strip(),
            vision_model=row.vision_model.strip(),
            base_url=row.base_url.strip(),
            api_key=str(row.api_key).strip(),
            source="database",
            revision=str(row.updated_at.timestamp()),
        )
    return _environment_config()


def mask_api_key(api_key: str) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "********"
    return f"{api_key[:4]}{'*' * 8}{api_key[-4:]}"


def serialize_model_config() -> dict[str, Any]:
    row = _config_row()
    if row is None:
        config = _environment_config()
        return {
            "model": config.model,
            "vision_model": config.vision_model,
            "base_url": config.base_url,
            "has_api_key": bool(config.api_key),
            "api_key_masked": mask_api_key(config.api_key),
            "is_enabled": True,
            "source": "environment",
            "updated_at": None,
            "last_test_status": "",
            "last_test_message": "",
            "last_tested_at": None,
        }
    return {
        "model": row.model,
        "vision_model": row.vision_model,
        "base_url": row.base_url,
        "has_api_key": bool(row.api_key),
        "api_key_masked": mask_api_key(str(row.api_key or "")),
        "is_enabled": row.is_enabled,
        "source": "database",
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        "last_test_status": row.last_test_status,
        "last_test_message": row.last_test_message,
        "last_tested_at": row.last_tested_at.isoformat() if row.last_tested_at else None,
    }


def _clean_text(payload: dict[str, Any], key: str, max_length: int) -> str:
    value = payload.get(key, "")
    if not isinstance(value, str):
        raise ValueError(f"{key} 必须是字符串。")
    value = value.strip()
    if len(value) > max_length:
        raise ValueError(f"{key} 长度不能超过 {max_length} 个字符。")
    return value


def resolve_form_config(payload: dict[str, Any]) -> EffectiveAIConfig:
    model = _clean_text(payload, "model", 128)
    vision_model = _clean_text(payload, "vision_model", 128)
    base_url = _clean_text(payload, "base_url", 500)
    api_key = _clean_text(payload, "api_key", 180)
    if not model:
        raise ValueError("主模型名称不能为空。")
    if base_url and urlparse(base_url).scheme not in {"http", "https"}:
        raise ValueError("Base URL 必须是有效的 HTTP 或 HTTPS 地址。")
    if not api_key:
        row = _config_row()
        if row is not None and row.api_key:
            api_key = str(row.api_key).strip()
        else:
            api_key = _environment_config().api_key
    if not api_key:
        raise ValueError("API Key 不能为空。")
    return EffectiveAIConfig(
        model=model,
        vision_model=vision_model,
        base_url=base_url,
        api_key=api_key,
        source="database",
    )


@transaction.atomic
def save_model_config(payload: dict[str, Any], user_id: int) -> dict[str, Any]:
    config = resolve_form_config(payload)
    row = _config_row()
    if row is None:
        row = AIModelConfig()
    row.model = config.model
    row.vision_model = config.vision_model
    row.base_url = config.base_url
    row.api_key = config.api_key
    row.is_enabled = bool(payload.get("is_enabled", True))
    row.updated_by_id = user_id
    row.save()
    return serialize_model_config()


def record_test_result(success: bool, message: str) -> None:
    row = _config_row()
    if row is None:
        return
    row.last_test_status = "success" if success else "failed"
    row.last_test_message = message[:500]
    row.last_tested_at = timezone.now()
    row.save(
        update_fields=["last_test_status", "last_test_message", "last_tested_at", "updated_at"]
    )


def _safe_error(exc: Exception, api_key: str) -> str:
    if isinstance(exc, TimeoutError):
        return "连接超时，请检查 Base URL 和网络。"
    status = getattr(exc, "status_code", None)
    if status == 401:
        return "认证失败，请检查 API Key。"
    if status == 404:
        return "接口或模型不存在，请检查 Base URL 和模型名称。"
    text = str(exc).replace(api_key, "***") if api_key else str(exc)
    return (text or exc.__class__.__name__)[:300]


async def test_model_connection(payload: dict[str, Any]) -> dict[str, Any]:
    config = await sync_to_async(resolve_form_config, thread_sensitive=True)(payload)
    client = AsyncOpenAI(
        api_key=config.api_key,
        base_url=config.base_url or None,
        timeout=min(float(getattr(settings, "AI_TIMEOUT_SECONDS", 60)), 30.0),
        max_retries=0,
    )
    started = time.perf_counter()
    try:
        response = await client.chat.completions.create(
            model=config.model,
            messages=[{"role": "user", "content": "请仅回复 OK"}],
            max_tokens=8,
            temperature=0,
        )
        reply = (response.choices[0].message.content or "").strip() if response.choices else ""
        return {
            "success": True,
            "message": "连接成功，模型已正常返回结果。",
            "model": response.model or config.model,
            "latency_ms": round((time.perf_counter() - started) * 1000),
            "reply": reply[:100],
        }
    except (OpenAIError, TimeoutError) as exc:
        raise AIConnectionTestError(_safe_error(exc, config.api_key)) from exc
    finally:
        await client.close()
