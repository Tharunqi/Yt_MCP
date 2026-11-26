import pytest

from youtube_mcp.playlists.planner import (
    build_playlist_plan,
    preview_result,
    validate_request,
)
from youtube_mcp.providers.youtube import SearchVideo, VideoDetails


def make_request():
    return validate_request(
        "math lessons",
        20,
        10,
        "English",
        "Math for the bus ride",
        "unlisted",
    )


def test_planner_selects_only_videos_that_fit_all_limits() -> None:
    candidates = [
        SearchVideo("video_00001", "One", "Alpha"),
        SearchVideo("video_00002", "Two", "Beta"),
        SearchVideo("video_00003", "Does not fit", "Gamma"),
        SearchVideo("video_00004", "Unknown duration", "Delta"),
        SearchVideo("video_00005", "Unknown language", "Epsilon"),
        SearchVideo("video_00006", "Too long", "Zeta"),
        SearchVideo("video_00007", "Wrong language", "Eta"),
        SearchVideo("video_00008", "Unavailable", "Theta"),
        SearchVideo("video_00001", "Duplicate", "Alpha"),
    ]
    videos = {
        "video_00001": VideoDetails(
            "video_00001", None, "channel_01", "Alpha", None, 600, "One", "en"
        ),
        "video_00002": VideoDetails(
            "video_00002", None, "channel_02", "Beta", None, 600, "Two", "en-US"
        ),
        "video_00003": VideoDetails(
            "video_00003", None, "channel_03", "Gamma", None, 60, "Does not fit", "en"
        ),
        "video_00004": VideoDetails(
            "video_00004", None, "channel_04", "Delta", None, None, "Unknown duration", "en"
        ),
        "video_00005": VideoDetails(
            "video_00005", None, "channel_05", "Epsilon", None, 300, "Unknown language"
        ),
        "video_00006": VideoDetails(
            "video_00006", None, "channel_06", "Zeta", None, 720, "Too long", "en"
        ),
        "video_00007": VideoDetails(
            "video_00007", None, "channel_07", "Eta", None, 300, "Wrong language", "es"
        ),
    }

    plan = build_playlist_plan(make_request(), candidates, videos)

    assert [item["video_id"] for item in plan.items] == [
        "video_00001",
        "video_00002",
    ]
    assert plan.total_duration_seconds == 1200
    reasons = {item["video_id"]: item["reason"] for item in plan.excluded_items}
    assert "remaining duration" in reasons["video_00003"]
    assert "Duration is unknown" in reasons["video_00004"]
    assert "Language is unknown" in reasons["video_00005"]
    assert "maximum" in reasons["video_00006"]
    assert "does not match" in reasons["video_00007"]
    assert "unavailable" in reasons["video_00008"]
    assert "Duplicate" in reasons["video_00001"]


def test_preview_shows_title_items_duration_and_visibility() -> None:
    plan = build_playlist_plan(
        make_request(),
        [SearchVideo("video_00001", "One", "Alpha")],
        {
            "video_00001": VideoDetails(
                "video_00001", None, "channel_01", "Alpha", None, 600, "One", "en"
            )
        },
    )

    result = preview_result(plan, "one-time-preview")

    assert result["preview_id"] == "one-time-preview"
    assert result["playlist_title"] == "Math for the bus ride"
    assert result["visibility"] == "unlisted"
    assert result["planned_duration_seconds"] == 600
    assert result["planned_duration"] == "10m"
    assert result["remaining_duration"] == "10m"
    assert result["remaining_duration_seconds"] == 600
    assert result["items"][0]["channel"] == "Alpha"
    assert result["items"][0]["url"].endswith("video_00001")
    assert result["items"][0]["selection_reason"]
    assert result["can_create"] is True


def test_request_rejects_invalid_title_duration_and_visibility() -> None:
    with pytest.raises(ValueError, match="positive number"):
        validate_request("topic", 0, None, None, "title", "private")
    with pytest.raises(ValueError, match="title"):
        validate_request("topic", 10, None, None, "  ", "private")
    with pytest.raises(ValueError, match="Visibility"):
        validate_request("topic", 10, None, None, "title", "friends")
