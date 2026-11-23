"""Hosted PaddleOCR and MinerU clients with randomized, enabled-only key selection."""

from __future__ import annotations

import asyncio
import base64
import io
import json
import random
import time
import uuid
import zipfile
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlencode

import httpx
from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import OperationalError, ProgrammingError
from django.db.models import F
from django.utils import timezone

from ..models import AIOCRKey

PADDLEOCR_JOBS_URL = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"
MINERU_API_ROOT = "https://mineru.net/api/v4"
BAIDU_TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"
BAIDU_GENERAL_URL = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic"
BAIDU_MAX_ENCODED_BYTES = 8 * 1024 * 1024
BAIDU_MAX_PDF_PAGES = 40
MAX_RESULT_BYTES = 50 * 1024 * 1024
MAX_MARKDOWN_MEMBER_BYTES = 5 * 1024 * 1024
_baidu_token_cache: dict[int, tuple[str, float]] = {}
_baidu_token_lock = asyncio.Lock()


class OCRError(RuntimeError):
    """Base error whose message is safe to show without provider secrets."""


class OCRNotConfiguredError(OCRError):
    pass


class OCRProviderError(OCRError):
    pass


class OCRAllProvidersFailedError(OCRError):
    pass


@dataclass(frozen=True, slots=True)
class OCRKeyCandidate:
    id: int
    provider: str
    label: str
    api_key: str = field(repr=False)

    @property
    def display_name(self) -> str:
        provider = {
            AIOCRKey.PROVIDER_PADDLEOCR: "PaddleOCR",
            AIOCRKey.PROVIDER_MINERU: "MinerU",
            AIOCRKey.PROVIDER_BAIDU: "百度 OCR",
        }.get(self.provider, self.provider)
        return f"{provider}（{self.label}）" if self.label else provider


@dataclass(frozen=True, slots=True)
class OCRTextResult:
    text: str
    provider: str
    key_id: int
    provider_name: str


def _request_timeout() -> float:
    return float(getattr(settings, "OCR_REQUEST_TIMEOUT_SECONDS", 45))


def _poll_timeout() -> float:
    return float(getattr(settings, "OCR_POLL_TIMEOUT_SECONDS", 180))


def has_enabled_ocr_keys() -> bool:
    try:
        return AIOCRKey.objects.filter(is_enabled=True).exists()
    except (OperationalError, ProgrammingError):
        return False


def _enabled_candidates() -> list[OCRKeyCandidate]:
    rows = AIOCRKey.objects.filter(is_enabled=True).order_by("id")
    return [
        OCRKeyCandidate(
            id=int(row.id),
            provider=row.provider,
            label=row.label,
            api_key=str(row.api_key),
        )
        for row in rows
        if str(row.api_key).strip()
    ]


def _record_attempt(key_id: int) -> None:
    AIOCRKey.objects.filter(id=key_id).update(
        use_count=F("use_count") + 1,
        last_used_at=timezone.now(),
    )


def _record_result(key_id: int, success: bool, message: str = "") -> None:
    AIOCRKey.objects.filter(id=key_id).update(
        last_status="success" if success else "failed",
        last_error="" if success else message[:300],
    )


def _response_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        payload = None
    if isinstance(payload, dict):
        for key in ("msg", "errorMsg", "message"):
            value = payload.get(key)
            if value:
                return str(value)[:180]
        data = payload.get("data")
        if isinstance(data, dict) and data.get("errorMsg"):
            return str(data["errorMsg"])[:180]
    return ""


def _raise_for_status(response: httpx.Response) -> None:
    if 200 <= response.status_code < 300:
        return
    if response.status_code in {401, 403}:
        raise OCRProviderError("API Key 认证失败。")
    if response.status_code == 429:
        raise OCRProviderError("调用额度或频率受限。")
    detail = _response_message(response)
    suffix = f"：{detail}" if detail else ""
    raise OCRProviderError(f"平台返回 HTTP {response.status_code}{suffix}")


