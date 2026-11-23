from dataclasses import asdict, dataclass
from typing import Any, Literal

ChatRole = Literal["system", "user", "assistant"]
ALLOWED_ROLES: set[str] = {"system", "user", "assistant"}
MAX_MESSAGES = 50
MAX_CONTENT_LENGTH = 20_000
MAX_TOTAL_CONTENT_LENGTH = 100_000
MAX_ATTACHMENTS_PER_MESSAGE = 4
MAX_TOTAL_ATTACHMENTS = 12


class ChatPayloadError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: ChatRole
    content: str
    attachment_ids: tuple[str, ...] = ()

    def to_provider_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass(frozen=True, slots=True)
class ChatRequest:
    messages: tuple[ChatMessage, ...]

    @classmethod
    def from_payload(cls, payload: Any) -> "ChatRequest":
        if not isinstance(payload, dict):
            raise ChatPayloadError("请求体必须是 JSON 对象。")

        raw_messages = payload.get("messages")
        if not isinstance(raw_messages, list) or not raw_messages:
            raise ChatPayloadError("messages 必须是非空数组。")
        if len(raw_messages) > MAX_MESSAGES:
            raise ChatPayloadError(f"messages 最多包含 {MAX_MESSAGES} 条消息。")

        messages: list[ChatMessage] = []
        total_length = 0
        total_attachments = 0
        for index, item in enumerate(raw_messages):
            if not isinstance(item, dict):
                raise ChatPayloadError(f"messages[{index}] 必须是对象。")

            role = item.get("role")
            content = item.get("content")
            if role not in ALLOWED_ROLES:
                raise ChatPayloadError(f"messages[{index}].role 不受支持。")
            if not isinstance(content, str) or not content.strip():
                raise ChatPayloadError(f"messages[{index}].content 不能为空。")

            clean_content = content.strip()
            if len(clean_content) > MAX_CONTENT_LENGTH:
                raise ChatPayloadError(
                    f"messages[{index}].content 不能超过 {MAX_CONTENT_LENGTH} 个字符。"
                )
            total_length += len(clean_content)
            raw_attachment_ids = item.get("attachment_ids", [])
            if not isinstance(raw_attachment_ids, list):
                raise ChatPayloadError(f"messages[{index}].attachment_ids 必须是数组。")
            if len(raw_attachment_ids) > MAX_ATTACHMENTS_PER_MESSAGE:
                raise ChatPayloadError("每条消息最多关联 4 个附件。")
            if raw_attachment_ids and role != "user":
                raise ChatPayloadError("只有用户消息可以关联附件。")
            attachment_ids = tuple(str(value) for value in raw_attachment_ids)
            if any(not value.isdigit() or len(value) > 32 for value in attachment_ids):
                raise ChatPayloadError("附件 ID 格式无效。")
            total_attachments += len(attachment_ids)
            messages.append(
                ChatMessage(role=role, content=clean_content, attachment_ids=attachment_ids)
            )

        if total_length > MAX_TOTAL_CONTENT_LENGTH:
            raise ChatPayloadError("消息总长度超出限制。")
        if total_attachments > MAX_TOTAL_ATTACHMENTS:
            raise ChatPayloadError("一次对话最多携带 12 个附件引用。")

        return cls(messages=tuple(messages))


@dataclass(frozen=True, slots=True)
class TokenUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True, slots=True)
class ChatResult:
    content: str
    model: str
    request_id: str | None
    usage: TokenUsage

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
