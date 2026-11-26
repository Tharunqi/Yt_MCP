import json
import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from googleapiclient.errors import HttpError

_PAGE_SIZE = 50
_MAX_LIKED_VIDEOS = 1000
_DURATION_PATTERN = re.compile(
    r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?"
)


@dataclass(frozen=True)
class VideoDetails:
    video_id: str
    published_at: date | None
    channel_id: str | None
    channel_title: str | None
    category_id: str | None
    duration_seconds: int | None
    title: str | None = None
    language_code: str | None = None


@dataclass(frozen=True)
class SearchVideo:
    video_id: str
    title: str | None
    channel_title: str | None


@dataclass(frozen=True)
class SubscriptionDetails:
    channel_id: str | None
    channel_title: str | None
    created_at: date | None


@dataclass(frozen=True)
class PlaylistItemDetails:
    playlist_id: str
    video_id: str
    added_at: date | None


def _api_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _duration_seconds(value: str | None) -> int | None:
    if not value:
        return None
    match = _DURATION_PATTERN.fullmatch(value)
    if match is None or not any(match.groups()) or value.endswith("T"):
        return None
    days, hours, minutes, seconds = (int(part or 0) for part in match.groups())
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def _pages(resource: Any, **params: object) -> Iterator[dict[str, Any]]:
    page_token = None
    while True:
        request = dict(params)
        if page_token:
            request["pageToken"] = page_token
        response = resource.list(**request).execute()
        yield response
        page_token = response.get("nextPageToken")
        if not page_token:
            return


class YouTubeDataProvider:
    """Keep YouTube Data API calls behind one small provider boundary."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def list_liked_video_ids(self) -> list[str]:
        video_ids: list[str] = []
        for response in _pages(
            self._client.videos(),
            part="id,snippet,contentDetails",
            myRating="like",
            maxResults=_PAGE_SIZE,
        ):
            for item in response.get("items", []):
                video_id = item.get("id")
                if isinstance(video_id, str) and video_id:
                    video_ids.append(video_id)
                    if len(video_ids) >= _MAX_LIKED_VIDEOS:
                        return video_ids
        return video_ids

    def list_subscriptions(self) -> list[SubscriptionDetails]:
        subscriptions: list[SubscriptionDetails] = []
        for response in _pages(
            self._client.subscriptions(),
            part="snippet",
            mine=True,
            maxResults=_PAGE_SIZE,
        ):
            for item in response.get("items", []):
                snippet = item.get("snippet", {})
                resource_id = snippet.get("resourceId", {})
                subscriptions.append(
                    SubscriptionDetails(
                        channel_id=resource_id.get("channelId"),
                        channel_title=snippet.get("title"),
                        created_at=_api_date(snippet.get("publishedAt")),
                    )
                )
        return subscriptions

    def list_playlist_items(self, playlist_id: str) -> list[PlaylistItemDetails]:
        playlist_items: list[PlaylistItemDetails] = []
        for response in _pages(
            self._client.playlistItems(),
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=_PAGE_SIZE,
        ):
            for item in response.get("items", []):
                snippet = item.get("snippet", {})
                details = item.get("contentDetails", {})
                resource_id = snippet.get("resourceId", {})
                video_id = details.get("videoId") or resource_id.get("videoId")
                if isinstance(video_id, str) and video_id:
                    playlist_items.append(
                        PlaylistItemDetails(
                            playlist_id=playlist_id,
                            video_id=video_id,
                            added_at=_api_date(snippet.get("publishedAt")),
                        )
                    )
        return playlist_items

    def search_videos(
        self, topic: str, language_code: str | None = None
    ) -> list[SearchVideo]:
        params: dict[str, object] = {
            "part": "snippet",
            "q": topic,
            "type": "video",
            "maxResults": _PAGE_SIZE,
            "order": "relevance",
        }
        if language_code:
            params["relevanceLanguage"] = language_code
        response = self._client.search().list(**params).execute()
        candidates: list[SearchVideo] = []
        for item in response.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            if isinstance(video_id, str) and video_id:
                snippet = item.get("snippet", {})
                candidates.append(
                    SearchVideo(
                        video_id=video_id,
                        title=snippet.get("title"),
                        channel_title=snippet.get("channelTitle"),
                    )
                )
        return candidates

    def get_my_channel_id(self) -> str | None:
        response = (
            self._client.channels()
            .list(part="id", mine=True, maxResults=1)
            .execute()
        )
        items = response.get("items", [])
        return items[0].get("id") if items else None

    def create_playlist(self, title: str, visibility: str) -> str:
        response = (
            self._client.playlists()
            .insert(
                part="snippet,status",
                body={
                    "snippet": {"title": title},
                    "status": {"privacyStatus": visibility},
                },
            )
            .execute()
        )
        playlist_id = response.get("id")
        if not isinstance(playlist_id, str) or not playlist_id:
            raise RuntimeError("YouTube did not return the new playlist ID.")
        return playlist_id

    def add_video_to_playlist(self, playlist_id: str, video_id: str) -> None:
        (
            self._client.playlistItems()
            .insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {"kind": "youtube#video", "videoId": video_id},
                    }
                },
            )
            .execute()
        )

    def get_videos(self, video_ids: list[str]) -> dict[str, VideoDetails]:
        videos: dict[str, VideoDetails] = {}
        for start in range(0, len(video_ids), _PAGE_SIZE):
            batch = video_ids[start : start + _PAGE_SIZE]
            response = (
                self._client.videos()
                .list(part="snippet,contentDetails", id=",".join(batch))
                .execute()
            )
            for item in response.get("items", []):
                snippet = item.get("snippet", {})
                content_details = item.get("contentDetails", {})
                video_id = item.get("id")
                if not isinstance(video_id, str) or not video_id:
                    continue
                videos[video_id] = VideoDetails(
                    video_id=video_id,
                    published_at=_api_date(snippet.get("publishedAt")),
                    channel_id=snippet.get("channelId"),
                    channel_title=snippet.get("channelTitle"),
                    category_id=snippet.get("categoryId"),
                    duration_seconds=_duration_seconds(
                        content_details.get("duration")
                    ),
                    title=snippet.get("title"),
                    language_code=(
                        snippet.get("defaultLanguage")
                        or snippet.get("defaultAudioLanguage")
                    ),
                )
        return videos

    def get_category_names(self, category_ids: list[str]) -> dict[str, str]:
        if not category_ids:
            return {}
        response = (
            self._client.videoCategories()
            .list(part="snippet", id=",".join(category_ids))
            .execute()
        )
        return {
            item["id"]: item["snippet"]["title"]
            for item in response.get("items", [])
            if item.get("id") and item.get("snippet", {}).get("title")
        }


def youtube_error_reason(error: HttpError) -> str | None:
    """Return YouTube's machine-readable reason from an API error, if present."""
    try:
        payload = json.loads(error.content.decode("utf-8"))
    except (AttributeError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    details = payload.get("error", {}).get("errors", [])
    return details[0].get("reason") if details else None