def _json_data(response: httpx.Response) -> dict[str, Any]:
    _raise_for_status(response)
    try:
        payload = response.json()
    except ValueError as exc:
        raise OCRProviderError("平台返回了无效 JSON。") from exc
    if not isinstance(payload, dict):
        raise OCRProviderError("平台响应格式不正确。")
    code = payload.get("code", 0)
    if code not in {0, None}:
        raise OCRProviderError(f"平台业务错误：{str(payload.get('msg') or code)[:180]}")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise OCRProviderError("平台响应缺少 data 对象。")
    return data


async def _network(call, *, timeout_message: str = "OCR 平台请求超时。"):
    try:
        return await call
    except httpx.TimeoutException as exc:
        raise OCRProviderError(timeout_message) from exc
    except httpx.HTTPError as exc:
        raise OCRProviderError("无法连接 OCR 平台，请检查服务器网络。") from exc


def _pruned_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if not isinstance(value, dict):
        return ""
    texts = value.get("rec_texts")
    if isinstance(texts, list):
        scores = value.get("rec_scores")
        blocks = []
        for index, text in enumerate(texts):
            if isinstance(scores, list) and index < len(scores):
                try:
                    if float(scores[index]) <= 0.5:
                        continue
                except (TypeError, ValueError):
                    pass
            if str(text).strip():
                blocks.append(str(text).strip())
        return "\n".join(blocks)
    for key in ("text", "markdown"):
        if isinstance(value.get(key), str):
            return value[key].strip()
    return ""


def _paddle_jsonl_text(content: bytes) -> str:
    pages = []
    try:
        lines = [json.loads(line) for line in content.decode("utf-8").splitlines() if line.strip()]
        for line in lines:
            result = line.get("result", {})
            for page in result.get("ocrResults", []):
                text = _pruned_text(page.get("prunedResult"))
                if text:
                    pages.append(text)
    except (UnicodeDecodeError, ValueError, TypeError, AttributeError) as exc:
        raise OCRProviderError("PaddleOCR 识别结果格式不正确。") from exc
    return "\n\n".join(pages).strip()


async def _paddleocr(
    client: httpx.AsyncClient,
    candidate: OCRKeyCandidate,
    filename: str,
    content: bytes,
    deadline: float,
) -> str:
    headers = {"Authorization": f"Bearer {candidate.api_key}"}
    optional = {
        "useDocOrientationClassify": False,
        "useDocUnwarping": False,
        "useTextlineOrientation": False,
        "visualize": False,
    }
    response = await _network(
        client.post(
            PADDLEOCR_JOBS_URL,
            headers=headers,
            data={"model": "PP-OCRv5", "optionalPayload": json.dumps(optional)},
            files={"file": (filename, content)},
        )
    )
    job_id = _json_data(response).get("jobId")
    if not isinstance(job_id, str) or not job_id:
        raise OCRProviderError("PaddleOCR 未返回任务 ID。")

    interval = 2.0
    while time.monotonic() < deadline:
        response = await _network(client.get(f"{PADDLEOCR_JOBS_URL}/{job_id}", headers=headers))
        data = _json_data(response)
        state = data.get("state")
        if state == "failed":
            raise OCRProviderError(f"识别失败：{str(data.get('errorMsg') or '未知错误')[:180]}")
        if state == "done":
            result_url = data.get("resultUrl")
            json_url = result_url.get("jsonUrl") if isinstance(result_url, dict) else None
            if not isinstance(json_url, str) or not json_url.startswith("https://"):
                raise OCRProviderError("PaddleOCR 未返回有效的结果地址。")
            result_response = await _network(client.get(json_url))
            _raise_for_status(result_response)
            if len(result_response.content) > MAX_RESULT_BYTES:
                raise OCRProviderError("PaddleOCR 结果文件过大。")
            return _paddle_jsonl_text(result_response.content)
        if state not in {"pending", "running"}:
            raise OCRProviderError("PaddleOCR 返回了未知任务状态。")
        await asyncio.sleep(min(interval, max(0.0, deadline - time.monotonic())))
        interval = min(interval * 1.5, 8.0)
    raise OCRProviderError("PaddleOCR 等待识别结果超时。")


