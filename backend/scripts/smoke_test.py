import argparse
import asyncio
import json
from urllib.request import urlopen

from mcp import Client


def check_api(base_url: str) -> dict[str, object]:
    with urlopen(f"{base_url}/api/v1/health/live/", timeout=5) as response:
        payload = json.load(response)
        status = response.status
    if status != 200 or payload.get("data", {}).get("status") != "ok":
        raise RuntimeError("API liveness check failed")
    return payload


async def check_mcp(base_url: str) -> list[str]:
    async with Client(f"{base_url}/mcp/") as client:
        tools = await client.list_tools()
        result = await client.call_tool("service_health", {})
    if result.is_error:
        raise RuntimeError("MCP health tool failed")
    return [tool.name for tool in tools.tools]


async def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test the running ASGI application.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    api = check_api(base_url)
    tools = await check_mcp(base_url)
    print(json.dumps({"api": api["data"]["status"], "mcp_tools": tools}, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
