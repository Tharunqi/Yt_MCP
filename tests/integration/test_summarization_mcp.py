from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp.server.fastmcp.exceptions import ToolError

from youtube_mcp.providers.youtube import VideoMetadata
from youtube_mcp.quota.preflight import QuotaEstimate
from youtube_mcp.quota.usage import record_api_call
from youtube_mcp.server import create_mcp_server


class FakeProvider:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def get_video(self, video_id_or_url: str) -> VideoMetadata:
        self.calls.append(video_id_or_url)
        record_api_call("standard")
        return VideoMetadata(
            video_id="abcdefghijk",
            title="Metadata summary test",
            description="A public video description.",
            channel_id="channel123",
            channel_title="Example channel",
            published_at="2026-01-02T03:04:05Z",
            tags=(),
            category_id="27",
            duration="PT4M10S",
            default_language="en",
        )

    def get_video_category_name(self, category_id: str) -> str | None:
        record_api_call("standard")
        return "Education" if category_id == "27" else None


class FakeReservation:
    def __init__(self) -> None:
        self.actual: list[QuotaEstimate] = []

    def settle(self, actual: QuotaEstimate) -> None:
        self.actual.append(actual)


class FakeQuotaPreflight:
    def __init__(self) -> None:
        self.estimates: list[QuotaEstimate] = []
        self.reservation = FakeReservation()

    def check_and_reserve(self, estimate: QuotaEstimate) -> FakeReservation:
        self.estimates.append(estimate)
        return self.reservation


def test_summarize_video_metadata_is_registered_and_returns_summary() -> None:
    provider = FakeProvider()
    quota = FakeQuotaPreflight()
    server = create_mcp_server(provider, quota)

    tools = asyncio.run(server.list_tools())
    content, structured = asyncio.run(
        server.call_tool(
            "summarize_video_metadata",
            {"video_url_or_id": "abcdefghijk"},
        )
    )

    assert "summarize_video_metadata" in {tool.name for tool in tools}
    payload: dict[str, Any] = json.loads(content[0].text)
    assert structured["summary_type"] == "metadata-based"
    assert payload["video"]["title"] == "Metadata summary test"
    assert payload["video"]["category"] == {"id": "27", "name": "Education"}
    assert payload["video"]["duration"] == "4m 10s"
    assert "does not summarize spoken content" in payload["notice"]
    assert provider.calls == ["abcdefghijk"]
    assert quota.estimates == [QuotaEstimate(2, 0)]
    assert quota.reservation.actual == [QuotaEstimate(2, 0)]


def test_summary_tool_fails_closed_without_quota_tracking() -> None:
    provider = FakeProvider()
    server = create_mcp_server(provider)

    try:
        asyncio.run(
            server.call_tool(
                "summarize_video_metadata",
                {"video_url_or_id": "abcdefghijk"},
            )
        )
    except ToolError as exc:
        assert "quota tracking is not configured" in str(exc)
    else:
        raise AssertionError("summary tool should require quota tracking")

    assert provider.calls == []