def _mineru_markdown(content: bytes) -> str:
    if len(content) > MAX_RESULT_BYTES:
        raise OCRProviderError("MinerU 结果压缩包过大。")
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            members = [item for item in archive.infolist() if not item.is_dir()]
            member = next((item for item in members if item.filename.endswith("/full.md")), None)
            if member is None:
                member = next((item for item in members if item.filename == "full.md"), None)
            if member is None:
                markdown = [item for item in members if item.filename.endswith(".md")]
                member = max(markdown, key=lambda item: item.file_size) if markdown else None
            if member is None or member.file_size > MAX_MARKDOWN_MEMBER_BYTES:
                raise OCRProviderError("MinerU 结果中没有可用的 Markdown 文本。")
            return archive.read(member).decode("utf-8").strip()
    except OCRProviderError:
        raise
    except (zipfile.BadZipFile, UnicodeDecodeError, OSError) as exc:
        raise OCRProviderError("MinerU 结果压缩包无法解析。") from exc


async def _mineru(
    client: httpx.AsyncClient,
    candidate: OCRKeyCandidate,
    filename: str,
    content: bytes,
    deadline: float,
) -> str:
    headers = {"Authorization": f"Bearer {candidate.api_key}"}
    payload = {
        "files": [{"name": filename, "data_id": uuid.uuid4().hex, "is_ocr": True}],
        "model_version": "vlm",
        "enable_formula": True,
        "enable_table": True,
        "language": "ch",
    }
    response = await _network(
        client.post(f"{MINERU_API_ROOT}/file-urls/batch", headers=headers, json=payload)
    )
    data = _json_data(response)
    batch_id = data.get("batch_id")
    urls = data.get("file_urls")
    if not isinstance(batch_id, str) or not isinstance(urls, list) or not urls:
        raise OCRProviderError("MinerU 未返回上传任务信息。")
    upload_url = urls[0]
    if not isinstance(upload_url, str) or not upload_url.startswith("https://"):
        raise OCRProviderError("MinerU 返回了无效上传地址。")
    upload_response = await _network(client.put(upload_url, content=content))
    _raise_for_status(upload_response)

    while time.monotonic() < deadline:
        response = await _network(
            client.get(f"{MINERU_API_ROOT}/extract-results/batch/{batch_id}", headers=headers)
        )
        data = _json_data(response)
        results = data.get("extract_result")
        item = results[0] if isinstance(results, list) and results else {}
        state = item.get("state") if isinstance(item, dict) else None
        if state == "failed":
            raise OCRProviderError(f"识别失败：{str(item.get('err_msg') or '未知错误')[:180]}")
        if state == "done":
            zip_url = item.get("full_zip_url")
            if not isinstance(zip_url, str) or not zip_url.startswith("https://"):
                raise OCRProviderError("MinerU 未返回有效的结果地址。")
            result_response = await _network(client.get(zip_url))
            _raise_for_status(result_response)
            return _mineru_markdown(result_response.content)
        if state not in {None, "waiting-file", "pending", "running", "converting"}:
            raise OCRProviderError("MinerU 返回了未知任务状态。")
        await asyncio.sleep(min(3.0, max(0.0, deadline - time.monotonic())))
    raise OCRProviderError("MinerU 等待识别结果超时。")


def _baidu_credentials(candidate: OCRKeyCandidate) -> dict[str, str]:
    try:
        value = json.loads(candidate.api_key)
        credentials = {
            key: str(value.get(key) or "").strip()
            for key in ("app_id", "api_key", "secret_key")
        }
    except (ValueError, TypeError, AttributeError) as exc:
        raise OCRProviderError("百度 OCR 凭据格式不正确。") from exc
    if not all(credentials.values()):
        raise OCRProviderError("百度 OCR 的 AppID、API Key、Secret Key 必须完整配置。")
    return credentials


