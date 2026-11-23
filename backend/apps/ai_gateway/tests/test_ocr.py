import io
import json
import zipfile
from unittest.mock import patch

import pytest
from asgiref.sync import sync_to_async
from django.core.files.uploadedfile import SimpleUploadedFile
from pypdf import PdfWriter

from apps.ai_gateway.models import AIOCRKey
from apps.ai_gateway.services.attachments import save_uploaded_attachment
from apps.ai_gateway.services.ocr import (
    OCRAllProvidersFailedError,
    OCRNotConfiguredError,
    OCRProviderError,
    _mineru_markdown,
    _paddle_jsonl_text,
    extract_with_ocr,
)
from apps.ai_gateway.services.ocr_keys import (
    create_ocr_key,
    list_ocr_keys,
    serialize_ocr_key,
    update_ocr_key,
)


async def _create_async(payload, user_id=1):
    return await sync_to_async(create_ocr_key, thread_sensitive=True)(payload, user_id)


async def _get_async(key_id):
    return await sync_to_async(AIOCRKey.objects.get, thread_sensitive=True)(id=int(key_id))


async def _reset_async():
    await sync_to_async(AIOCRKey.objects.all().delete, thread_sensitive=True)()


@pytest.mark.django_db
def test_ocr_keys_are_encrypted_masked_and_independently_disabled() -> None:
    created = create_ocr_key(
        {
            "provider": "mineru",
            "label": "测试账号",
            "api_key": "sk-test-secret-value",
            "is_enabled": True,
        },
        user_id=1,
    )
    assert created["api_key_masked"].startswith("sk-t")
    assert "sk-test-secret-value" not in json.dumps(list_ocr_keys())
    row = AIOCRKey.objects.get(id=int(created["id"]))
    assert row.api_key == "sk-test-secret-value"
    assert "sk-test-secret-value" not in json.dumps(serialize_ocr_key(row))

    disabled = update_ocr_key(created["id"], {"is_enabled": False})
    assert disabled["is_enabled"] is False


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_only_enabled_key_is_used_and_result_is_recorded() -> None:
    await _reset_async()
    enabled = await _create_async(
        {"provider": "paddleocr", "api_key": "enabled-secret", "is_enabled": True}, 1
    )
    disabled = await _create_async(
        {"provider": "mineru", "api_key": "disabled-secret", "is_enabled": False}, 1
    )

    async def fake_provider(client, candidate, filename, content, deadline):
        assert candidate.api_key == "enabled-secret"
        return "识别后的工作记录"

    with patch("apps.ai_gateway.services.ocr._run_provider", side_effect=fake_provider):
        result = await extract_with_ocr("work.png", b"image")

    assert result.text == "识别后的工作记录"
    assert result.key_id == int(enabled["id"])
    assert (await _get_async(enabled["id"])).last_status == "success"
    assert (await _get_async(disabled["id"])).use_count == 0


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_failed_key_is_not_retried_and_next_enabled_key_succeeds() -> None:
    await _reset_async()
    first = await _create_async(
        {"provider": "paddleocr", "api_key": "first-secret", "is_enabled": True}, 1
    )
    second = await _create_async(
        {"provider": "mineru", "api_key": "second-secret", "is_enabled": True}, 1
    )

    async def fake_provider(client, candidate, filename, content, deadline):
        if candidate.provider == "paddleocr":
            raise OCRProviderError(f"认证失败 {candidate.api_key}")
        return "备用 Key 识别结果"

    with (
        patch("apps.ai_gateway.services.ocr._run_provider", side_effect=fake_provider),
        patch("apps.ai_gateway.services.ocr.random.SystemRandom") as system_random,
    ):
        system_random.return_value.shuffle.side_effect = lambda values: None
        result = await extract_with_ocr("work.pdf", b"pdf")

    assert result.key_id == int(second["id"])
    failed = await _get_async(first["id"])
    assert failed.use_count == 1
    assert failed.last_status == "failed"
    assert "first-secret" not in failed.last_error


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_no_enabled_key_fails_without_calling_provider() -> None:
    await _reset_async()
    await _create_async(
        {"provider": "mineru", "api_key": "disabled-never-used", "is_enabled": False}, 1
    )
    with pytest.raises(OCRNotConfiguredError):
        await extract_with_ocr("work.png", b"image")


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_all_enabled_key_errors_are_safe() -> None:
    await _reset_async()
    await _create_async(
        {"provider": "mineru", "api_key": "never-leak-me", "is_enabled": True}, 1
    )

    async def fake_provider(client, candidate, filename, content, deadline):
        raise OCRProviderError(f"bad credential {candidate.api_key}")

    with (
        patch("apps.ai_gateway.services.ocr._run_provider", side_effect=fake_provider),
        pytest.raises(OCRAllProvidersFailedError) as caught,
    ):
        await extract_with_ocr("work.png", b"image")
    assert "never-leak-me" not in str(caught.value)


def test_paddle_jsonl_extracts_recognized_text() -> None:
    line = {
        "result": {
            "ocrResults": [
                {
                    "prunedResult": {
                        "rec_texts": ["完成客户回访", "低置信度", "下周跟进"],
                        "rec_scores": [0.98, 0.2, 0.96],
                    }
                }
            ]
        }
    }
    content = (json.dumps(line, ensure_ascii=False) + "\n").encode()
    assert _paddle_jsonl_text(content) == "完成客户回访\n下周跟进"


def test_mineru_zip_extracts_full_markdown() -> None:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("result/full.md", "# 工作记录\n\n已完成测试")
        archive.writestr("result/layout.json", "{}")
    assert _mineru_markdown(output.getvalue()) == "# 工作记录\n\n已完成测试"


@pytest.mark.django_db
def test_scanned_pdf_is_accepted_for_deferred_ocr(tmp_path, settings) -> None:
    settings.MEDIA_ROOT = tmp_path
    output = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.write(output)
    upload = SimpleUploadedFile("scan.pdf", output.getvalue(), content_type="application/pdf")
    result = save_uploaded_attachment(upload, 100)
    assert result["kind"] == "document"
