"""MCP tools for system capabilities."""

from mcp.server import MCPServer


def register(server: MCPServer) -> None:
    """Register system capability tools on the shared MCP server."""

    @server.tool()
    def service_health() -> dict[str, str]:
        """返回 MCP 服务自身的存活状态。

        工具/入口：service_health，经统一 MCP HTTP 入口 /mcp/ 调用。
        认证/权限：公开健康探针；不读取业务数据；幂等：是。
        请求参数：无。
        成功响应：JSON 对象，status 固定为 ok，service 为服务标识字符串。
        失败响应：MCP 协议错误由统一入口处理，不返回堆栈、配置或连接信息。
        追踪/兼容：调用链使用统一 trace_id；新增字段向后兼容，既有字段语义不可静默修改。
        """
        return {"status": "ok", "service": "dingchi-week-report-mcp"}
