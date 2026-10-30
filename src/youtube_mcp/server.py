
import os

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "youtube-video-intelligence",
    host="0.0.0.0",
    port=int(os.getenv("MCP_PORT", "8000")),
)


@mcp.tool()
def health_check() -> str:
    """Check whether the YouTube MCP server is running."""
    return "YouTube Video Intelligence MCP Server is running."


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
