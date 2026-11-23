import pytest
from mcp import Client

from apps.mcp_server.server import mcp_server


@pytest.mark.asyncio
async def test_mcp_lists_and_calls_health_tool() -> None:
    async with Client(mcp_server) as client:
        tools = await client.list_tools()
        names = {tool.name for tool in tools.tools}
        result = await client.call_tool("service_health", {})

    assert {"service_health", "ask_ai"}.issubset(names)
    assert not result.is_error
