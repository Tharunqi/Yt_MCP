"""Opt-in smoke tests against public YouTube Data API resources.

Run explicitly with:
    RUN_YOUTUBE_LIVE_TESTS=1 python -m pytest tests/live -q
"""

import os
from collections.abc import Callable
from typing import TypeVar

import pytest

from youtube_mcp.common.config import Settings
from youtube_mcp.providers.youtube import ChannelMetadata, VideoMetadata, YouTubeProvider

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_YOUTUBE_LIVE_TESTS") != "1",
    reason="Set RUN_YOUTUBE_LIVE_TESTS=1 to make live YouTube API requests.",
)

# Stable public video used only for low-cost metadata read smoke tests.
VIDEO_ID = os.getenv("YOUTUBE_LIVE_VIDEO_ID", "dQw4w9WgXcQ")
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
    config = Settings(max_search_results=3, max_upload_sample=3)
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
