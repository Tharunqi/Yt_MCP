from datetime import date

import pytest

from youtube_mcp.engagement.analysis import (
    EngagementData,
    analyze_engagement_data,
    analyze_period,
    fetch_engagement_data,
    parse_period,
    validate_playlist_ids,
)
from youtube_mcp.providers.youtube import (
    PlaylistItemDetails,
    SubscriptionDetails,
    VideoDetails,
)


def sample_data() -> EngagementData:
    videos = {
        "v1": VideoDetails("v1", date(2026, 1, 2), "c1", "Alpha", "1", 120),
        "v2": VideoDetails("v2", date(2026, 1, 10), "c2", "Beta", "2", 900),
        "v3": VideoDetails("v3", date(2025, 12, 20), "c1", "Alpha", "1", 1800),
    }
    return EngagementData(
        liked_video_ids=("v1", "v2"),
        subscriptions=(
            SubscriptionDetails("c1", "Alpha", date(2026, 1, 2)),
            SubscriptionDetails("c2", "Beta", date(2026, 1, 8)),
        ),
        playlist_items=(
            PlaylistItemDetails("PL123456789", "v3", date(2026, 1, 3)),
            PlaylistItemDetails("PL123456789", "v2", date(2026, 1, 5)),
            PlaylistItemDetails("PL123456789", "v1", date(2026, 1, 9)),
        ),
        videos=videos,
        category_names={"1": "Film & Animation", "2": "Education"},
    )


def test_fetch_engagement_data_uses_provider_and_selected_playlists() -> None:
    class FakeProvider:
        def list_liked_video_ids(self):
            return ["video_00001"]

        def list_subscriptions(self):
            return [SubscriptionDetails("channel_001", "Channel", date(2026, 1, 2))]

        def list_playlist_items(self, playlist_id):
            assert playlist_id == "PL123456789"
            return [PlaylistItemDetails(playlist_id, "video_00002", date(2026, 1, 3))]

        def get_videos(self, video_ids):
            assert video_ids == ["video_00001", "video_00002"]
            return {
                "video_00001": VideoDetails(
                    "video_00001", date(2026, 1, 1), "channel_001", "Channel", "22", 90
                ),
                "video_00002": VideoDetails(
                    "video_00002", date(2026, 1, 2), "channel_002", "Second", "23", 120
                ),
            }

        def get_category_names(self, category_ids):
            assert category_ids == ["22", "23"]
            return {"22": "People & Blogs", "23": "Comedy"}

    data = fetch_engagement_data(FakeProvider(), ["PL123456789"])

    assert data.liked_video_ids == ("video_00001",)
    assert len(data.subscriptions) == 1
    assert len(data.playlist_items) == 1
    assert data.category_names["23"] == "Comedy"


def test_analysis_filters_range_and_returns_all_fr4_metrics() -> None:
    result = analyze_period(sample_data(), date(2026, 1, 1), date(2026, 1, 7))

    assert result["date_range"] == {"start": "2026-01-01", "end": "2026-01-07"}
    assert result["video_count"] == 3
    assert result["top_channels"] == [
        {"channel_id": "c1", "channel_title": "Alpha", "video_count": 2},
        {"channel_id": "c2", "channel_title": "Beta", "video_count": 1},
    ]
    assert result["top_categories"] == [
        {"category_id": "1", "category_name": "Film & Animation", "video_count": 2},
        {"category_id": "2", "category_name": "Education", "video_count": 1},
    ]
    assert result["duration_statistics"] == {
        "count": 3,
        "missing_duration_count": 0,
        "total_seconds": 2820,
        "average_seconds": 940,
        "median_seconds": 900,
        "distribution": {
            "under_5_minutes": 1,
            "5_to_under_15_minutes": 0,
            "15_to_under_30_minutes": 1,
            "30_to_under_60_minutes": 1,
            "60_minutes_or_more": 0,
        },
    }
    assert result["time_trends"] == {
        "subscriptions_created_by_week": [
            {"week_start": "2025-12-29", "count": 1}
        ],
        "playlist_items_added_by_week": [
            {"week_start": "2025-12-29", "count": 1},
            {"week_start": "2026-01-05", "count": 1},
        ],
    }
    assert result["sources"]


def test_comparison_uses_same_metrics_and_discloses_date_limits() -> None:
    result = analyze_engagement_data(
        sample_data(), date(2026, 1, 1), date(2026, 1, 7),
        date(2026, 1, 8), date(2026, 1, 12),
    )

    metrics = (
        "top_channels",
        "top_categories",
        "duration_statistics",
        "time_trends",
        "sources",
    )
    for metric in metrics:
        assert metric in result["analysis_period"]
        assert metric in result["comparison_period"]
    assert (
        result["analysis_period"]["duration_statistics"]
        != result["comparison_period"]["duration_statistics"]
    )
    assert result["comparison_period"]["date_range"] == {
        "start": "2026-01-08",
        "end": "2026-01-12",
    }
    assert result["comparison_summary"]["video_count_change"] == 1
    assert result["comparison_summary"]["duration_changes"]["count"] == 1
    assert any("publish date" in note for note in result["data_notes"])
    assert any("not watch time" in note for note in result["data_notes"])
    assert any("not saved" in note for note in result["data_notes"])


def test_unknown_category_is_returned_without_guessing_a_name() -> None:
    data = sample_data()
    video = data.videos["v1"]
    data.videos["v1"] = VideoDetails(
        video.video_id, video.published_at, video.channel_id,
        video.channel_title, "missing-category", video.duration_seconds,
    )

    result = analyze_period(data, date(2026, 1, 1), date(2026, 1, 3))

    unknown = next(
        category
        for category in result["top_categories"]
        if category["category_id"] == "missing-category"
    )
    assert unknown["category_name"] is None


def test_date_range_validation() -> None:
    assert parse_period("2026-01-01", "2026-01-31") == (
        date(2026, 1, 1), date(2026, 1, 31)
    )
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        parse_period("not-a-date", "2026-01-31")
    with pytest.raises(ValueError, match="on or before"):
        parse_period("2026-02-01", "2026-01-31")


def test_playlist_ids_are_checked_and_deduplicated() -> None:
    assert validate_playlist_ids(["PL123456789", "PL123456789"]) == ["PL123456789"]
    with pytest.raises(ValueError, match="Playlist IDs"):
        validate_playlist_ids([""])


def test_playlist_selection_is_bounded() -> None:
    ids = [f"playlist_{index}" for index in range(6)]

    with pytest.raises(ValueError, match="no more than 5"):
        validate_playlist_ids(ids)
