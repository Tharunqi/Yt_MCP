from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from youtube_mcp.engagement.metrics import summarize_durations
from youtube_mcp.providers.youtube import (
    PlaylistItemDetails,
    SubscriptionDetails,
    VideoDetails,
    YouTubeDataProvider,
)


@dataclass(frozen=True)
class EngagementData:
    liked_video_ids: tuple[str, ...]
    subscriptions: tuple[SubscriptionDetails, ...]
    playlist_items: tuple[PlaylistItemDetails, ...]
    videos: dict[str, VideoDetails]
    category_names: dict[str, str]


def parse_period(start_value: str, end_value: str) -> tuple[date, date]:
    try:
        start = date.fromisoformat(start_value)
        end = date.fromisoformat(end_value)
    except (TypeError, ValueError) as error:
        raise ValueError("Dates must use YYYY-MM-DD format.") from error
    if start > end:
        raise ValueError("The start date must be on or before the end date.")
    return start, end


MAX_SELECTED_PLAYLISTS = 5


def validate_playlist_ids(playlist_ids: list[str] | None) -> list[str]:
    if playlist_ids is None:
        return []
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")
    if any(
        not isinstance(playlist_id, str)
        or not 1 <= len(playlist_id) <= 128
        or not set(playlist_id) <= allowed
        for playlist_id in playlist_ids
    ):
        raise ValueError("Playlist IDs must contain 1 to 128 letters, numbers, _ or -.")
    unique_ids = list(dict.fromkeys(playlist_ids))
    if len(unique_ids) > MAX_SELECTED_PLAYLISTS:
        raise ValueError("Select no more than 5 playlists.")
    return unique_ids


def fetch_engagement_data(
    provider: YouTubeDataProvider, playlist_ids: list[str]
) -> EngagementData:
    liked_video_ids = provider.list_liked_video_ids()
    subscriptions = provider.list_subscriptions()
    playlist_items = [
        item
        for playlist_id in playlist_ids
        for item in provider.list_playlist_items(playlist_id)
    ]
    video_ids = list(
        dict.fromkeys(
            liked_video_ids + [item.video_id for item in playlist_items]
        )
    )
    videos = provider.get_videos(video_ids)
    category_ids = list(
        dict.fromkeys(
            video.category_id
            for video in videos.values()
            if video.category_id is not None
        )
    )
    return EngagementData(
        liked_video_ids=tuple(liked_video_ids),
        subscriptions=tuple(subscriptions),
        playlist_items=tuple(playlist_items),
        videos=videos,
        category_names=provider.get_category_names(category_ids),
    )


def _in_period(value: date | None, start: date, end: date) -> bool:
    return value is not None and start <= value <= end


def _weekly_counts(dates: list[date]) -> list[dict[str, Any]]:
    counts: Counter[date] = Counter(
        value - timedelta(days=value.weekday()) for value in dates
    )
    return [
        {"week_start": week.isoformat(), "count": count}
        for week, count in sorted(counts.items())
    ]


def _top_channels(videos: list[VideoDetails]) -> list[dict[str, Any]]:
    counts: Counter[tuple[str | None, str]] = Counter()
    for video in videos:
        if video.channel_id or video.channel_title:
            key = (video.channel_id, video.channel_title or "Unknown channel")
            counts[key] += 1
    return [
        {"channel_id": channel_id, "channel_title": title, "video_count": count}
        for (channel_id, title), count in sorted(
            counts.items(), key=lambda entry: (-entry[1], entry[0][1].casefold())
        )[:5]
    ]


def _top_categories(
    videos: list[VideoDetails], category_names: dict[str, str]
) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter(
        video.category_id for video in videos if video.category_id
    )
    return [
        {
            "category_id": category_id,
            "category_name": category_names.get(category_id),
            "video_count": count,
        }
        for category_id, count in sorted(
            counts.items(), key=lambda entry: (-entry[1], entry[0])
        )[:5]
    ]


