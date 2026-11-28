from datetime import date

import pytest

from youtube_mcp.analytics.playlist_analysis import analyze_video, validate_video_identifier
from youtube_mcp.common.errors import InvalidIdentifierError
from youtube_mcp.providers.youtube import VideoDetails


class FakeProvider:
    def get_videos(self, video_ids):
        assert video_ids == ["b8u2CQLQBVU"]
        return {
            "b8u2CQLQBVU": VideoDetails(
                "b8u2CQLQBVU", date(2025, 12, 3), "channel_01", "Channel", "27", 1071, "Lecture"
            )
        }

    def get_category_names(self, category_ids):
        assert category_ids == ["27"]
        return {"27": "Education"}


def test_video_analysis_returns_metadata_counts_and_duration():
    result = analyze_video("https://youtu.be/b8u2CQLQBVU", FakeProvider())

    assert result["analysis_type"] == "descriptive_metadata"
    assert result["source_type"] == "video"
    assert result["video_id"] == "b8u2CQLQBVU"
    assert result["total_duration_seconds"] == 1071
    assert result["duration_count"] == 1
    assert result["duration_distribution"]["15_to_under_30_minutes"] == 1
    assert result["channel_counts"][0]["item_count"] == 1
    assert result["category_counts"][0]["category_name"] == "Education"
    assert result["items"][0]["title"] == "Lecture"


def test_video_input_is_validated_before_provider_call():
    with pytest.raises(InvalidIdentifierError):
        validate_video_identifier("not a video")
