from __future__ import annotations

import asyncio
import json

from google.auth.exceptions import GoogleAuthError
from mcp.server.fastmcp.exceptions import ToolError
import pytest

import youtube_mcp.server as server_module
from youtube_mcp.providers.youtube import (
    ChannelMetadata,
    PlaylistItemDetails,
    SubscriptionDetails,
    VideoMetadata,
)
from youtube_mcp.quota.preflight import QuotaEstimate
from youtube_mcp.quota.usage import record_api_call


class FakeReservation:
    def __init__(self) -> None:
        self.settlements: list[QuotaEstimate] = []

    def settle(self, actual: QuotaEstimate) -> None:
        self.settlements.append(actual)


class FakeQuota:
    def __init__(self) -> None:
        self.estimates: list[QuotaEstimate] = []
        self.reservation = FakeReservation()

    def check_and_reserve(self, estimate: QuotaEstimate) -> FakeReservation:
        self.estimates.append(estimate)
        return self.reservation


class FakeAccountProvider:
    def list_liked_video_ids(self) -> list[str]:
        record_api_call("standard")
        return ["liked-video"]

    def list_subscriptions(
        self, *, max_results: int | None = None
    ) -> list[SubscriptionDetails]:
        assert max_results == 50
        record_api_call("standard")
        return [SubscriptionDetails("creator", "Creator", None)]

    def list_playlist_items(
        self, playlist_id: str, *, max_results: int | None = None
    ) -> list[PlaylistItemDetails]:
        assert playlist_id == "PL123"
        assert max_results == 50
        record_api_call("standard")
        return [PlaylistItemDetails(playlist_id, "saved-video", None)]


class FakeMetadataProvider:
    def get_videos(self, video_ids: list[str]) -> list[VideoMetadata]:
        record_api_call("standard")
        return [
            VideoMetadata(
                video_id,
                "Python programming",
                "",
                "liked-creator",
                "Liked creator",
                None,
                (),
                None,
                None,
                None,
            )
            for video_id in video_ids
        ]

    def search_videos(
        self, query: str, *, max_results: int | None = None
    ) -> list[VideoMetadata]:
        assert query == "Python"
        assert max_results == 25
        record_api_call("search")
        record_api_call("standard")
        return [
            VideoMetadata(
                "candidate-video",
                "Python programming guide",
                "",
                "candidate-creator",
                "Candidate creator",
                None,
                (),
                None,
                None,
                None,
            )
        ]

    def get_channel(self, identifier: str) -> ChannelMetadata:
        raise AssertionError("subscription uploads were disabled")

    def list_channel_uploads(
        self, channel: ChannelMetadata, *, max_results: int | None = None
    ) -> list[VideoMetadata]:
        raise AssertionError("subscription uploads were disabled")


def test_recommendation_tool_is_registered_and_returns_explained_results(monkeypatch) -> None:
    quota = FakeQuota()
    monkeypatch.setattr(server_module, "build_youtube_client", lambda *, scopes: "client")
    monkeypatch.setattr(server_module, "YouTubeDataProvider", lambda client: FakeAccountProvider())
    monkeypatch.setattr(server_module, "YouTubeProvider", lambda client: FakeMetadataProvider())
    server = server_module.create_mcp_server(quota_preflight=quota)

    tools = asyncio.run(server.list_tools())
    content, structured = asyncio.run(
        server.call_tool(
            "recommend_videos",
            {
                "topic": "Python",
                "selected_playlist_ids": ["PL123"],
                "include_subscription_uploads": False,
                "max_results": 4,
            },
        )
    )

    payload = json.loads(content[0].text)
    assert "recommend_videos" in {tool.name for tool in tools}
    assert payload["status"] == "ok"
    assert payload["result_count"] == 1
    assert payload["results"][0]["video_id"] == "candidate-video"
    assert payload["results"][0]["reasons"]
    assert structured["results"][0]["video_id"] == "candidate-video"
    assert quota.estimates == [QuotaEstimate(43, 1)]
    assert quota.reservation.settlements == [QuotaEstimate(6, 1)]


def test_recommendation_tool_reports_missing_authorization_without_fetching(monkeypatch) -> None:
    quota = FakeQuota()
    monkeypatch.setattr(
        server_module,
        "build_youtube_client",
        lambda **kwargs: (_ for _ in ()).throw(GoogleAuthError("denied")),
    )
    server = server_module.create_mcp_server(quota_preflight=quota)

    content, structured = asyncio.run(
        server.call_tool("recommend_videos", {"topic": "Python"})
    )

    payload = json.loads(content[0].text)
    assert payload["status"] == "authorization_required"
    assert payload["results"] == []
    assert structured["status"] == "authorization_required"
    assert quota.reservation.settlements == [QuotaEstimate(0, 0)]


def test_recommendation_tool_quota_failure_happens_before_oauth(monkeypatch) -> None:
    def fail_oauth(**kwargs):
        raise AssertionError("OAuth must not run before quota preflight")

    monkeypatch.setattr(server_module, "build_youtube_client", fail_oauth)

    class RejectingQuota:
        def check_and_reserve(self, estimate: QuotaEstimate) -> FakeReservation:
            raise RuntimeError("quota unavailable")

    server = server_module.create_mcp_server(quota_preflight=RejectingQuota())
    with pytest.raises(ToolError, match="quota unavailable"):
        asyncio.run(server.call_tool("recommend_videos", {"topic": "Python"}))
