import pytest

from youtube_mcp.quota.preflight import (
    QuotaEstimate,
    estimate_engagement_quota,
    estimate_playlist_analysis_quota,
    estimate_playlist_creation_quota,
    estimate_playlist_preview_quota,
    estimate_video_analysis_quota,
)


def test_engagement_estimate_covers_the_fetch_caps() -> None:
    assert estimate_engagement_quota(max_playlists=0) == QuotaEstimate(61, 0)
    assert estimate_engagement_quota(max_playlists=5) == QuotaEstimate(261, 0)
    with pytest.raises(ValueError, match="between 0 and 5"):
        estimate_engagement_quota(max_playlists=6)


def test_playlist_preview_estimate_uses_separate_search_bucket() -> None:
    assert estimate_playlist_preview_quota() == QuotaEstimate(1, 1)


def test_playlist_creation_estimate_counts_each_write() -> None:
    assert estimate_playlist_creation_quota(1) == QuotaEstimate(101, 0)
    assert estimate_playlist_creation_quota(50) == QuotaEstimate(2551, 0)
    with pytest.raises(ValueError, match="positive"):
        estimate_playlist_creation_quota(0)


def test_playlist_analysis_estimate_covers_bounded_reads() -> None:
    assert estimate_playlist_analysis_quota() == QuotaEstimate(41, 0)


def test_video_analysis_estimate_covers_video_and_category_reads() -> None:
    assert estimate_video_analysis_quota() == QuotaEstimate(2, 0)
