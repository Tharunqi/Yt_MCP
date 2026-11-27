from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from youtube_mcp.providers.youtube import ChannelMetadata, VideoMetadata
from youtube_mcp.quota.preflight import QuotaEstimate
from youtube_mcp.quota.usage import record_api_call
from youtube_mcp.server import create_mcp_server


class FakeVideoProvider:
    def __init__(self) -> None:
        self.seed = VideoMetadata(
            video_id="abcdefghijk",
            title="Python async tutorial",
            description="Learn asynchronous Python",
            channel_id="seed-channel",
            channel_title="Seed channel",
            published_at=None,
            tags=("python", "asyncio"),
            category_id="27",
            duration="PT5M",
            default_language="en",
        )
        self.candidate = VideoMetadata(
            video_id="lmnopqrstuv",
            title="Python async guide",
            description="Asynchronous Python examples",
            channel_id="candidate-channel",
            channel_title="Candidate channel",
            published_at=None,
            tags=("python", "asyncio"),
            category_id="27",
            duration="PT8M",
            default_language="en",
        )
        self.get_video_calls: list[str] = []
        self.search_calls: list[tuple[str, int | None]] = []

    def get_video(self, video_id_or_url: str) -> VideoMetadata:
        record_api_call("standard")
        self.get_video_calls.append(video_id_or_url)
        return self.seed

    def search_videos(self, query: str, *, max_results: int | None = None) -> list[VideoMetadata]:
        record_api_call("search")
        record_api_call("standard")
        self.search_calls.append((query, max_results))
        return [self.candidate]


class FakeQuotaReservation:
    def __init__(self) -> None:
        self.settlements: list[QuotaEstimate] = []

    def settle(self, actual: QuotaEstimate) -> None:
        self.settlements.append(actual)


class FakeQuotaPreflight:
    def __init__(self) -> None:
        self.estimates: list[QuotaEstimate] = []
        self.reservation = FakeQuotaReservation()

    def check_and_reserve(self, estimate: QuotaEstimate) -> FakeQuotaReservation:
        self.estimates.append(estimate)
        return self.reservation


def test_find_similar_videos_tool_returns_ranked_results() -> None:
    provider = FakeVideoProvider()
    quota_preflight = FakeQuotaPreflight()
    server = create_mcp_server(provider, quota_preflight)

    tools = asyncio.run(server.list_tools())
    result = asyncio.run(
        server.call_tool(
            "find_similar_videos",
            {"video_url_or_id": "abcdefghijk", "max_results": 5},
        )
    )

    assert "find_similar_videos" in {tool.name for tool in tools}
    assert provider.get_video_calls == ["abcdefghijk"]
    assert provider.search_calls
    assert quota_preflight.estimates == [QuotaEstimate(4, 3)]
    assert quota_preflight.reservation.settlements == [QuotaEstimate(4, 3)]
    content, structured = result
    assert len(content) == 1
    payload: dict[str, Any] = json.loads(content[0].text)
    assert structured["seed"]["video_id"] == "abcdefghijk"
    assert payload["seed"]["video_id"] == "abcdefghijk"
    assert payload["results"][0]["video_id"] == "lmnopqrstuv"
    assert payload["results"][0]["url"] == "https://www.youtube.com/watch?v=lmnopqrstuv"
    assert payload["results"][0]["reasons"]


def test_default_mcp_server_fails_closed_without_quota_ledger() -> None:
    provider = FakeVideoProvider()
    server = create_mcp_server(provider)

    with pytest.raises(ToolError, match="quota tracking is not configured"):
        asyncio.run(
            server.call_tool(
                "find_similar_videos",
                {"video_url_or_id": "abcdefghijk"},
            )
        )

    assert provider.get_video_calls == []
    assert provider.search_calls == []


def test_find_similar_channels_tool_returns_ranked_results() -> None:
    seed_id = "UC" + "a" * 22
    candidate_id = "UC" + "b" * 22

    class FakeChannelProvider:
        def get_channel(self, identifier: str) -> ChannelMetadata:
            assert identifier == "@python_seed"
            record_api_call("standard")
            return ChannelMetadata(
                seed_id, "Python Learning", "Python tutorials", None, "UU" + "a" * 22
            )

        def list_channel_uploads(
            self, channel: ChannelMetadata, *, max_results: int | None = None
        ) -> list[VideoMetadata]:
            record_api_call("standard")
            record_api_call("standard")
            video_id = "abcdefghijk" if channel.channel_id == seed_id else "lmnopqrstuv"
            title = (
                "Python async tutorial"
                if channel.channel_id == seed_id
                else "Python async guide"
            )
            return [
                VideoMetadata(
                    video_id=video_id,
                    title=title,
                    description="Python asynchronous programming",
                    channel_id=channel.channel_id,
                    channel_title=channel.title,
                    published_at=None,
                    tags=("python", "async"),
                    category_id="27",
                    duration="PT5M",
                    default_language="en",
                )
            ][:max_results]

        def search_channels(
            self, query: str, *, max_results: int | None = None
        ) -> list[ChannelMetadata]:
            record_api_call("search")
            record_api_call("standard")
            return [
                ChannelMetadata(
                    candidate_id,
                    "Python Academy",
                    "Python tutorials",
                    None,
                    "UU" + "b" * 22,
                )
            ]

    provider = FakeChannelProvider()
    quota_preflight = FakeQuotaPreflight()
    server = create_mcp_server(provider, quota_preflight)
    tools = asyncio.run(server.list_tools())

    result = asyncio.run(
        server.call_tool(
            "find_similar_channels",
            {"channel_url_handle_or_id": "@python_seed", "max_results": 4},
        )
    )

    assert "find_similar_channels" in {tool.name for tool in tools}
    content, structured = result
    payload: dict[str, Any] = json.loads(content[0].text)
    assert structured["seed"]["channel_id"] == seed_id
    assert payload["results"][0]["channel_id"] == candidate_id
    assert payload["results"][0]["url"] == f"https://www.youtube.com/channel/{candidate_id}"
    assert payload["results"][0]["reasons"]
