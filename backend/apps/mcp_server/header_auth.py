"""MCP 调用方鉴权：从 HTTP 头提取 API Key，经 ContextVar 透传给工具。

背景：mcp SDK 2.x 的 `streamable_http_app`（legacy manager 路径）不会把 HTTP 头
塞进 `Context.transport`，因此工具处理函数无法直接读到请求头。这里用一个极薄的
ASGI 中间件（在 `config/asgi.py` 里包住 `mcp_application`）把 `X-MCP-API-Key`
取出，存入 ContextVar；工具函数通过 `MCP_API_KEY_VAR.get()` 读取。

为什么用 ContextVar 而不是从 scope 透传：sync 工具函数由 `anyio.to_thread.run_sync`
在线程池执行，而 anyio 会把当前 contextvars 复制到工作线程，故 ContextVar 在线程内
依然可见，比逐层传 scope 更稳。
"""
from __future__ import annotations

from contextvars import ContextVar
from typing import Any

# ASGI / Starlette 头名统一小写
HEADER_NAME = "x-mcp-api-key"

MCP_API_KEY_VAR: ContextVar[str | None] = ContextVar("mcp_api_key", default=None)


class McpApiKeyMiddleware:
    """ASGI 中间件：从请求头提取 MCP API Key 并写入 ContextVar。"""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        token = None
        try:
            if scope.get("type") == "http":
                raw = scope.get("headers") or []
                headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in raw}
                key = headers.get(HEADER_NAME)
                if not key:
                    # 兼容 Authorization: Bearer <key>
                    auth = headers.get("authorization") or ""
                    if auth.lower().startswith("bearer "):
                        key = auth[7:].strip()
                if key:
                    token = MCP_API_KEY_VAR.set(key.strip())
            await self.app(scope, receive, send)
        finally:
            if token is not None:
                MCP_API_KEY_VAR.reset(token)
