"""Official YouTube Data API v3 provider boundary for public discovery data."""

from dataclasses import dataclass
from typing import Any

from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError

from youtube_mcp.common.config import Settings, settings
from youtube_mcp.common.errors import ResourceNotFoundError, YouTubeAPIError
from youtube_mcp.common.identifiers import parse_channel_identifier, parse_video_id


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
    def _execute(request: Any) -> dict[str, Any]:
        try:
            return request.execute()
        except HttpError as exc:
            raise YouTubeAPIError("YouTube Data API request failed.") from exc

    def get_video(self, video_id_or_url: str) -> VideoMetadata:
        video_id = parse_video_id(video_id_or_url)
        response = self._execute(
            self._api().videos().list(part="snippet,contentDetails", id=video_id)
        )
        items = response.get("items", [])
        if not items:
            raise ResourceNotFoundError("Video was not found or is not publicly accessible.")
        return self._video(items[0])

    def search_videos(self, query: str, *, max_results: int | None = None) -> list[VideoMetadata]:
        limit = self._bounded_limit(max_results, self._config.max_search_results)
        response = self._execute(
            self._api().search().list(part="snippet", type="video", q=query, maxResults=limit)
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
        response = self._execute(self._api().channels().list(**kwargs))
        items = response.get("items", [])
        if not items:
            raise ResourceNotFoundError("Channel was not found or is not publicly accessible.")
        return self._channel(items[0])

    def search_channels(
        self, query: str, *, max_results: int | None = None
    ) -> list[ChannelMetadata]:
        limit = self._bounded_limit(max_results, self._config.max_search_results)
        response = self._execute(
            self._api().search().list(part="snippet", type="channel", q=query, maxResults=limit)
        )
        ids = [item.get("id", {}).get("channelId") for item in response.get("items", [])]
        return self._channels_by_ids([channel_id for channel_id in ids if channel_id])

    def list_recent_uploads(
        self, channel_identifier: str, *, max_results: int | None = None
    ) -> list[VideoMetadata]:
        channel = self.get_channel(channel_identifier)
        playlist_id = channel.uploads_playlist_id
        if not playlist_id:
            return []
        limit = self._bounded_limit(max_results, self._config.max_upload_sample)
        response = self._execute(
            self._api()
            .playlistItems()
            .list(part="contentDetails", playlistId=playlist_id, maxResults=limit)
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
                )
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
                )
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
