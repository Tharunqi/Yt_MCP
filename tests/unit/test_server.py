import pytest

import youtube_mcp.server as server
from youtube_mcp.engagement.analysis import EngagementData
from youtube_mcp.quota.preflight import QuotaEstimate


class FakeReservation:
    def __init__(self):
        self.actual = None

    def settle(self, actual):
        self.actual = actual


class FakeQuotaGate:
    def __init__(self):
        self.estimates = []
        self.reservations = []

    def check_and_reserve(self, estimate):
        self.estimates.append(estimate)
        reservation = FakeReservation()
        self.reservations.append(reservation)
        return reservation


def test_analyze_engagement_tool_returns_period_and_comparison(monkeypatch) -> None:
    data = EngagementData((), (), (), {}, {})
    quota_gate = FakeQuotaGate()
    monkeypatch.setattr(server, "_feature_quota_preflight", quota_gate)
    captured: dict[str, object] = {}

    monkeypatch.setattr(server, "build_youtube_client", lambda: "fake-client")
    monkeypatch.setattr(
        server,
        "fetch_engagement_data",
        lambda provider, playlist_ids: captured.update(
            provider=provider, playlist_ids=playlist_ids
        ) or data,
    )

    result = server.analyze_engagement(
        "2026-01-01", "2026-01-31", ["PL123456789"],
        "2025-12-01", "2025-12-31",
    )

    assert quota_gate.estimates == [QuotaEstimate(101, 0)]
    assert quota_gate.reservations[0].actual == QuotaEstimate(0, 0)
    assert captured["playlist_ids"] == ["PL123456789"]
    assert captured["provider"]._client == "fake-client"
    assert result["analysis_period"]["date_range"] == {
        "start": "2026-01-01", "end": "2026-01-31"
    }
    assert result["comparison_period"]["date_range"] == {
        "start": "2025-12-01", "end": "2025-12-31"
    }


def test_tool_requires_both_comparison_dates(monkeypatch) -> None:
    monkeypatch.setattr(server, "build_youtube_client", lambda: "unused")
    monkeypatch.setattr(server, "_feature_quota_preflight", FakeQuotaGate())

    with pytest.raises(ValueError, match="both comparison dates"):
        server.analyze_engagement("2026-01-01", "2026-01-31", comparison_start_date="2025-01-01")


def test_server_keeps_analysis_request_scoped() -> None:
    assert not hasattr(server, "capture_engagement_snapshot")
    assert not hasattr(server, "get_latest_engagement_snapshot")


def test_engagement_rejects_quota_before_fetching_data(monkeypatch) -> None:
    class RejectingQuotaGate:
        def check_and_reserve(self, estimate):
            raise RuntimeError("quota rejected")

    monkeypatch.setattr(server, "_feature_quota_preflight", RejectingQuotaGate())
    monkeypatch.setattr(server, "build_youtube_client", lambda: "unused")
    monkeypatch.setattr(
        server,
        "fetch_engagement_data",
        lambda *args: pytest.fail("provider data must not be fetched"),
    )

    with pytest.raises(RuntimeError, match="quota rejected"):
        server.analyze_engagement("2026-01-01", "2026-01-31")
