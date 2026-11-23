"""Stable public entry points for other application modules."""

from collections.abc import Mapping, Sequence
from typing import Any

from .schemas import ChatRequest
from .services.openai_chat import get_chat_service


async def complete_chat(messages: Sequence[Mapping[str, str]]) -> dict[str, Any]:
    """Complete a chat request for protocol adapters and other modules."""
    chat_request = ChatRequest.from_payload({"messages": [dict(message) for message in messages]})
    result = await get_chat_service().complete(chat_request.messages)
    return result.to_dict()
