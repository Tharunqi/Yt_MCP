from datetime import date

import pytest

from youtube_mcp.analytics.playlist_analysis import analyze_playlist, validate_playlist_id
from youtube_mcp.providers.youtube import PlaylistItemDetails, VideoDetails


class FakeProvider:
    def __init__(self):
        self.items = [
            PlaylistItemDetails("PL123456789", "v1", None),
            PlaylistItemDetails("PL123456789", "v1", None),
            PlaylistItemDetails("PL123456789", "v2", None),
            PlaylistItemDetails("PL123456789", "v3", None),
        ]
        self.video_ids = None
        self.category_ids = None

    def list_playlist_items(self, playlist_id):
        assert playlist_id == "PL123456789"
        return self.items

    def get_videos(self, video_ids):
        self.video_ids = video_ids
        return {
            "v1": VideoDetails("v1", date(2020, 1, 2), "c1", "Alpha", "22", 60, "One"),
            "v2": VideoDetails("v2", date(2021, 2, 3), "c2", "Beta", "23", None, "Two"),
        }

    def get_category_names(self, category_ids):
        self.category_ids = category_ids
        return {"22": "People & Blogs", "23": "Comedy"}


def test_playlist_analysis_counts_playlist_items_and_reports_missing_metadata():
    provider = FakeProvider()

    result = analyze_playlist("PL123456789", provider)

    assert result["analysis_type"] == "descriptive_metadata"
    assert result["item_count"] == 4
    assert result["unique_video_count"] == 3
    assert provider.video_ids == ["v1", "v2", "v3"]
    assert provider.category_ids == ["22", "23"]
    assert result["total_duration_seconds"] == 120
    assert result["duration_count"] == 2
    assert result["unknown_channel_count"] == 1
    assert result["unknown_category_count"] == 1
    assert result["duration_complete"] is False
    assert result["missing_duration_count"] == 2
    assert result["unavailable_item_count"] == 1
    assert result["duration_distribution"]["under_5_minutes"] == 2
    assert result["channel_counts"] == [
        {"channel_id": "c1", "channel_title": "Alpha", "item_count": 2},
        {"channel_id": "c2", "channel_title": "Beta", "item_count": 1},
    ]
    assert result["category_counts"][0] == {
        "category_id": "22", "category_name": "People & Blogs", "item_count": 2
    }
    assert result["items"][0]["title"] == "One"
    assert result["items"][-1]["metadata_available"] is False
    assert any("metadata only" in note for note in result["data_notes"])
    assert any("not saved" in note for note in result["data_notes"])


def test_empty_playlist_returns_zero_metrics():
    provider = FakeProvider()
    provider.items = []

    result = analyze_playlist("PL123456789", provider)

    assert result["item_count"] == 0
    assert result["total_duration_seconds"] == 0
    assert result["duration_complete"] is True
    assert result["items"] == []


@pytest.mark.parametrize(
    "playlist_id", ["", "invalid id", "https://youtube.com/playlist?list=x", "x" * 129]
)
def test_playlist_id_validation(playlist_id):
    with pytest.raises(ValueError, match="Playlist ID"):
        validate_playlist_id(playlist_id)