def _baidu_encoded_file(filename: str, content: bytes) -> tuple[str, str]:
    field = "pdf_file" if filename.lower().endswith(".pdf") else "image"
    encoded = ""
    if field == "image":
        try:
            from PIL import Image, UnidentifiedImageError

            with Image.open(io.BytesIO(content)) as image:
                image.seek(0)
                if image.width < 15 or image.height < 15:
                    raise OCRProviderError("图片最短边不能小于 15 像素。")
                if max(image.width, image.height) > 4096:
                    image.thumbnail((4096, 4096), Image.Resampling.LANCZOS)
                if image.mode not in {"RGB", "L"}:
                    image = image.convert("RGB")
                output = io.BytesIO()
                image.save(output, format="PNG", optimize=True)
                encoded = base64.b64encode(output.getvalue()).decode("ascii")
                if len(urlencode({field: encoded}).encode("ascii")) > BAIDU_MAX_ENCODED_BYTES:
                    output = io.BytesIO()
                    image.save(output, format="JPEG", quality=90, optimize=True)
                    encoded = base64.b64encode(output.getvalue()).decode("ascii")
        except (UnidentifiedImageError, OSError) as exc:
            raise OCRProviderError("图片无法解析，无法转换为百度 OCR 支持的格式。") from exc
    if not encoded:
        encoded = base64.b64encode(content).decode("ascii")
    if len(urlencode({field: encoded}).encode("ascii")) > BAIDU_MAX_ENCODED_BYTES:
        raise OCRProviderError("文件 Base64 编码后超过百度 OCR 的 8MB 限制，未发起调用。")
    return field, encoded


async def _baidu_access_token(
    client: httpx.AsyncClient, candidate: OCRKeyCandidate, force_refresh: bool = False
) -> str:
    now = time.monotonic()
    cached = _baidu_token_cache.get(candidate.id)
    if not force_refresh and cached and cached[1] > now:
        return cached[0]
    async with _baidu_token_lock:
        cached = _baidu_token_cache.get(candidate.id)
        if not force_refresh and cached and cached[1] > time.monotonic():
            return cached[0]
        credentials = _baidu_credentials(candidate)
        response = await _network(
            client.get(
                BAIDU_TOKEN_URL,
                params={
                    "grant_type": "client_credentials",
                    "client_id": credentials["api_key"],
                    "client_secret": credentials["secret_key"],
                },
            )
        )
        _raise_for_status(response)
        try:
            payload = response.json()
        except ValueError as exc:
            raise OCRProviderError("百度 OCR 认证接口返回格式不正确。") from exc
        token = payload.get("access_token")
        if not isinstance(token, str) or not token:
            raise OCRProviderError("百度 OCR 认证失败，请检查 API Key 和 Secret Key。")
        expires_in = int(payload.get("expires_in") or 2_592_000)
        _baidu_token_cache[candidate.id] = (
            token,
            time.monotonic() + max(60, expires_in - 300),
        )
        return token


def _baidu_error(payload: dict[str, Any]) -> None:
    code = payload.get("error_code")
    if code in {6, 14}:
        raise OCRProviderError("百度 OCR 应用未开通对应接口权限。")
    if code in {17, 18, 19}:
        raise OCRProviderError("百度 OCR 免费额度或 QPS 已超限。")
    if code == 336004:
        raise OCRProviderError("文件大小不符合百度 OCR 限制。")
    if code:
        message = str(payload.get("error_msg") or "未知错误")[:180]
        raise OCRProviderError(f"百度 OCR 识别失败（{code}）：{message}")


