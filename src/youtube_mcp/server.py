import os

from mcp.server.fastmcp import FastMCP

from youtube_mcp.auth.youtube import build_youtube_client
from youtube_mcp.engagement.analysis import (
    analyze_engagement_data,
    fetch_engagement_data,
    parse_period,
    validate_playlist_ids,
)
from youtube_mcp.providers.youtube import YouTubeDataProvider

mcp = FastMCP(
    "youtube-video-intelligence",
    host="0.0.0.0",
    port=int(os.getenv("MCP_PORT", "8000")),
)


@mcp.tool()
def health_check() -> str:
    """Check whether the YouTube MCP server is running."""
    return "YouTube Video Intelligence MCP Server is running."


@mcp.tool()
def analyze_engagement(
    start_date: str,
    end_date: str,
    selected_playlist_ids: list[str] | None = None,
    comparison_start_date: str | None = None,
    comparison_end_date: str | None = None,
) -> dict[str, object]:
    """Analyze likes, subscriptions and selected playlists for a date range."""
    start, end = parse_period(start_date, end_date)
    if (comparison_start_date is None) != (comparison_end_date is None):
        raise ValueError("Provide both comparison dates or leave both empty.")

    comparison_start = comparison_end = None
    if comparison_start_date is not None and comparison_end_date is not None:
        comparison_start, comparison_end = parse_period(
            comparison_start_date, comparison_end_date
        )

    playlist_ids = validate_playlist_ids(selected_playlist_ids)
    provider = YouTubeDataProvider(build_youtube_client())
    data = fetch_engagement_data(provider, playlist_ids)
    return analyze_engagement_data(
        data, start, end, comparison_start, comparison_end
    )


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
