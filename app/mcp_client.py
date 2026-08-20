from langchain_mcp_adapters.client import MultiServerMCPClient

mcp_client = MultiServerMCPClient(
    {
        "research-tools":{
            "command": "python",
            "args": ["-m", "app.mcp_server.server"],
            "transport": "stdio",
        }
    }
)