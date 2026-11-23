"""MCP tools for AI capabilities."""

from typing import Any

from mcp.server import MCPServer

from apps.ai_gateway.public import complete_chat

DEFAULT_SYSTEM_PROMPT = "你是一名专业的企业周报助手。"


def register(server: MCPServer) -> None:
    """Register AI capability tools on the shared MCP server."""

    @server.tool()
    async def ask_ai(
        prompt: str,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ) -> dict[str, Any]:
        """调用已配置的大模型，根据提示生成内容。

        工具/入口：ask_ai，经统一 MCP HTTP 入口 /mcp/ 调用。
        认证/权限：由 MCP 入口统一认证和工具授权；幂等：否，调用方不得无条件自动重试。
        请求参数：prompt 为必填非空字符串；system_prompt 为可选字符串，默认使用企业周报助手提示词；
          长度限制和敏感信息规则与 AI REST 接口一致。
        成功响应：返回 JSON 对象，包含 content、model、request_id 和 usage；不返回上游原始响应。
        失败响应：统一映射 AI_NOT_CONFIGURED、AI_PROVIDER_ERROR、INVALID_REQUEST
          等稳定错误；保留 trace_id。
        兼容性：新增结果字段向后兼容；工具参数改名、改类型或改变语义必须升级工具版本并保留迁移期。
        """
        return await complete_chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]
        )
