import io
import json
import time
from urllib.parse import parse_qs

import httpx
import pytest
from PIL import Image
from pypdf import PdfWriter

from apps.ai_gateway.models import AIOCRKey
from apps.ai_gateway.services.ocr import (
    OCRKeyCandidate,
    OCRProviderError,
    _baidu_ocr,
    _baidu_token_cache,
    _safe_candidate_error,
)
from apps.ai_gateway.services.ocr_keys import create_ocr_key, list_ocr_keys


def _candidate() -> OCRKeyCandidate:
    return OCRKeyCandidate(
        id=998877,
        provider=AIOCRKey.PROVIDER_BAIDU,
        label="测试应用",
        api_key=json.dumps(
            {"app_id": "123456", "api_key": "api-secret", "secret_key": "very-secret"}
        ),
    )


def _png() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (640, 240), "white").save(output, format="PNG")
    return output.getvalue()


def _pdf(page_count: int) -> bytes:
    output = io.BytesIO()
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=200, height=200)
    writer.write(output)
    return output.getvalue()


@pytest.mark.django_db
def test_baidu_credentials_are_encrypted_and_secret_key_never_serialized() -> None:
    created = create_ocr_key(
        {
            "provider": "baidu",
            "label": "文档识别",
            "app_id": "123456789",
            "api_key": "api-secret",
            "secret_key": "very-secret",
            "is_enabled": True,
        },
        user_id=1,
    )
    assert created["app_id"] == "123456789"
    serialized = json.dumps(list_ocr_keys())
    assert "api-secret" not in serialized
    assert "very-secret" not in serialized
    row = AIOCRKey.objects.get(id=int(created["id"]))
    bundle = json.loads(row.api_key)
    assert bundle["app_id"] == "123456789"
    assert bundle["secret_key"] == "very-secret"


@pytest.mark.asyncio
async def test_baidu_image_ocr_reuses_cached_access_token() -> None:
    _baidu_token_cache.clear()
    token_calls = 0
    ocr_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal token_calls, ocr_calls
        if request.url.path == "/oauth/2.0/token":
            token_calls += 1
            return httpx.Response(200, json={"access_token": "token-value", "expires_in": 2592000})
        ocr_calls += 1
        form = parse_qs(request.content.decode())
        assert form["language_type"] == ["CHN_ENG"]
        assert form["detect_direction"] == ["true"]
        assert "image" in form
        return httpx.Response(
            200,
            json={"words_result": [{"words": "本周完成部署"}, {"words": "下周继续验证"}]},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        first = await _baidu_ocr(client, _candidate(), "work.png", _png(), time.monotonic() + 60)
        second = await _baidu_ocr(client, _candidate(), "work.png", _png(), time.monotonic() + 60)

    assert first == "本周完成部署\n下周继续验证"
    assert second == first
    assert token_calls == 1
    assert ocr_calls == 2


@pytest.mark.asyncio
async def test_baidu_pdf_is_sent_with_each_page_number() -> None:
    _baidu_token_cache.clear()
    pages = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth/2.0/token":
            return httpx.Response(200, json={"access_token": "token-value"})
        form = parse_qs(request.content.decode())
        page = form["pdf_file_num"][0]
        pages.append(page)
        return httpx.Response(200, json={"words_result": [{"words": f"第{page}页内容"}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await _baidu_ocr(client, _candidate(), "scan.pdf", _pdf(2), time.monotonic() + 60)

    assert pages == ["1", "2"]
    assert "第1页内容" in result
    assert "第2页内容" in result


@pytest.mark.asyncio
async def test_baidu_rejects_oversize_file_before_calling_api() -> None:
    _baidu_token_cache.clear()
    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(500)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(OCRProviderError, match="8MB"):
            await _baidu_ocr(
                client, _candidate(), "large.pdf", b"0" * (7 * 1024 * 1024), time.monotonic() + 60
            )
    assert called is False


def test_baidu_error_hides_every_credential() -> None:
    candidate = _candidate()
    error = OCRProviderError("api-secret very-secret 123456")
    safe = _safe_candidate_error(candidate, error)
    assert "api-secret" not in safe
    assert "very-secret" not in safe
    assert "123456" not in safe
