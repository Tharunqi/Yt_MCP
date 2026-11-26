from googleapiclient.errors import HttpError

import youtube_mcp.server as server
from youtube_mcp.auth.youtube import (
    YOUTUBE_PLAYLIST_WRITE_SCOPE,
    YOUTUBE_READ_ONLY_SCOPE,
)
from youtube_mcp.playlists.previews import PlaylistPreviewStore
from youtube_mcp.providers.youtube import SearchVideo, VideoDetails


class FakeResponse:
    status = 400
    reason = "Bad Request"


class FakeProvider:
    def __init__(self, client):
        self.client = client
        self.added = []

    def search_videos(self, topic, language_code):
        return [SearchVideo("video_00001", "Lesson 1", "Teacher")]

    def get_videos(self, video_ids):
        return {
            "video_00001": VideoDetails(
                "video_00001", None, "channel_01", "Teacher", None, 600,
                "Lesson 1", "en",
            )
        }

    def get_my_channel_id(self):
        return "channel_01"

    def create_playlist(self, title, visibility):
        self.client["playlist"] = (title, visibility)
        return "playlist_01"

    def add_video_to_playlist(self, playlist_id, video_id):
        if video_id == getattr(self, "fail_video", None):
            raise HttpError(FakeResponse(), b'{"error":{"errors":[{"reason":"videoNotFound"}]}}')
        self.added.append(video_id)


def prepare(monkeypatch):
    store = PlaylistPreviewStore()
    monkeypatch.setattr(server, "playlist_previews", store)
    providers = []

    def provider_factory(client):
        provider = FakeProvider(client)
        providers.append(provider)
        return provider

    monkeypatch.setattr(server, "YouTubeDataProvider", provider_factory)
    preview = server.preview_playlist("math", 20, "Math lessons", "private")
    return preview, providers


def test_preview_does_not_request_write_access_or_create_playlist(monkeypatch):
    client = {"writes": 0}
    monkeypatch.setattr(server, "build_youtube_client", lambda **kwargs: client)

    preview, providers = prepare(monkeypatch)

    assert preview["status"] == "preview"
    assert preview["items"][0]["title"] == "Lesson 1"
    assert preview["visibility"] == "private"
    assert providers[0].client is client
    assert "playlist" not in client


def test_playlist_is_created_only_after_confirmation(monkeypatch):
    client = {}
    scope_requests = []
    monkeypatch.setattr(
        server,
        "build_youtube_client",
        lambda scopes=None: scope_requests.append(scopes) or client,
    )
    preview, providers = prepare(monkeypatch)

    pending = server.create_playlist_from_preview(preview["preview_id"], False)
    assert pending["status"] == "confirmation_required"
    assert scope_requests == [None]
    assert "playlist" not in client

    result = server.create_playlist_from_preview(preview["preview_id"], True)

    assert scope_requests == [
        None,
        [YOUTUBE_READ_ONLY_SCOPE, YOUTUBE_PLAYLIST_WRITE_SCOPE],
    ]
    assert client["playlist"] == ("Math lessons", "private")
    assert providers[-1].added == ["video_00001"]
    assert result["status"] == "completed"
    assert result["playlist_url"].endswith("playlist_01")
    assert result["added_video_ids"] == ["video_00001"]
    assert result["failed_items"] == []


def test_partial_playlist_failure_lists_items_that_were_not_added(monkeypatch):
    client = {}
    monkeypatch.setattr(server, "build_youtube_client", lambda scopes=None: client)
    preview, providers = prepare(monkeypatch)
    monkeypatch.setattr(FakeProvider, "fail_video", "video_00001", raising=False)

    result = server.create_playlist_from_preview(preview["preview_id"], True)

    assert result["status"] == "partial"
    assert result["playlist_created"] is True
    assert result["added_video_ids"] == []
    assert result["failed_items"] == [
        {"video_id": "video_00001", "message": "YouTube rejected this video."}
    ]


def test_missing_youtube_channel_stops_before_playlist_creation(monkeypatch):
    class NoChannelProvider(FakeProvider):
        def get_my_channel_id(self):
            return None

    monkeypatch.setattr(server, "playlist_previews", PlaylistPreviewStore())
    monkeypatch.setattr(server, "build_youtube_client", lambda scopes=None: {})
    monkeypatch.setattr(server, "YouTubeDataProvider", NoChannelProvider)
    preview = server.preview_playlist("math", 20, "Math lessons", "private")

    result = server.create_playlist_from_preview(preview["preview_id"], True)

    assert result["status"] == "needs_youtube_channel"
    assert result["playlist_created"] is False
