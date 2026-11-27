from collections import deque
from typing import Any

from youtube_mcp.providers.youtube import YouTubeDataProvider


class FakeRequest:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response

    def execute(self) -> dict[str, Any]:
        return self.response


class FakeResource:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = deque(responses)
        self.calls: list[dict[str, Any]] = []

    def list(self, **kwargs: Any) -> FakeRequest:
        self.calls.append(kwargs)
        return FakeRequest(self.responses.popleft())


class FakeVideos:
    def __init__(self, likes: list[dict[str, Any]], details: list[dict[str, Any]]) -> None:
        self.likes = FakeResource(likes)
        self.details = FakeResource(details)

    def list(self, **kwargs: Any) -> FakeRequest:
        resource = self.likes if kwargs.get("myRating") == "like" else self.details
        return resource.list(**kwargs)


class FakeClient:
    def __init__(self) -> None:
        self.video_resource = FakeVideos(
            [
                {
                    "items": [{"id": "video_00001"}],
                    "nextPageToken": "next",
                },
                {"items": [{"id": "video_00002"}]},
            ],
            [
                {
                    "items": [
                        {
                            "id": "video_00001",
                            "snippet": {
                                "publishedAt": "2026-01-02T10:00:00Z",
                                "channelId": "channel_001",
                                "channelTitle": "Channel",
                                "categoryId": "22",
                            },
                            "contentDetails": {"duration": "PT1M30S"},
                        }
                    ]
                },
                {"items": []},
            ],
        )
        self.subscription_resource = FakeResource(
            [
                {
                    "items": [
                        {
                            "snippet": {
                                "publishedAt": "2026-01-03T10:00:00Z",
                                "title": "Channel",
                                "resourceId": {"channelId": "channel_001"},
                            }
                        }
                    ],
                    "nextPageToken": "next",
                },
                {"items": []},
            ]
        )
        self.playlist_resource = FakeResource(
            [
                {
                    "items": [
                        {
                            "snippet": {
                                "publishedAt": "2026-01-04T10:00:00Z",
                                "resourceId": {"videoId": "video_00001"},
                            },
                            "contentDetails": {"videoId": "video_00001"},
                        }
                    ],
                    "nextPageToken": "next",
                },
                {"items": []},
            ]
        )
        self.category_resource = FakeResource(
            [{"items": [{"id": "22", "snippet": {"title": "People & Blogs"}}]}]
        )

    def videos(self) -> FakeVideos:
        return self.video_resource

    def subscriptions(self) -> FakeResource:
        return self.subscription_resource

    def playlistItems(self) -> FakeResource:
        return self.playlist_resource

    def videoCategories(self) -> FakeResource:
        return self.category_resource


def test_provider_reads_likes_subscriptions_playlists_and_categories() -> None:
    client = FakeClient()
    provider = YouTubeDataProvider(client)

    assert provider.list_liked_video_ids() == ["video_00001", "video_00002"]
    subscriptions = provider.list_subscriptions()
    items = provider.list_playlist_items("PL123456789")
    videos = provider.get_videos(["video_00001"])
    categories = provider.get_category_names(["22"])

    assert subscriptions[0].channel_id == "channel_001"
    assert subscriptions[0].created_at.isoformat() == "2026-01-03"
    assert items[0].added_at.isoformat() == "2026-01-04"
    assert videos["video_00001"].duration_seconds == 90
    assert videos["video_00001"].category_id == "22"
    assert categories == {"22": "People & Blogs"}
    assert client.video_resource.likes.calls[0]["maxResults"] == 50
    assert client.subscription_resource.calls[1]["pageToken"] == "next"
    assert client.playlist_resource.calls[1]["pageToken"] == "next"


def test_provider_batches_video_requests_at_50_ids() -> None:
    client = FakeClient()
    ids = [f"video_{index:05d}" for index in range(51)]

    YouTubeDataProvider(client).get_videos(ids)

    assert [len(call["id"].split(",")) for call in client.video_resource.details.calls] == [50, 1]


def test_subscription_read_stops_at_1000_items() -> None:
    pages = [
        {
            "items": [
                {"snippet": {"title": f"Channel {index}", "resourceId": {"channelId": str(index)}}}
                for index in range(50)
            ],
            "nextPageToken": f"page-{page + 1}",
        }
        for page in range(21)
    ]
    client = FakeClient()
    client.subscription_resource = FakeResource(pages)

    subscriptions = YouTubeDataProvider(client).list_subscriptions()

    assert len(subscriptions) == 1000
    assert len(client.subscription_resource.calls) == 20


def test_subscription_read_stops_after_20_pages_even_with_sparse_pages() -> None:
    pages = [
        {
            "items": [
                {"snippet": {"title": "Channel", "resourceId": {"channelId": str(page)}}}
            ],
            "nextPageToken": f"page-{page + 1}",
        }
        for page in range(21)
    ]
    client = FakeClient()
    client.subscription_resource = FakeResource(pages)

    subscriptions = YouTubeDataProvider(client).list_subscriptions()

    assert len(subscriptions) == 20
    assert len(client.subscription_resource.calls) == 20
