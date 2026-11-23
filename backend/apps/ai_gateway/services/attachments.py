"""Private AI chat attachment storage, validation and text extraction."""

from __future__ import annotations

import csv
import io
import json
import uuid
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from ..models import AIChatAttachment

MAX_FILES_PER_MESSAGE = 4
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_EXTRACTED_CHARS = 40_000
MAX_PDF_PAGES = 40
MAX_SHEET_ROWS = 1_000
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
DOCUMENT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".pdf", ".docx", ".xlsx"}
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | DOCUMENT_EXTENSIONS


class AttachmentValidationError(ValueError):
    pass


def _clip(text: str, limit: int = MAX_EXTRACTED_CHARS) -> str:
    normalized = text.replace("\x00", "").strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[:limit] + "\n\n[附件内容过长，已截断]"


def _decode_text(data: bytes) -> str:
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise AttachmentValidationError("文本文件编码不受支持，请使用 UTF-8 或 GB18030。")


def _extract_csv(data: bytes) -> str:
    text = _decode_text(data)
    rows = list(csv.reader(io.StringIO(text)))
    return "\n".join(" | ".join(cell.strip() for cell in row) for row in rows[:MAX_SHEET_ROWS])


def _extract_json(data: bytes) -> str:
    try:
        value = json.loads(_decode_text(data))
        return json.dumps(value, ensure_ascii=False, indent=2)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise AttachmentValidationError("JSON 文件格式无效。") from exc


def _extract_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(data))
        blocks = []
        for page in reader.pages[:MAX_PDF_PAGES]:
            blocks.append(page.extract_text() or "")
            if sum(len(block) for block in blocks) >= MAX_EXTRACTED_CHARS:
                break
        return "\n\n".join(blocks)
    except Exception as exc:
        raise AttachmentValidationError("PDF 无法解析，请确认文件未加密且未损坏。") from exc


def _extract_docx(data: bytes) -> str:
    from docx import Document

    try:
        document = Document(io.BytesIO(data))
        blocks = [p.text for p in document.paragraphs if p.text.strip()]
        for table in document.tables:
            for row in table.rows:
                blocks.append(" | ".join(cell.text.strip() for cell in row.cells))
        return "\n".join(blocks)
    except Exception as exc:
        raise AttachmentValidationError("Word 文档无法解析，请使用有效的 .docx 文件。") from exc


def _extract_xlsx(data: bytes) -> str:
    from openpyxl import load_workbook

    try:
        workbook = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        blocks = []
        for sheet in workbook.worksheets[:20]:
            blocks.append(f"## 工作表：{sheet.title}")
            for row_index, row in enumerate(sheet.iter_rows(values_only=True), start=1):
                if row_index > MAX_SHEET_ROWS:
                    blocks.append("[工作表行数过多，已截断]")
                    break
                values = ["" if value is None else str(value) for value in row]
                if any(values):
                    blocks.append(" | ".join(values))
                if sum(len(block) for block in blocks) >= MAX_EXTRACTED_CHARS:
                    break
        workbook.close()
        return "\n".join(blocks)
    except Exception as exc:
        raise AttachmentValidationError("Excel 文件无法解析，请使用有效的 .xlsx 文件。") from exc


def _validate_image(data: bytes) -> None:
    from PIL import Image, UnidentifiedImageError

    try:
        with Image.open(io.BytesIO(data)) as image:
            image.verify()
        with Image.open(io.BytesIO(data)) as image:
            if image.width * image.height > 30_000_000:
                raise AttachmentValidationError("图片像素过大，请压缩后上传。")
    except (UnidentifiedImageError, OSError) as exc:
        raise AttachmentValidationError("图片已损坏或格式不受支持。") from exc


def _extract_document(extension: str, data: bytes) -> str:
    if extension in {".txt", ".md"}:
        return _decode_text(data)
    if extension == ".csv":
        return _extract_csv(data)
    if extension == ".json":
        return _extract_json(data)
    if extension == ".pdf":
        return _extract_pdf(data)
    if extension == ".docx":
        return _extract_docx(data)
    if extension == ".xlsx":
        return _extract_xlsx(data)
    raise AttachmentValidationError("不支持的文档格式。")


def serialize_attachment(attachment: AIChatAttachment) -> dict[str, Any]:
    return {
        "id": str(attachment.id),
        "name": attachment.original_name,
        "mime_type": attachment.mime_type,
        "size": attachment.file_size,
        "kind": attachment.kind,
    }


def attachment_path(attachment: AIChatAttachment) -> Path:
    root = (Path(settings.MEDIA_ROOT) / "ai_chat").resolve()
    path = (root / attachment.storage_name).resolve()
    if root not in path.parents:
        raise AttachmentValidationError("附件存储路径无效。")
    return path


@transaction.atomic
def save_uploaded_attachment(upload: UploadedFile, user_id: int) -> dict[str, Any]:
    original_name = Path(str(upload.name or "")).name.strip()
    if not original_name or len(original_name) > 255:
        raise AttachmentValidationError("文件名无效或过长。")
    extension = Path(original_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise AttachmentValidationError(
            "仅支持 PNG/JPG/WebP/GIF 图片，以及 PDF、DOCX、XLSX、TXT、MD、CSV、JSON 文件。"
        )
    if upload.size <= 0:
        raise AttachmentValidationError("不能上传空文件。")
    configured_max = int(getattr(settings, "ATTACHMENT_MAX_SIZE_BYTES", MAX_FILE_SIZE))
    if upload.size > min(MAX_FILE_SIZE, configured_max):
        raise AttachmentValidationError("单个附件不能超过 10MB。")
    data = upload.read()
    kind = "image" if extension in IMAGE_EXTENSIONS else "document"
    if kind == "image":
        _validate_image(data)
        extracted = ""
        mime_type = "image/jpeg" if extension in {".jpg", ".jpeg"} else f"image/{extension[1:]}"
    else:
        extracted = _clip(_extract_document(extension, data))
        if not extracted and extension != ".pdf":
            raise AttachmentValidationError("未能从文件中提取到文本，请确认文件内容有效。")
        mime_type = upload.content_type or "application/octet-stream"

    storage_name = f"{user_id}/{uuid.uuid4().hex}{extension}"
    path = (Path(settings.MEDIA_ROOT) / "ai_chat" / storage_name).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    try:
        attachment = AIChatAttachment.objects.create(
            uploader_id=user_id,
            original_name=original_name,
            storage_name=storage_name,
            mime_type=mime_type,
            file_size=len(data),
            kind=kind,
            extracted_text=extracted,
        )
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return serialize_attachment(attachment)


def owned_attachments(attachment_ids: list[int], user_id: int) -> dict[int, AIChatAttachment]:
    unique_ids = list(dict.fromkeys(attachment_ids))
    rows = AIChatAttachment.objects.filter(id__in=unique_ids, uploader_id=user_id)
    result = {int(row.id): row for row in rows}
    if len(result) != len(unique_ids):
        raise AttachmentValidationError("附件不存在、已失效或无权访问。")
    return result