def analyze_period(
    data: EngagementData, start: date, end: date
) -> dict[str, Any]:
    liked_ids = {
        video_id
        for video_id in data.liked_video_ids
        if video_id in data.videos
        and _in_period(data.videos[video_id].published_at, start, end)
    }
    matching_playlist_items = [
        item
        for item in data.playlist_items
        if _in_period(item.added_at, start, end)
    ]
    video_ids = liked_ids | {item.video_id for item in matching_playlist_items}
    period_videos = [
        data.videos[video_id]
        for video_id in sorted(video_ids)
        if video_id in data.videos
    ]
    durations = [
        video.duration_seconds
        for video in period_videos
        if video.duration_seconds is not None
    ]
    duration_stats = summarize_durations(durations)

    return {
        "date_range": {"start": start.isoformat(), "end": end.isoformat()},
        "video_count": len(video_ids),
        "video_metadata_count": len(period_videos),
        "unavailable_video_count": len(video_ids) - len(period_videos),
        "data_quality": {
            "liked_videos_missing_metadata": sum(
                video_id not in data.videos for video_id in data.liked_video_ids
            ),
            "liked_videos_missing_publish_date": sum(
                video_id in data.videos
                and data.videos[video_id].published_at is None
                for video_id in data.liked_video_ids
            ),
            "playlist_items_missing_added_date": sum(
                item.added_at is None for item in data.playlist_items
            ),
            "subscriptions_missing_created_date": sum(
                subscription.created_at is None
                for subscription in data.subscriptions
            ),
        },
        "top_channels": _top_channels(period_videos),
        "top_categories": _top_categories(period_videos, data.category_names),
        "duration_statistics": {
            "count": duration_stats.count,
            "missing_duration_count": len(period_videos) - duration_stats.count,
            "total_seconds": duration_stats.total_seconds,
            "average_seconds": duration_stats.average_seconds,
            "median_seconds": duration_stats.median_seconds,
            "distribution": duration_stats.distribution,
        },
        "time_trends": {
            "subscriptions_created_by_week": _weekly_counts(
                [
                    subscription.created_at
                    for subscription in data.subscriptions
                    if _in_period(subscription.created_at, start, end)
                ]
            ),
            "playlist_items_added_by_week": _weekly_counts(
                [item.added_at for item in matching_playlist_items if item.added_at]
            ),
        },
        "sources": [
            "YouTube liked videos (up to the latest 1,000 available)",
            "YouTube subscription-created dates (up to 1,000 subscriptions)",
            "Selected playlist items and added dates "
            "(up to 5 playlists, 1,000 items each)",
            "YouTube video channel, category, publish date, and duration metadata",
        ],
    }


def _comparison_summary(
    current: dict[str, Any], comparison: dict[str, Any]
) -> dict[str, Any]:
    current_duration = current["duration_statistics"]
    comparison_duration = comparison["duration_statistics"]
    duration_changes = {
        key: (
            current_duration[key] - comparison_duration[key]
            if current_duration[key] is not None
            and comparison_duration[key] is not None
            else None
        )
        for key in (
            "count",
            "total_seconds",
            "average_seconds",
            "median_seconds",
        )
    }
    duration_changes["distribution"] = {
        bucket: current_duration["distribution"][bucket]
        - comparison_duration["distribution"][bucket]
        for bucket in current_duration["distribution"]
    }

    current_channels = {
        channel["channel_id"] or f"title:{channel['channel_title'].casefold()}": channel
        for channel in current["top_channels"]
    }
    comparison_channels = {
        channel["channel_id"] or f"title:{channel['channel_title'].casefold()}": channel
        for channel in comparison["top_channels"]
    }
    channel_changes = [
        {
            "channel_id": (current_channels.get(key) or comparison_channels[key])["channel_id"],
            "channel_title": (
                current_channels.get(key) or comparison_channels[key]
            )["channel_title"],
            "analysis_video_count": current_channels.get(key, {}).get("video_count", 0),
            "comparison_video_count": comparison_channels.get(key, {}).get("video_count", 0),
            "change": current_channels.get(key, {}).get("video_count", 0)
            - comparison_channels.get(key, {}).get("video_count", 0),
        }
        for key in sorted(current_channels.keys() | comparison_channels.keys())
    ]
    current_categories = {
        category["category_id"]: category for category in current["top_categories"]
    }
    comparison_categories = {
        category["category_id"]: category for category in comparison["top_categories"]
    }
    category_changes = [
        {
            "category_id": category_id,
            "category_name": (
                current_categories.get(category_id)
                or comparison_categories[category_id]
            )["category_name"],
            "analysis_video_count": current_categories.get(category_id, {}).get(
                "video_count", 0
            ),
            "comparison_video_count": comparison_categories.get(category_id, {}).get(
                "video_count", 0
            ),
            "change": current_categories.get(category_id, {}).get("video_count", 0)
            - comparison_categories.get(category_id, {}).get("video_count", 0),
        }
        for category_id in sorted(
            current_categories.keys() | comparison_categories.keys()
        )
    ]
    return {
        "video_count_change": current["video_count"] - comparison["video_count"],
        "duration_changes": duration_changes,
        "channel_video_count_changes": channel_changes,
        "category_video_count_changes": category_changes,
    }


def analyze_engagement_data(
    data: EngagementData,
    start: date,
    end: date,
    comparison_start: date | None = None,
    comparison_end: date | None = None,
) -> dict[str, Any]:
    current = analyze_period(data, start, end)
    comparison = None
    if comparison_start is not None and comparison_end is not None:
        comparison = analyze_period(data, comparison_start, comparison_end)
    result: dict[str, Any] = {
        "analysis_period": current,
        "comparison_period": comparison,
        "comparison_summary": (
            _comparison_summary(current, comparison) if comparison is not None else None
        ),
        "data_notes": [
            "YouTube does not provide when a video was liked. "
            "Liked videos use the video publish date for period filtering.",
            "Time trends use the available subscription-created and "
            "selected-playlist-item-added dates.",
            "Only subscriptions and playlist items still returned by YouTube "
            "can appear in trends.",
            "These results describe liked and saved content, not watch time.",
            "Results are calculated for this request and are not saved.",
            "Analysis reads up to 1,000 subscriptions and 1,000 items from "
            "each of up to 5 selected playlists.",
        ],
    }
    return result
