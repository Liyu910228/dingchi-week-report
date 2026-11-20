from collections.abc import Sequence
from typing import Any

from asgiref.sync import sync_to_async
from django.conf import settings
from openai import AsyncOpenAI, OpenAIError

from ..schemas import ChatMessage, ChatResult, TokenUsage
from .user_data_tools import TOOLS_SCHEMA, build_user_context, execute_tool

# 工具调用最大轮数，防止模型循环调用不收敛
MAX_TOOL_ROUNDS = 6


class AIProviderConfigurationError(RuntimeError):
    pass


class AIProviderError(RuntimeError):
    pass


class OpenAIChatService:
    def __init__(self) -> None:
        if not settings.AI_API_KEY:
            raise AIProviderConfigurationError("尚未配置 AI_API_KEY。")
        if not settings.AI_MODEL or settings.AI_MODEL == "your-model-name":
            raise AIProviderConfigurationError("尚未配置 AI_MODEL。")

        client_options: dict[str, Any] = {
            "api_key": settings.AI_API_KEY,
            "timeout": settings.AI_TIMEOUT_SECONDS,
        }
        if settings.AI_BASE_URL:
            client_options["base_url"] = settings.AI_BASE_URL

        self.model = settings.AI_MODEL
        self.client = AsyncOpenAI(**client_options)

    async def complete(
        self, messages: Sequence[ChatMessage], user: Any | None = None
    ) -> ChatResult:
        provider_messages: list[dict[str, Any]] = [
            message.to_provider_dict() for message in messages
        ]

        # 注入当前登录用户上下文，并启用数据查询工具（function calling）
        use_tools = user is not None
        if use_tools:
            # build_user_context 内部含同步 ORM 查询，必须放入线程执行
            user_context = await sync_to_async(
                build_user_context, thread_sensitive=True
            )(user)
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
                raise AIProviderError("大模型服务调用失败，请稍后重试。") from exc

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
                    # 工具内部使用同步 ORM，必须放入线程执行
                    tool_result = await sync_to_async(
                        execute_tool, thread_sensitive=True
                    )(call.function.name, call.function.arguments, user.id)
                    provider_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.id,
                            "content": tool_result,
                        }
                    )
                continue

            content = message.content or ""
            return ChatResult(
                content=content,
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


def get_chat_service() -> OpenAIChatService:
    global _chat_service
    if _chat_service is None:
        _chat_service = OpenAIChatService()
    return _chat_service


async def close_chat_service() -> None:
    global _chat_service
    if _chat_service is not None:
        await _chat_service.close()
        _chat_service = None
