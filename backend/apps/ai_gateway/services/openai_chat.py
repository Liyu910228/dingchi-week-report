import asyncio
import base64
import io
from collections.abc import Sequence
from typing import Any

from asgiref.sync import sync_to_async
from django.conf import settings
from openai import AsyncOpenAI, OpenAIError

from ..models import AIChatAttachment
from ..schemas import ChatMessage, ChatResult, TokenUsage
from .attachments import (
    MAX_EXTRACTED_CHARS,
    attachment_path,
    owned_attachments,
)
from .model_config import EffectiveAIConfig, load_effective_config
from .ocr import OCRError, extract_with_ocr, has_enabled_ocr_keys
from .user_data_tools import TOOLS_SCHEMA, build_user_context, execute_tool

MAX_TOOL_ROUNDS = 6
MAX_ATTACHMENT_CONTEXT_CHARS = 80_000
MAX_CHARS_PER_ATTACHMENT = 25_000


class AIProviderConfigurationError(RuntimeError):
    pass


class AIProviderError(RuntimeError):
    pass


def _image_data_url(attachment: AIChatAttachment) -> str:
    data = attachment_path(attachment).read_bytes()
    mime_type = attachment.mime_type or "image/png"
    if attachment.original_name.lower().endswith(".gif"):
        from PIL import Image

        with Image.open(io.BytesIO(data)) as image:
            image.seek(0)
            output = io.BytesIO()
            image.convert("RGB").save(output, format="PNG")
            data = output.getvalue()
            mime_type = "image/png"
    return f"data:{mime_type};base64,{base64.b64encode(data).decode('ascii')}"


