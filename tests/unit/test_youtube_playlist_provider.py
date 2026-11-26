from typing import Any

from youtube_mcp.providers.youtube import SearchVideo, YouTubeDataProvider


class FakeRequest:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response

    def execute(self) -> dict[str, Any]:
        return self.response


class FakeResource:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def list(self, **params: Any) -> FakeRequest:
        self.calls.append(params)
        return FakeRequest(self.response)

    def insert(self, **params: Any) -> FakeRequest:
        self.calls.append(params)
        return FakeRequest(self.response)


class FakeYouTube:
    def __init__(self) -> None:
        self.search_resource = FakeResource({
            "items": [{
                "id": {"videoId": "video_00001"},
                "snippet": {"title": "Algebra", "channelTitle": "Math"},
            }]
        })
        self.video_resource = FakeResource({
            "items": [{
                "id": "video_00001",
                "snippet": {
                    "title": "Algebra",
                    "channelTitle": "Math",
                    "defaultLanguage": "en",
                },
                "contentDetails": {"duration": "PT10M"},
            }]
        })
        self.channel_resource = FakeResource({"items": [{"id": "channel_01"}]})
        self.playlist_resource = FakeResource({"id": "playlist_01"})
        self.item_resource = FakeResource({"id": "item_01"})

    def search(self) -> FakeResource:
        return self.search_resource

    def videos(self) -> FakeResource:
        return self.video_resource

    def channels(self) -> FakeResource:
        return self.channel_resource

    def playlists(self) -> FakeResource:
        return self.playlist_resource

    def playlistItems(self) -> FakeResource:
        return self.item_resource


def test_provider_searches_checks_channel_and_sends_write_bodies() -> None:
    client = FakeYouTube()
    provider = YouTubeDataProvider(client)

    results = provider.search_videos("algebra", "en")
    videos = provider.get_videos(["video_00001"])
    channel_id = provider.get_my_channel_id()
    playlist_id = provider.create_playlist("Math lessons", "private")
    provider.add_video_to_playlist(playlist_id, "video_00001")

    assert results == [SearchVideo("video_00001", "Algebra", "Math")]
    assert videos["video_00001"].duration_seconds == 600
    assert videos["video_00001"].language_code == "en"
    assert channel_id == "channel_01"
    assert playlist_id == "playlist_01"
    assert client.search_resource.calls == [{
        "part": "snippet",
        "q": "algebra",
        "type": "video",
        "maxResults": 50,
        "order": "relevance",
        "relevanceLanguage": "en",
    }]
    assert client.playlist_resource.calls[0]["body"] == {
        "snippet": {"title": "Math lessons"},
        "status": {"privacyStatus": "private"},
    }
    assert client.item_resource.calls[0]["body"]["snippet"]["resourceId"] == {
        "kind": "youtube#video",
        "videoId": "video_00001",
    }
