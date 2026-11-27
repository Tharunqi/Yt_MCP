import pytest

import youtube_mcp.server as server
from youtube_mcp.providers.youtube import PlaylistItemDetails, VideoDetails
from youtube_mcp.quota.preflight import QuotaEstimate


class FakeReservation:
    def __init__(self):
        self.actual = None

    def settle(self, actual):
        self.actual = actual


class FakeQuotaGate:
    def __init__(self, reject=False):
        self.estimates = []
        self.reservations = []
        self.reject = reject

    def check_and_reserve(self, estimate):
        self.estimates.append(estimate)
        if self.reject:
            raise RuntimeError("quota rejected")
        reservation = FakeReservation()
        self.reservations.append(reservation)
        return reservation


class FakeProvider:
    def __init__(self, client):
        self.client = client

    def list_playlist_items(self, playlist_id):
        return [PlaylistItemDetails(playlist_id, "video_00001", None)]

    def get_videos(self, video_ids):
        return {"video_00001": VideoDetails(
            "video_00001", None, "channel_01", "Channel", "22", 90, "Video"
        )}

    def get_category_names(self, category_ids):
        return {"22": "People & Blogs"}


def test_analyze_playlist_reserves_quota_and_returns_metadata(monkeypatch):
    gate = FakeQuotaGate()
    monkeypatch.setattr(server, "_feature_quota_preflight", gate)
    monkeypatch.setattr(server, "build_youtube_client", lambda: "client")
    monkeypatch.setattr(server, "YouTubeDataProvider", FakeProvider)

    result = server.analyze_playlist("PL123456789")

    assert gate.estimates == [QuotaEstimate(41, 0)]
    assert gate.reservations[0].actual == QuotaEstimate(0, 0)
    assert result["item_count"] == 1
    assert result["total_duration_seconds"] == 90


def test_invalid_playlist_id_is_rejected_before_quota_or_auth(monkeypatch):
    gate = FakeQuotaGate()
    monkeypatch.setattr(server, "_feature_quota_preflight", gate)
    monkeypatch.setattr(
        server, "build_youtube_client", lambda: pytest.fail("must not authenticate")
    )

    with pytest.raises(ValueError, match="Playlist ID"):
        server.analyze_playlist("not a playlist")

    assert gate.estimates == []


def test_quota_rejection_happens_before_auth_or_provider(monkeypatch):
    gate = FakeQuotaGate(reject=True)
    monkeypatch.setattr(server, "_feature_quota_preflight", gate)
    monkeypatch.setattr(
        server, "build_youtube_client", lambda: pytest.fail("must not authenticate")
    )

    with pytest.raises(RuntimeError, match="quota rejected"):
        server.analyze_playlist("PL123456789")
