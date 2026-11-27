from __future__ import annotations

from typing import Any

import pytest

from youtube_mcp.common.config import Settings
from youtube_mcp.common.errors import InvalidIdentifierError, ResourceNotFoundError
from youtube_mcp.common.identifiers import parse_channel_identifier, parse_video_id
from youtube_mcp.providers.youtube import ChannelMetadata, YouTubeProvider


class FakeRequest:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.kwargs: dict[str, Any] | None = None

    def list(self, **kwargs: Any) -> FakeRequest:
        self.kwargs = kwargs
        return self

    def execute(self) -> dict[str, Any]:
        return self.response


class FakeResource:
    def __init__(self, responses: dict[str, dict[str, Any]]) -> None:
        self.responses = responses
        self.requests: dict[str, FakeRequest] = {}
        self.resource_kind = ""

    def _request(self, name: str) -> FakeRequest:
        request = FakeRequest(self.responses.get(name, {"items": []}))
        self.requests[name] = request
        return request

    def videos(self) -> FakeResource:
        self.resource_kind = "videos"
        return self

    def channels(self) -> FakeResource:
        self.resource_kind = "channels"
        return self

    def search(self) -> FakeResource:
        self.resource_kind = "search"
        return self

    def playlistItems(self) -> FakeResource:
        self.resource_kind = "playlist_items"
        return self

    def list(self, **kwargs: Any) -> FakeRequest:
        if "id" in kwargs and kwargs.get("part") == "snippet,contentDetails":
            if self.resource_kind == "videos":
                kind = "videos_by_id"
            elif "," in kwargs["id"]:
                kind = "channels_by_id"
            else:
                kind = "channel_lookup"
        elif kwargs.get("type") == "video":
            kind = "search_videos"
        elif kwargs.get("type") == "channel":
            kind = "search_channels"
        elif "playlistId" in kwargs:
            kind = "uploads"
        elif "forHandle" in kwargs or "forUsername" in kwargs:
            kind = "channel_lookup"
        elif kwargs.get("part") == "snippet,contentDetails":
            kind = "channel_lookup"
        else:
            kind = "unknown"
        request = self._request(kind)
        request.kwargs = kwargs
        return request


def settings() -> Settings:
    return Settings(api_key=None, max_search_results=12, max_upload_sample=8)


def test_parse_video_id_from_supported_urls() -> None:
    video_id = "abcdefghijk"
    assert parse_video_id(video_id) == video_id
    assert parse_video_id(f"https://www.youtube.com/watch?v={video_id}") == video_id
    assert parse_video_id(f"https://youtu.be/{video_id}") == video_id
    assert parse_video_id(f"https://youtube.com/shorts/{video_id}") == video_id


def test_parse_video_id_rejects_malformed_inputs() -> None:
    with pytest.raises(InvalidIdentifierError):
        parse_video_id("https://example.com/watch?v=abcdefghijk")
    with pytest.raises(InvalidIdentifierError):
        parse_video_id("too-short")


def test_parse_channel_identifiers() -> None:
    channel_id = "UC" + "a" * 22
    assert parse_channel_identifier(channel_id) == ("channel_id", channel_id)
    assert parse_channel_identifier("@example_handle") == ("handle", "@example_handle")
    assert parse_channel_identifier("https://youtube.com/user/example") == (
        "username",
        "example",
    )


def test_get_video_fetches_metadata() -> None:
    client = FakeResource(
        {
            "videos_by_id": {
                "items": [
                    {
                        "id": "abcdefghijk",
                        "snippet": {
                            "title": "A video",
                            "description": "Description",
                            "channelId": "UC" + "b" * 22,
                            "channelTitle": "A channel",
                            "publishedAt": "2025-01-01T00:00:00Z",
                            "tags": ["one", "two"],
                            "categoryId": "10",
                            "defaultLanguage": "en",
                        },
                        "contentDetails": {"duration": "PT5M"},
                    }
                ]
            }
        }
    )
    provider = YouTubeProvider(client=client, config=settings())

    video = provider.get_video("https://youtu.be/abcdefghijk")

    assert video.video_id == "abcdefghijk"
    assert video.tags == ("one", "two")
    assert video.duration == "PT5M"
    assert client.requests["videos_by_id"].kwargs == {
        "part": "snippet,contentDetails",
        "id": "abcdefghijk",
    }


def test_get_video_raises_for_unavailable_resource() -> None:
    provider = YouTubeProvider(client=FakeResource({}), config=settings())
    with pytest.raises(ResourceNotFoundError):
        provider.get_video("abcdefghijk")


def test_search_videos_caps_requested_candidate_count() -> None:
    client = FakeResource(
        {
            "search_videos": {
                "items": [{"id": {"videoId": "abcdefghijk"}}],
            },
            "videos_by_id": {"items": []},
        }
    )
    provider = YouTubeProvider(client=client, config=settings())

    provider.search_videos("cooking", max_results=50)

    assert client.requests["search_videos"].kwargs["maxResults"] == 12


def test_get_channel_resolves_handle_without_at_prefix() -> None:
    client = FakeResource(
        {
            "channel_lookup": {
                "items": [
                    {
                        "id": "UC" + "a" * 22,
                        "snippet": {"title": "A channel", "description": "About"},
                        "contentDetails": {"relatedPlaylists": {"uploads": "UU" + "a" * 22}},
                    }
                ]
            }
        }
    )
    provider = YouTubeProvider(client=client, config=settings())

    channel = provider.get_channel("@example_handle")

    assert channel.title == "A channel"
    assert channel.uploads_playlist_id == "UU" + "a" * 22
    assert client.requests["channel_lookup"].kwargs["forHandle"] == "example_handle"


def test_recent_uploads_uses_bounded_sample_and_returns_details() -> None:
    client = FakeResource(
        {
            "channel_lookup": {
                "items": [
                    {
                        "id": "UC" + "a" * 22,
                        "snippet": {"title": "A channel"},
                        "contentDetails": {"relatedPlaylists": {"uploads": "UU" + "a" * 22}},
                    }
                ]
            },
            "uploads": {"items": [{"contentDetails": {"videoId": "abcdefghijk"}}]},
            "videos_by_id": {"items": [{"id": "abcdefghijk", "snippet": {"title": "Upload"}}]},
        }
    )
    provider = YouTubeProvider(client=client, config=settings())

    uploads = provider.list_recent_uploads("UC" + "a" * 22, max_results=50)

    assert len(uploads) == 1
    assert uploads[0].title == "Upload"
    assert client.requests["uploads"].kwargs["maxResults"] == 8


def test_list_channel_uploads_uses_resolved_channel_without_lookup() -> None:
    client = FakeResource(
        {
            "uploads": {"items": [{"contentDetails": {"videoId": "abcdefghijk"}}]},
            "videos_by_id": {
                "items": [{"id": "abcdefghijk", "snippet": {"title": "Upload"}}]
            },
        }
    )
    provider = YouTubeProvider(client=client, config=settings())
    resolved = ChannelMetadata(
        "UC" + "a" * 22,
        "A channel",
        "About",
        None,
        "UU" + "a" * 22,
    )

    uploads = provider.list_channel_uploads(resolved, max_results=3)

    assert uploads[0].title == "Upload"
    assert client.requests["uploads"].kwargs["maxResults"] == 3
    assert "channel_lookup" not in client.requests
