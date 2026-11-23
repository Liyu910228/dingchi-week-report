import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

django_application = get_asgi_application()

from django.conf import settings  # noqa: E402
from starlette.applications import Starlette  # noqa: E402
from starlette.middleware import Middleware  # noqa: E402
from starlette.middleware.cors import CORSMiddleware  # noqa: E402
from starlette.routing import Mount  # noqa: E402

from apps.ai_gateway.services.openai_chat import close_chat_service  # noqa: E402
from apps.core.middleware.trace_id import TraceIdMiddleware  # noqa: E402
from apps.mcp_server.header_auth import McpApiKeyMiddleware  # noqa: E402
from apps.mcp_server.server import mcp_server  # noqa: E402

mcp_application = mcp_server.streamable_http_app(streamable_http_path="/")
# 从 HTTP 头（X-MCP-API-Key / Authorization: Bearer）提取调用方密钥，经 ContextVar 透传工具
mcp_application = McpApiKeyMiddleware(mcp_application)


@asynccontextmanager
async def lifespan(_: Starlette) -> AsyncIterator[None]:
    async with mcp_server.session_manager.run():
        try:
            yield
        finally:
            await close_chat_service()


application = Starlette(
    routes=[
        Mount("/mcp", app=mcp_application),
        Mount("/", app=django_application),
    ],
    middleware=[
        Middleware(TraceIdMiddleware),
        Middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ALLOWED_ORIGINS,
            allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
            allow_methods=settings.CORS_ALLOWED_METHODS,
            allow_headers=settings.CORS_ALLOW_HEADERS,
            expose_headers=settings.CORS_EXPOSE_HEADERS,
        ),
    ],
    lifespan=lifespan,
)
