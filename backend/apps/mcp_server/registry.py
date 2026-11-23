"""Central registration of all MCP capability modules."""

from mcp.server import MCPServer

from .modules.ai.tools import register as register_ai_tools
from .modules.system.tools import register as register_system_tools
from .modules.weekly_report.tools import register as register_weekly_report_tools


def register_tools(server: MCPServer) -> None:
    """Register every capability module on the shared MCP server."""
    register_system_tools(server)
    register_ai_tools(server)
    register_weekly_report_tools(server)
