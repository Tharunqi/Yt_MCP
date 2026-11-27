"""Opt-in smoke tests against public YouTube Data API resources.

Run explicitly with:
    RUN_YOUTUBE_LIVE_TESTS=1 python -m pytest tests/live -q
"""

import asyncio
import os
from collections.abc import Callable
from typing import TypeVar

import pytest
from sqlalchemy import create_engine

from youtube_mcp.common.config import Settings
from youtube_mcp.providers.youtube import ChannelMetadata, VideoMetadata, YouTubeProvider
from youtube_mcp.quota.ledger import SQLAlchemyQuotaLedger
from youtube_mcp.server import create_mcp_server

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.getenv("RUN_YOUTUBE_LIVE_TESTS") != "1",
        reason="Set RUN_YOUTUBE_LIVE_TESTS=1 to make live YouTube API requests.",
    ),
]

# FR-1 uses a video seed; FR-2 uses an independent channel URL seed.
VIDEO_ID = os.getenv("YOUTUBE_LIVE_VIDEO_ID", "vVVIWEGciKk")
CHANNEL_IDENTIFIER = os.getenv(
    "YOUTUBE_LIVE_CHANNEL_IDENTIFIER", "https://www.youtube.com/@gameranxTV"
)
Result = TypeVar("Result")


def _safe_call(label: str, operation: Callable[[], Result]) -> Result:
    """Keep HTTP client exceptions from printing URLs that contain the API key."""
    try:
        return operation()
    except Exception as exc:
        pytest.fail(
            f"{label} failed ({type(exc).__name__}); request details suppressed.",
            pytrace=False,
        )


@pytest.fixture(scope="module")
def provider() -> YouTubeProvider:
    config = Settings()
    if not config.api_key:
        pytest.skip("Set YOUTUBE_API_KEY in .env to run live YouTube API tests.")
    return YouTubeProvider(config=config)


@pytest.fixture(scope="module")
def live_video(provider: YouTubeProvider) -> VideoMetadata:
    return _safe_call("Video details request", lambda: provider.get_video(VIDEO_ID))


@pytest.fixture(scope="module")
def live_channel(provider: YouTubeProvider, live_video: VideoMetadata) -> ChannelMetadata:
    return _safe_call(
        "Channel details request", lambda: provider.get_channel(live_video.channel_id)
    )


def test_live_video_details_return_public_metadata(live_video: VideoMetadata) -> None:
    assert live_video.video_id == VIDEO_ID
    assert live_video.title
    assert live_video.channel_id
    assert live_video.channel_title


def test_live_channel_details_return_public_metadata(live_channel: ChannelMetadata) -> None:
    assert live_channel.channel_id
    assert live_channel.title
    assert live_channel.uploads_playlist_id


def test_live_recent_uploads_are_bounded_and_have_metadata(
    provider: YouTubeProvider, live_channel: ChannelMetadata
) -> None:
    uploads = _safe_call(
        "Recent uploads request",
        lambda: provider.list_recent_uploads(live_channel.channel_id, max_results=3),
    )

    assert len(uploads) <= 3
    assert all(upload.video_id and upload.title for upload in uploads)


def test_live_channel_search_returns_public_metadata(provider: YouTubeProvider) -> None:
    channels = _safe_call(
        "Channel search request",
        lambda: provider.search_channels("python programming", max_results=2),
    )

    assert len(channels) <= 2
    assert all(channel.channel_id and channel.title for channel in channels)


def test_live_mcp_discovery_returns_video_and_channel_matches(
    provider: YouTubeProvider, live_video: VideoMetadata
) -> None:
    """Exercise FR-1 with a video and FR-2 with a separate channel URL seed."""
    engine = create_engine("sqlite:///:memory:")
    config = Settings()
    ledger = SQLAlchemyQuotaLedger(
        engine,
        standard_daily_limit=config.default_quota_daily_limit,
        search_daily_limit=config.search_quota_daily_limit,
    )
    server = create_mcp_server(provider, ledger)

    try:
        video_result = _safe_call(
            "Similar-video MCP request",
            lambda: asyncio.run(
                server.call_tool(
                    "find_similar_videos",
                    {"video_url_or_id": VIDEO_ID, "max_results": 10},
                )
            ),
        )
        _, similar_videos = video_result
        assert similar_videos["seed"]["video_id"] == VIDEO_ID
        assert 1 <= len(similar_videos["search_queries"]) <= 3
        assert similar_videos["results"], "FR-1 returned no similar videos for the seed."
        assert len(similar_videos["results"]) <= 10
        print(f"Similar videos returned ({len(similar_videos['results'])}):")
        for video in similar_videos["results"]:
            print(f"  {video['score']:.4f} {video['title']} — {video['url']}")

        channel_result = _safe_call(
            "Similar-channel MCP request",
            lambda: asyncio.run(
                server.call_tool(
                    "find_similar_channels",
                    {
                        "channel_url_handle_or_id": CHANNEL_IDENTIFIER,
                        "max_results": 10,
                    },
                )
            ),
        )
        _, similar_channels = channel_result
        assert similar_channels["seed"]["channel_id"]
        assert 1 <= len(similar_channels["search_queries"]) <= 3
        print(f"FR-2 search queries from the channel profile: {similar_channels['search_queries']}")
        print(
            f"Similar channels returned for {similar_channels['seed']['title']} "
            f"({len(similar_channels['results'])}):"
        )
        for channel in similar_channels["results"]:
            print(f"  {channel['score']:.4f} {channel['title']} — {channel['url']}")
        assert similar_channels["results"], (
            f"FR-2 returned no similar channels for {similar_channels['seed']['title']}; "
            f"queries={similar_channels['search_queries']}"
        )
        assert len(similar_channels["results"]) <= 10
        assert all(
            channel["channel_id"] != live_video.channel_id
            for channel in similar_channels["results"]
        )
    finally:
        engine.dispose()
