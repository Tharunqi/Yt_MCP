import pytest

from youtube_mcp.engagement.metrics import summarize_durations


def test_summarize_durations_returns_statistics_and_distribution() -> None:
    result = summarize_durations([60, 300, 900, 1800, 3600])

    assert result.count == 5
    assert result.total_seconds == 6660
    assert result.average_seconds == 1332
    assert result.median_seconds == 900
    assert result.distribution == {
        "under_5_minutes": 1,
        "5_to_under_15_minutes": 1,
        "15_to_under_30_minutes": 1,
        "30_to_under_60_minutes": 1,
        "60_minutes_or_more": 1,
    }


def test_summarize_empty_durations() -> None:
    result = summarize_durations([])

    assert result.count == 0
    assert result.total_seconds == 0
    assert result.average_seconds is None
    assert result.median_seconds is None
    assert sum(result.distribution.values()) == 0


def test_summarize_durations_rejects_negative_values() -> None:
    with pytest.raises(ValueError, match="zero or greater"):
        summarize_durations([60, -1])
