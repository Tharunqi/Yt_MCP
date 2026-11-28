from __future__ import annotations

from datetime import date

import pytest

from youtube_mcp.common.errors import ResourceNotFoundError
from youtube_mcp.providers.youtube import (
    ChannelMetadata,
    PlaylistItemDetails,
    SubscriptionDetails,
    VideoMetadata,
)
from youtube_mcp.quota.preflight import QuotaEstimate
from youtube_mcp.quota.usage import record_api_call
from youtube_mcp.recommendations.service import recommend_personalized_videos


def video(
    video_id: str,
    *,
    title: str,
    channel_id: str,
    published_at: str | None = "2026-11-20T00:00:00Z",
) -> VideoMetadata:
    return VideoMetadata(
        video_id=video_id,
        title=title,
        description="",
        channel_id=channel_id,
        channel_title=channel_id,
        published_at=published_at,
        tags=(),
        category_id=None,
        duration=None,
        default_language=None,
    )


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


class FakeAccount:
    def __init__(self) -> None:
        self.liked_calls = 0
        self.subscription_limits: list[int | None] = []
        self.playlist_calls: list[tuple[str, int | None]] = []

    def list_liked_video_ids(self) -> list[str]:
        self.liked_calls += 1
        record_api_call("standard")
        return ["liked-video"]

    def list_subscriptions(
        self, *, max_results: int | None = None
    ) -> list[SubscriptionDetails]:
        self.subscription_limits.append(max_results)
        record_api_call("standard")
        return [
            SubscriptionDetails(f"channel-{index}", f"Channel {index}", None)
            for index in range(7)
        ]

    def list_playlist_items(
        self, playlist_id: str, *, max_results: int | None = None
    ) -> list[PlaylistItemDetails]:
        self.playlist_calls.append((playlist_id, max_results))
        record_api_call("standard")
        return [PlaylistItemDetails(playlist_id, "saved-video", date(2026, 1, 1))]


class FakeMetadata:
    def __init__(self) -> None:
        self.video_fetches: list[list[str]] = []
        self.search_calls: list[tuple[str, int | None]] = []
        self.channel_calls: list[str] = []
        self.upload_calls: list[tuple[str, int | None]] = []

    def get_videos(self, video_ids: list[str]) -> list[VideoMetadata]:
        self.video_fetches.append(video_ids)
        record_api_call("standard")
        return [
            video(video_id, title="Python data science", channel_id="liked-creator")
            for video_id in video_ids
        ]

    def search_videos(
        self, query: str, *, max_results: int | None = None
    ) -> list[VideoMetadata]:
        self.search_calls.append((query, max_results))
        record_api_call("search")
        record_api_call("standard")
        return [
            video("liked-video", title="Python course", channel_id="topic-channel"),
            video("saved-video", title="Python project", channel_id="topic-channel"),
            video("topic-video", title="Python data science guide", channel_id="topic-channel"),
        ]

    def get_channel(self, identifier: str) -> ChannelMetadata:
        self.channel_calls.append(identifier)
        record_api_call("standard")
        if identifier == "channel-2":
            raise ResourceNotFoundError("missing")
        return ChannelMetadata(identifier, identifier, "", None, f"uploads-{identifier}")

    def list_channel_uploads(
        self, channel: ChannelMetadata, *, max_results: int | None = None
    ) -> list[VideoMetadata]:
        self.upload_calls.append((channel.channel_id, max_results))
        record_api_call("standard")
        record_api_call("standard")
        return [
            video("topic-video", title="Python data science guide", channel_id=channel.channel_id),
            video(
                f"upload-{channel.channel_id}",
                title="Python tutorial",
                channel_id=channel.channel_id,
            ),
        ]


def test_service_aggregates_bounded_signals_excludes_interactions_and_settles_usage() -> None:
    account = FakeAccount()
    metadata = FakeMetadata()
    quota = FakeQuota()

    result = recommend_personalized_videos(
        "  Python tutorials  ",
        ["playlist-1", "playlist-1"],
        account,
        metadata,
        quota_preflight=quota,
        max_results=5,
    )

    assert result["status"] == "ok"
    assert result["topic"] == "Python tutorials"
    assert result["sources"] == {
        "liked_video_count": 1,
        "saved_video_count": 1,
        "subscription_count": 7,
        "selected_playlist_count": 1,
        "sampled_subscription_channels": 4,
        "topic_candidate_limit": 25,
        "uploads_per_sampled_channel": 5,
    }
    assert {item["video_id"] for item in result["results"]} == {
        "topic-video",
        "upload-channel-0",
        "upload-channel-1",
        "upload-channel-3",
    }
    assert account.liked_calls == 1
    assert account.subscription_limits == [50]
    assert account.playlist_calls == [("playlist-1", 50)]
    assert metadata.video_fetches == [["liked-video", "saved-video"]]
    assert metadata.search_calls == [("Python tutorials", 25)]
    assert metadata.channel_calls == [
        "channel-0",
        "channel-1",
        "channel-2",
        "channel-3",
        "channel-4",
    ]
    assert metadata.upload_calls == [
        ("channel-0", 5),
        ("channel-1", 5),
        ("channel-3", 5),
        ("channel-4", 5),
    ]
    assert quota.estimates == [QuotaEstimate(59, 1)]
    assert quota.reservation.settlements == [QuotaEstimate(19, 1)]
    assert "liked-video" not in {item["video_id"] for item in result["results"]}
    assert "saved-video" not in {item["video_id"] for item in result["results"]}
    assert all(item["reasons"] for item in result["results"])


def test_preflight_rejects_before_any_account_or_metadata_call() -> None:
    account = FakeAccount()
    metadata = FakeMetadata()

    class RejectingQuota:
        def check_and_reserve(self, estimate: QuotaEstimate) -> FakeReservation:
            raise RuntimeError("quota unavailable")

    with pytest.raises(RuntimeError, match="quota unavailable"):
        recommend_personalized_videos(
            "Python", None, account, metadata, quota_preflight=RejectingQuota()
        )

    assert account.liked_calls == 0
    assert account.subscription_limits == []
    assert metadata.search_calls == []


def test_invalid_request_fails_before_quota_or_provider_access() -> None:
    account = FakeAccount()
    metadata = FakeMetadata()
    quota = FakeQuota()

    with pytest.raises(ValueError, match="At most 3"):
        recommend_personalized_videos(
            "Python",
            ["PL1", "PL2", "PL3", "PL4"],
            account,
            metadata,
            quota_preflight=quota,
        )

    assert quota.estimates == []
    assert account.liked_calls == 0
    assert metadata.search_calls == []


def test_provider_failure_settles_attempted_usage_before_reraising() -> None:
    account = FakeAccount()
    metadata = FakeMetadata()
    quota = FakeQuota()

    def fail_search(query: str, *, max_results: int | None = None) -> list[VideoMetadata]:
        record_api_call("search")
        raise RuntimeError("provider unavailable")

    metadata.search_videos = fail_search  # type: ignore[method-assign]

    with pytest.raises(RuntimeError, match="provider unavailable"):
        recommend_personalized_videos(
            "Python",
            None,
            account,
            metadata,
            quota_preflight=quota,
            include_subscription_uploads=False,
        )

    assert quota.reservation.settlements == [QuotaEstimate(3, 1)]