class OpenAIChatService:
    def __init__(self, config: EffectiveAIConfig) -> None:
        if not config.api_key:
            raise AIProviderConfigurationError("尚未配置 AI API Key。")
        if not config.model or config.model == "your-model-name":
            raise AIProviderConfigurationError("尚未配置主模型名称。")
        self.config = config
        self.model = config.model
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url or None,
            timeout=settings.AI_TIMEOUT_SECONDS,
        )

    async def _extract_with_hosted_ocr(self, attachment: AIChatAttachment) -> str:
        data = await sync_to_async(attachment_path(attachment).read_bytes, thread_sensitive=True)()
        try:
            result = await extract_with_ocr(attachment.original_name, data)
        except OCRError as exc:
            raise AIProviderError(str(exc)) from exc
        attachment.extracted_text = result.text[:MAX_EXTRACTED_CHARS]
        attachment.extraction_provider = result.provider
        attachment.extraction_key_id = result.key_id
        await sync_to_async(attachment.save, thread_sensitive=True)(
            update_fields=[
                "extracted_text",
                "extraction_provider",
                "extraction_key_id",
                "updated_at",
            ]
        )
        return attachment.extracted_text

    async def _describe_image(self, attachment: AIChatAttachment) -> str:
        if attachment.extracted_text:
            return attachment.extracted_text
        configured = await sync_to_async(has_enabled_ocr_keys, thread_sensitive=True)()
        if configured:
            return await self._extract_with_hosted_ocr(attachment)
        return await self._describe_image_with_vision(attachment)

    async def _describe_image_with_vision(self, attachment: AIChatAttachment) -> str:
        if attachment.extracted_text:
            return attachment.extracted_text
        data_url = await sync_to_async(_image_data_url, thread_sensitive=True)(attachment)
        try:
            response = await self.client.chat.completions.create(
                model=self.config.vision_model_or_main,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "请详细阅读这张工作资料图片，提取其中的文字、表格、日期、"
                                    "工作事项、进展数据、风险和后续计划。保留关键数字与专有名词，"
                                    "不要编造图片中不存在的信息。用简体中文输出结构化笔记。"
                                ),
                            },
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    }
                ],
                temperature=0,
                max_tokens=2_500,
            )
        except OpenAIError as exc:
            raise AIProviderError(
                "图片解析失败，请在系统设置的模型配置中检查视觉模型及其服务权限。"
            ) from exc
        text = (response.choices[0].message.content or "").strip() if response.choices else ""
        if not text:
            raise AIProviderError("视觉模型未能识别图片内容，请换一张更清晰的图片。")
        attachment.extracted_text = text[:MAX_EXTRACTED_CHARS]
        attachment.extraction_provider = "vision"
        attachment.extraction_key_id = None
        await sync_to_async(attachment.save, thread_sensitive=True)(
            update_fields=[
                "extracted_text",
                "extraction_provider",
                "extraction_key_id",
                "updated_at",
            ]
        )
        return attachment.extracted_text

    async def _provider_messages(
        self, messages: Sequence[ChatMessage], user_id: int
    ) -> list[dict[str, Any]]:
        ids = [int(value) for message in messages for value in message.attachment_ids]
        if not ids:
            return [message.to_provider_dict() for message in messages]
        attachment_map = await sync_to_async(owned_attachments, thread_sensitive=True)(ids, user_id)
        provider_messages: list[dict[str, Any]] = []
        remaining_chars = MAX_ATTACHMENT_CONTEXT_CHARS
        for message in messages:
            content = message.content
            blocks = []
            for value in message.attachment_ids:
                attachment = attachment_map[int(value)]
                if attachment.kind == "image":
                    extracted = await self._describe_image(attachment)
                elif (
                    not attachment.extracted_text
                    and attachment.original_name.lower().endswith(".pdf")
                ):
                    configured = await sync_to_async(has_enabled_ocr_keys, thread_sensitive=True)()
                    if not configured:
                        raise AIProviderError(
                            "该 PDF 没有可提取文本，请先在模型配置中启用 PaddleOCR 或 MinerU Key。"
                        )
                    extracted = await self._extract_with_hosted_ocr(attachment)
                else:
                    extracted = attachment.extracted_text
                if not extracted or remaining_chars <= 0:
                    continue
                allowed = min(MAX_CHARS_PER_ATTACHMENT, remaining_chars)
                clipped = extracted[:allowed]
                if len(extracted) > allowed:
                    clipped += "\n[该附件上下文已截断]"
                remaining_chars -= len(clipped)
                blocks.append(
                    f"\n\n--- 用户上传附件：{attachment.original_name} ---\n"
                    f"{clipped}\n--- 附件结束 ---"
                )
            provider_messages.append(
                {"role": message.role, "content": content + "".join(blocks)}
            )
        return provider_messages

    async def complete(
        self, messages: Sequence[ChatMessage], user: Any | None = None
    ) -> ChatResult:
        if user is None and any(message.attachment_ids for message in messages):
            raise AIProviderConfigurationError("附件对话必须登录。")
        if user is not None:
            provider_messages = await self._provider_messages(messages, user.id)
        else:
            provider_messages = [message.to_provider_dict() for message in messages]

        use_tools = user is not None
        if use_tools:
            user_context = await sync_to_async(build_user_context, thread_sensitive=True)(user)
            provider_messages.insert(0, {"role": "system", "content": user_context})

        total_input = 0
        total_output = 0
        total_tokens = 0
        request_id: str | None = None

        for _round in range(MAX_TOOL_ROUNDS + 1):
            request_kwargs: dict[str, Any] = {
                "model": self.model,
                "messages": provider_messages,
            }
            if use_tools:
                request_kwargs["tools"] = TOOLS_SCHEMA
            try:
                response = await self.client.chat.completions.create(**request_kwargs)
            except OpenAIError as exc:
                raise AIProviderError("大模型服务调用失败，请检查模型配置或稍后重试。") from exc

            if not response.choices:
                raise AIProviderError("大模型服务未返回候选结果。")
            message = response.choices[0].message
            request_id = response.id or request_id
            usage = response.usage
            if usage is not None:
                total_input += getattr(usage, "prompt_tokens", 0) or 0
                total_output += getattr(usage, "completion_tokens", 0) or 0
                total_tokens += getattr(usage, "total_tokens", 0) or 0

            tool_calls = getattr(message, "tool_calls", None)
            if tool_calls:
                if _round == MAX_TOOL_ROUNDS:
                    raise AIProviderError("工具调用轮次超出限制。")
                provider_messages.append(
                    {
                        "role": "assistant",
                        "content": message.content or "",
                        "tool_calls": [
                            {
                                "id": call.id,
                                "type": "function",
                                "function": {
                                    "name": call.function.name,
                                    "arguments": call.function.arguments,
                                },
                            }
                            for call in tool_calls
                        ],
                    }
                )
                for call in tool_calls:
                    tool_result = await sync_to_async(execute_tool, thread_sensitive=True)(
                        call.function.name, call.function.arguments, user.id
                    )
                    provider_messages.append(
                        {"role": "tool", "tool_call_id": call.id, "content": tool_result}
                    )
                continue

            return ChatResult(
                content=message.content or "",
                model=response.model or self.model,
                request_id=request_id,
                usage=TokenUsage(
                    input_tokens=total_input or None,
                    output_tokens=total_output or None,
                    total_tokens=total_tokens or None,
                ),
            )
        raise AIProviderError("工具调用未收敛，请调整问题后重试。")

    async def close(self) -> None:
        await self.client.close()


_chat_service: OpenAIChatService | None = None
_service_lock = asyncio.Lock()


async def get_chat_service() -> OpenAIChatService:
    global _chat_service
    config = await sync_to_async(load_effective_config, thread_sensitive=True)()
    if _chat_service is not None and _chat_service.config.fingerprint == config.fingerprint:
        return _chat_service
    async with _service_lock:
        if _chat_service is not None and _chat_service.config.fingerprint == config.fingerprint:
            return _chat_service
        previous = _chat_service
        _chat_service = OpenAIChatService(config)
        if previous is not None:
            await previous.close()
    return _chat_service


async def close_chat_service() -> None:
    global _chat_service
    if _chat_service is not None:
        await _chat_service.close()
        _chat_service = None
