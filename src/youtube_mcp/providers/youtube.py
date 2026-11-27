"""YouTube Data API provider boundaries for discovery and signed-in features."""

import json
import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError

from youtube_mcp.common.config import Settings, settings
from youtube_mcp.common.errors import ResourceNotFoundError, YouTubeAPIError
from youtube_mcp.common.identifiers import parse_channel_identifier, parse_video_id
from youtube_mcp.quota.usage import QuotaBucket, record_api_call

_PAGE_SIZE = 50
_MAX_LIKED_VIDEOS = 1000
_DURATION_PATTERN = re.compile(
    r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?"
)


@dataclass(frozen=True)
class VideoMetadata:
    video_id: str
    title: str
    description: str
    channel_id: str
    channel_title: str
    published_at: str | None
    tags: tuple[str, ...]
    category_id: str | None
    duration: str | None
    default_language: str | None


@dataclass(frozen=True)
class ChannelMetadata:
    channel_id: str
    title: str
    description: str
    custom_url: str | None
    uploads_playlist_id: str | None


class YouTubeProvider:
    """Thin, injectable wrapper around the official YouTube Data API client."""

    def __init__(self, client: Resource | Any | None = None, config: Settings = settings) -> None:
        if client is not None:
            self._client = client
        elif config.api_key:
            self._client = build("youtube", "v3", developerKey=config.api_key.get_secret_value())
        else:
            self._client = None
        self._config = config

    def _api(self) -> Resource | Any:
        if self._client is None:
            raise YouTubeAPIError("YouTube API access is not configured; set YOUTUBE_API_KEY.")
        return self._client

    @staticmethod
    def _execute(request: Any, *, quota_bucket: QuotaBucket = "standard") -> dict[str, Any]:
        record_api_call(quota_bucket)
        try:
            return request.execute()
        except HttpError as exc:
            raise YouTubeAPIError("YouTube Data API request failed.") from exc

    def get_video(self, video_id_or_url: str) -> VideoMetadata:
        video_id = parse_video_id(video_id_or_url)
        response = self._execute(
            self._api().videos().list(part="snippet,contentDetails", id=video_id),
            quota_bucket="standard",
        )
        items = response.get("items", [])
        if not items:
            raise ResourceNotFoundError("Video was not found or is not publicly accessible.")
        return self._video(items[0])

    def get_video_category_name(self, category_id: str) -> str | None:
        """Resolve a video category ID to its display name when available."""
        response = self._execute(
            self._api().videoCategories().list(part="snippet", id=category_id),
            quota_bucket="standard",
        )
        for item in response.get("items", []):
            title = item.get("snippet", {}).get("title")
            if isinstance(title, str) and title.strip():
                return title.strip()
        return None

    def search_videos(self, query: str, *, max_results: int | None = None) -> list[VideoMetadata]:
        limit = self._bounded_limit(max_results, self._config.max_search_results)
        response = self._execute(
            self._api().search().list(part="snippet", type="video", q=query, maxResults=limit),
            quota_bucket="search",
        )
        ids = [item.get("id", {}).get("videoId") for item in response.get("items", [])]
        return self._videos_by_ids([video_id for video_id in ids if video_id])

    def get_channel(self, identifier: str) -> ChannelMetadata:
        kind, parsed_value = parse_channel_identifier(identifier)
        kwargs = {"part": "snippet,contentDetails"}
        if kind == "handle":
            parsed_value = parsed_value.removeprefix("@")
        parameter = {
            "channel_id": "id",
            "handle": "forHandle",
            "username": "forUsername",
        }[kind]
        kwargs[parameter] = parsed_value
        response = self._execute(self._api().channels().list(**kwargs), quota_bucket="standard")
        items = response.get("items", [])
        if not items:
            raise ResourceNotFoundError("Channel was not found or is not publicly accessible.")
        return self._channel(items[0])

    def search_channels(
        self, query: str, *, max_results: int | None = None
    ) -> list[ChannelMetadata]:
        limit = self._bounded_limit(max_results, self._config.max_search_results)
        response = self._execute(
            self._api().search().list(
                part="snippet",
                type="channel",
                q=query,
                maxResults=limit,
                safeSearch="none",
            ),
            quota_bucket="search",
        )
        ids = [item.get("id", {}).get("channelId") for item in response.get("items", [])]
        return self._channels_by_ids([channel_id for channel_id in ids if channel_id])

    def list_recent_uploads(
        self, channel_identifier: str, *, max_results: int | None = None
    ) -> list[VideoMetadata]:
        """Resolve a channel, then return its bounded recent-upload sample."""
        channel = self.get_channel(channel_identifier)
        return self.list_channel_uploads(channel, max_results=max_results)

    def list_channel_uploads(
        self, channel: ChannelMetadata, *, max_results: int | None = None
    ) -> list[VideoMetadata]:
        """Fetch uploads for resolved metadata without repeating channel lookup."""
        playlist_id = channel.uploads_playlist_id
        if not playlist_id:
            return []
        limit = self._bounded_limit(max_results, self._config.max_upload_sample)
        response = self._execute(
            self._api()
            .playlistItems()
            .list(part="contentDetails", playlistId=playlist_id, maxResults=limit),
            quota_bucket="standard",
        )
        ids = [item.get("contentDetails", {}).get("videoId") for item in response.get("items", [])]
        return self._videos_by_ids([video_id for video_id in ids if video_id])

    def _videos_by_ids(self, ids: list[str]) -> list[VideoMetadata]:
        results: list[VideoMetadata] = []
        for start in range(0, len(ids), 50):
            response = self._execute(
                self._api()
                .videos()
                .list(
                    part="snippet,contentDetails",
                    id=",".join(ids[start : start + 50]),
                ),
                quota_bucket="standard",
            )
            results.extend(self._video(item) for item in response.get("items", []))
        return results

    def _channels_by_ids(self, ids: list[str]) -> list[ChannelMetadata]:
        results: list[ChannelMetadata] = []
        for start in range(0, len(ids), 50):
            response = self._execute(
                self._api()
                .channels()
                .list(
                    part="snippet,contentDetails",
                    id=",".join(ids[start : start + 50]),
                ),
                quota_bucket="standard",
            )
            results.extend(self._channel(item) for item in response.get("items", []))
        return results

    @staticmethod
    def _bounded_limit(requested: int | None, maximum: int) -> int:
        return min(max(1, requested or maximum), maximum)

    @staticmethod
    def _video(item: dict[str, Any]) -> VideoMetadata:
        snippet = item.get("snippet", {})
        details = item.get("contentDetails", {})
        return VideoMetadata(
            video_id=item.get("id", ""),
            title=snippet.get("title", ""),
            description=snippet.get("description", ""),
            channel_id=snippet.get("channelId", ""),
            channel_title=snippet.get("channelTitle", ""),
            published_at=snippet.get("publishedAt"),
            tags=tuple(snippet.get("tags", [])),
            category_id=snippet.get("categoryId"),
            duration=details.get("duration"),
            default_language=snippet.get("defaultLanguage") or snippet.get("defaultAudioLanguage"),
        )

    @staticmethod
    def _channel(item: dict[str, Any]) -> ChannelMetadata:
        snippet = item.get("snippet", {})
        content = item.get("contentDetails", {})
        return ChannelMetadata(
            channel_id=item.get("id", ""),
            title=snippet.get("title", ""),
            description=snippet.get("description", ""),
            custom_url=snippet.get("customUrl"),
            uploads_playlist_id=content.get("relatedPlaylists", {}).get("uploads"),
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
