"""MCP server and tool registration for YouTube video discovery."""

import os
from typing import Any

from mcp.server.fastmcp import FastMCP
from sqlalchemy import Engine

from youtube_mcp.common.config import settings
from youtube_mcp.database.engine import create_database_engine
from youtube_mcp.discovery.similar_videos import (
    SimilarVideoProvider,
)
from youtube_mcp.discovery.similar_videos import (
    find_similar_videos as discover_similar_videos,
)
from youtube_mcp.providers.youtube import YouTubeProvider
from youtube_mcp.quota.ledger import SQLAlchemyQuotaLedger
from youtube_mcp.quota.preflight import (
    QuotaPreflight,
    UnavailableQuotaPreflight,
)


def _configured_quota_preflight(database_url: str | None) -> QuotaPreflight:
    """Build a PostgreSQL quota ledger when the app has a database URL."""
    if not database_url:
        return UnavailableQuotaPreflight()
    engine: Engine = create_database_engine(database_url)
    return SQLAlchemyQuotaLedger(
        engine,
        standard_daily_limit=settings.default_quota_daily_limit,
        search_daily_limit=settings.search_quota_daily_limit,
    )


def create_mcp_server(
    provider: SimilarVideoProvider | None = None,
    quota_preflight: QuotaPreflight | None = None,
) -> FastMCP:
    """Build a server with injected API and quota dependencies.

    The default quota dependency fails closed. Callers must provide a working
    preflight implementation before the similar-videos tool can access YouTube.
    """
    server = FastMCP(
        "youtube-video-intelligence",
        host="0.0.0.0",
        port=int(os.getenv("MCP_PORT", "8000")),
    )
    video_provider = provider or YouTubeProvider()
    quota_gate = quota_preflight or _configured_quota_preflight(os.getenv("DATABASE_URL"))

    @server.tool()
    def health_check() -> str:
        """Check whether the YouTube MCP server is running."""
        return "YouTube Video Intelligence MCP Server is running."

    @server.tool()
    def find_similar_videos(video_url_or_id: str, max_results: int = 10) -> dict[str, Any]:
        """Find public videos similar to a seed using metadata-based ranking.

        Returns a bounded ranked candidate list with links and short reasons.
        The result describes best matches in the searched candidate pool, not a
        guarantee of globally similar videos.
        """
        if not 1 <= max_results <= 25:
            raise ValueError("max_results must be between 1 and 25")

        result = discover_similar_videos(
            video_url_or_id,
            video_provider,
            quota_preflight=quota_gate,
            candidate_limit=25,
            result_limit=max_results,
            max_queries=3,
        )
        return {
            "seed": {
                "video_id": result.seed.video_id,
                "title": result.seed.title,
                "channel_title": result.seed.channel_title,
                "url": f"https://www.youtube.com/watch?v={result.seed.video_id}",
            },
            "search_queries": list(result.search_queries),
            "results": [
                {
                    "video_id": ranked.video.video_id,
                    "title": ranked.video.title,
                    "channel_title": ranked.video.channel_title,
                    "duration": ranked.video.duration,
                    "score": ranked.score,
                    "reasons": list(ranked.reasons),
                    "url": ranked.url,
                }
                for ranked in result.videos
            ],
        }

    return server


mcp = create_mcp_server()


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
