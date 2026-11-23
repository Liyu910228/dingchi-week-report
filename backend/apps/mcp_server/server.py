from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from .registry import register_tools

mcp_server = MCPServer(
    "dingchi-week-report",
    instructions=(
        "提供鼎驰周报系统的健康检查、AI 文本生成，"
        "以及按调用方数据范围鉴权的周报数据查询工具。"
    ),
)

register_tools(mcp_server)

# DNS 重绑定保护：显式声明允许访问 /mcp 的 Host 头。
# 经 nginx 反代时 Host 头为真实域名/IP（无端口），直连 uvicorn 时为本机 127.0.0.1:<port>。
# 注意：MCP SDK 仅支持精确匹配和 `host:*` 端口通配，不支持 `*.domain` 通配，子域需显式列出。
_mcp_allowed_hosts = [
    "weekly.dingchi.com",
    "121.40.42.131",
    "127.0.0.1:*",
    "localhost:*",
    "[::1]:*",
]
mcp_application = mcp_server.streamable_http_app(
    streamable_http_path="/",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=_mcp_allowed_hosts,
        allowed_origins=[],  # 同源/无 Origin 放行；MCP 客户端（非浏览器）通常不带 Origin
    ),
)
