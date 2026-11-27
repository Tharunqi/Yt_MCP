from __future__ import annotations

import pytest

from youtube_mcp.common.errors import InvalidIdentifierError
from youtube_mcp.providers.youtube import VideoMetadata
from youtube_mcp.quota.preflight import QuotaEstimate
from youtube_mcp.quota.usage import record_api_call
from youtube_mcp.summarization.metadata_summary import (
    format_duration,
    summarize_video_metadata,
)


def video_metadata(**overrides: object) -> VideoMetadata:
    values: dict[str, object] = {
        "video_id": "abcdefghijk",
        "title": "A metadata example",
        "description": "A description from the video metadata.",
        "channel_id": "channel123",
        "channel_title": "Example channel",
        "published_at": "2026-01-02T03:04:05Z",
        "tags": (),
        "category_id": "27",
        "duration": "PT1H2M3S",
        "default_language": "en",
    }
    values.update(overrides)
    return VideoMetadata(**values)  # type: ignore[arg-type]


class FakeProvider:
    def __init__(self, video: VideoMetadata) -> None:
        self.video = video
        self.calls: list[str] = []

    def get_video(self, video_id_or_url: str) -> VideoMetadata:
        self.calls.append(video_id_or_url)
        record_api_call("standard")
        return self.video

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


def test_summary_returns_available_metadata_and_metadata_only_notice() -> None:
    provider = FakeProvider(video_metadata())
    quota = FakeQuotaPreflight()

    result = summarize_video_metadata(
        "https://youtu.be/abcdefghijk", provider, quota_preflight=quota
    )

    assert result["summary_type"] == "metadata-based"
    assert "does not summarize spoken content" in str(result["notice"])
    details = result["video"]
    assert isinstance(details, dict)
    assert details["video_id"] == "abcdefghijk"
    assert details["title"] == "A metadata example"
    assert details["channel"] == {
        "channel_id": "channel123",
        "title": "Example channel",
    }
    assert details["description"] == "A description from the video metadata."
    assert details["category"] == {"id": "27", "name": "Education"}
    assert details["published_at"] == "2026-01-02T03:04:05Z"
    assert details["duration"] == "1h 2m 3s"
    assert provider.calls == ["abcdefghijk"]
    assert quota.estimates == [QuotaEstimate(2, 0)]
    assert quota.reservation.actual == [QuotaEstimate(2, 0)]


def test_summary_keeps_missing_metadata_explicit() -> None:
    provider = FakeProvider(
        video_metadata(
            title="",
            description="",
            channel_id="",
            channel_title="",
            published_at=None,
            category_id=None,
            duration=None,
        )
    )

    quota = FakeQuotaPreflight()
    result = summarize_video_metadata(
        "abcdefghijk", provider, quota_preflight=quota
    )

    details = result["video"]
    assert isinstance(details, dict)
    assert details["title"] is None
    assert details["description"] is None
    assert details["category"] is None
    assert details["published_at"] is None
    assert details["duration"] is None
    assert details["duration_iso8601"] is None
    assert details["channel"] == {"channel_id": None, "title": None}
    assert quota.reservation.actual == [QuotaEstimate(1, 0)]


def test_invalid_identifier_is_rejected_before_quota_or_provider_call() -> None:
    provider = FakeProvider(video_metadata())
    quota = FakeQuotaPreflight()

    with pytest.raises(InvalidIdentifierError):
        summarize_video_metadata("short-id", provider, quota_preflight=quota)

    assert quota.estimates == []
    assert provider.calls == []


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("PT0S", "0s"), ("P1DT2H", "1d 2h"), ("not-a-duration", None)],
)
def test_format_duration(raw: str, expected: str | None) -> None:
    assert format_duration(raw) == expected
