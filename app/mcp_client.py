from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from contextlib import asynccontextmanager, AsyncExitStack

mcp_client = MultiServerMCPClient(
    {
        "research-tools":{
            "command": "python",
            "args": ["-m", "app.mcp_server.server"],
            "transport": "stdio",
        }
    }
)

_exit_stack: AsyncExitStack | None = None
_session = None
_tools = None

async def start_mcp_session():
    """Open one persistent MCP session and load tools bound to it. Call once at app startup"""
    global _exit_stack, _session, _tools
    _exit_stack = AsyncExitStack()
    _session = await _exit_stack.enter_async_context(mcp_client.session("research-tools"))
    _tools = await load_mcp_tools(_session)

    return _tools

async def stop_mcp_session():
    """Close the persistent session cleanly. Call once at app shutdown"""
    global _exit_stack

    if _exit_stack is not None:
        await _exit_stack.aclose()

def get_cached_tools():
    """Return the tools bound to the persistent session. Must call start_mcp_session() first."""
    if _tools is None:
        raise RuntimeError("MCP session not started - call start_mcp_session() at app startup")
    return _tools