async def _baidu_request(
    client: httpx.AsyncClient,
    candidate: OCRKeyCandidate,
    field: str,
    encoded: str,
    page_number: int | None = None,
    retry_auth: bool = True,
) -> str:
    token = await _baidu_access_token(client, candidate)
    data = {
        field: encoded,
        "language_type": "CHN_ENG",
        "detect_direction": "true",
        "probability": "false",
    }
    if page_number is not None:
        data["pdf_file_num"] = str(page_number)
    response = await _network(
        client.post(
            BAIDU_GENERAL_URL,
            params={"access_token": token},
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    )
    _raise_for_status(response)
    try:
        payload = response.json()
    except ValueError as exc:
        raise OCRProviderError("百度 OCR 返回了无效 JSON。") from exc
    if not isinstance(payload, dict):
        raise OCRProviderError("百度 OCR 响应格式不正确。")
    if payload.get("error_code") in {110, 111} and retry_auth:
        await _baidu_access_token(client, candidate, force_refresh=True)
        return await _baidu_request(
            client, candidate, field, encoded, page_number, retry_auth=False
        )
    _baidu_error(payload)
    rows = payload.get("words_result")
    if not isinstance(rows, list):
        raise OCRProviderError("百度 OCR 未返回识别文本。")
    return "\n".join(
        str(row.get("words") or "").strip()
        for row in rows
        if isinstance(row, dict) and str(row.get("words") or "").strip()
    ).strip()


async def _baidu_ocr(
    client: httpx.AsyncClient,
    candidate: OCRKeyCandidate,
    filename: str,
    content: bytes,
    deadline: float,
) -> str:
    field, encoded = _baidu_encoded_file(filename, content)
    if field == "image":
        return await _baidu_request(client, candidate, field, encoded)
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(content))
        if reader.is_encrypted:
            raise OCRProviderError("加密 PDF 无法使用百度 OCR 识别。")
        total_pages = len(reader.pages)
    except OCRProviderError:
        raise
    except Exception as exc:
        raise OCRProviderError("PDF 无法解析，无法使用百度 OCR。") from exc
    if total_pages == 0:
        raise OCRProviderError("PDF 没有可识别页面。")
    pages = []
    for page_number in range(1, min(total_pages, BAIDU_MAX_PDF_PAGES) + 1):
        if time.monotonic() >= deadline:
            raise OCRProviderError("百度 OCR 按页识别超时。")
        text = await _baidu_request(client, candidate, field, encoded, page_number)
        pages.append(f"--- 第 {page_number} 页 ---\n{text}" if total_pages > 1 else text)
    if total_pages > BAIDU_MAX_PDF_PAGES:
        pages.append(f"[PDF 共 {total_pages} 页，仅识别前 {BAIDU_MAX_PDF_PAGES} 页]")
    return "\n\n".join(pages).strip()


async def _run_provider(
    client: httpx.AsyncClient,
    candidate: OCRKeyCandidate,
    filename: str,
    content: bytes,
    deadline: float,
) -> str:
    if candidate.provider == AIOCRKey.PROVIDER_PADDLEOCR:
        return await _paddleocr(client, candidate, filename, content, deadline)
    if candidate.provider == AIOCRKey.PROVIDER_BAIDU:
        return await _baidu_ocr(client, candidate, filename, content, deadline)
    return await _mineru(client, candidate, filename, content, deadline)


def _safe_candidate_error(candidate: OCRKeyCandidate, error: Exception) -> str:
    message = str(error).replace(candidate.api_key, "***")
    if candidate.provider == AIOCRKey.PROVIDER_BAIDU:
        try:
            credentials = _baidu_credentials(candidate)
        except OCRProviderError:
            credentials = {}
        for secret in credentials.values():
            message = message.replace(secret, "***")
    return message[:300]


async def extract_with_ocr(filename: str, content: bytes) -> OCRTextResult:
    """Try a random permutation of enabled keys, recording only safe diagnostics."""

    candidates = await sync_to_async(_enabled_candidates, thread_sensitive=True)()
    if not candidates:
        raise OCRNotConfiguredError("尚未配置已启用的 PaddleOCR、MinerU 或百度 OCR API Key。")
    random.SystemRandom().shuffle(candidates)
    deadline = time.monotonic() + _poll_timeout()
    errors = []
    for candidate in candidates:
        if time.monotonic() >= deadline:
            errors.append("OCR 总等待时间已用尽。")
            break
        await sync_to_async(_record_attempt, thread_sensitive=True)(candidate.id)
        try:
            remaining = max(1.0, deadline - time.monotonic())
            timeout = httpx.Timeout(min(_request_timeout(), remaining))
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                text = await _run_provider(client, candidate, filename, content, deadline)
            if not text.strip():
                raise OCRProviderError("识别结果为空，请换用更清晰的文件。")
        except OCRProviderError as exc:
            message = _safe_candidate_error(candidate, exc)
            errors.append(f"{candidate.display_name}：{message}")
            await sync_to_async(_record_result, thread_sensitive=True)(candidate.id, False, message)
            continue
        await sync_to_async(_record_result, thread_sensitive=True)(candidate.id, True)
        return OCRTextResult(
            text=text.strip(),
            provider=candidate.provider,
            key_id=candidate.id,
            provider_name=candidate.display_name,
        )
    raise OCRAllProvidersFailedError("所有已启用 OCR Key 均调用失败；" + "；".join(errors))
