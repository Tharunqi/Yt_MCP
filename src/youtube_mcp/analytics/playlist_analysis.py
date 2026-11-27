"""Build request-scoped, descriptive analysis of one YouTube playlist."""

import re
from collections import Counter
from typing import Any

from youtube_mcp.engagement.metrics import summarize_durations
from youtube_mcp.providers.youtube import YouTubeDataProvider

_PLAYLIST_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


def validate_playlist_id(playlist_id: str) -> str:
    """Check a playlist ID before authentication or API access."""
    if not isinstance(playlist_id, str) or not _PLAYLIST_ID.fullmatch(playlist_id):
        raise ValueError("Playlist ID must contain 1 to 128 letters, numbers, _ or -.")
    return playlist_id


def analyze_playlist(playlist_id: str, provider: YouTubeDataProvider) -> dict[str, Any]:
    """Fetch a bounded playlist and return metadata-only statistics."""
    validate_playlist_id(playlist_id)
    items = provider.list_playlist_items(playlist_id)
    video_ids = list(dict.fromkeys(item.video_id for item in items))
    videos = provider.get_videos(video_ids)
    category_ids = sorted(
        {video.category_id for video in videos.values() if video.category_id}
    )
    category_names = provider.get_category_names(category_ids)

    channels: Counter[tuple[str | None, str]] = Counter()
    categories: Counter[str] = Counter()
    durations: list[int] = []
    summaries: list[dict[str, Any]] = []
    missing_duration_count = 0
    unavailable_item_count = 0
    unknown_channel_count = 0
    unknown_category_count = 0

    for position, item in enumerate(items, start=1):
        video = videos.get(item.video_id)
        if video is None:
            unavailable_item_count += 1
            missing_duration_count += 1
            unknown_channel_count += 1
            unknown_category_count += 1
            summaries.append({
                "position": position,
                "video_id": item.video_id,
                "added_at": item.added_at.isoformat() if item.added_at else None,
                "url": f"https://www.youtube.com/watch?v={item.video_id}",
                "metadata_available": False,
                "title": None,
                "channel_id": None,
                "channel_title": None,
                "category_id": None,
                "category_name": None,
                "published_at": None,
                "duration_seconds": None,
            })
            continue

        if video.duration_seconds is None:
            missing_duration_count += 1
        else:
            durations.append(video.duration_seconds)
        if video.channel_id or video.channel_title:
            channels[(video.channel_id, video.channel_title or "Unknown channel")] += 1
        else:
            unknown_channel_count += 1
        if video.category_id:
            categories[video.category_id] += 1
        else:
            unknown_category_count += 1
        summaries.append({
            "position": position,
            "video_id": video.video_id,
            "added_at": item.added_at.isoformat() if item.added_at else None,
            "url": f"https://www.youtube.com/watch?v={video.video_id}",
            "metadata_available": True,
            "title": video.title,
            "channel_id": video.channel_id,
            "channel_title": video.channel_title,
            "category_id": video.category_id,
            "category_name": category_names.get(video.category_id),
            "published_at": video.published_at.isoformat() if video.published_at else None,
            "duration_seconds": video.duration_seconds,
        })

    duration_stats = summarize_durations(durations)
    return {
        "status": "analyzed",
        "analysis_type": "descriptive_metadata",
        "playlist_id": playlist_id,
        "item_count": len(items),
        "unique_video_count": len(video_ids),
        "total_duration_seconds": duration_stats.total_seconds,
        "duration_count": duration_stats.count,
        "duration_complete": missing_duration_count == 0,
        "missing_duration_count": missing_duration_count,
        "unavailable_item_count": unavailable_item_count,
        "unknown_channel_count": unknown_channel_count,
        "unknown_category_count": unknown_category_count,
        "duration_distribution": duration_stats.distribution,
        "channel_counts": [
            {"channel_id": channel_id, "channel_title": title, "item_count": count}
            for (channel_id, title), count in sorted(
                channels.items(), key=lambda entry: (-entry[1], entry[0][1].casefold())
            )
        ],
        "category_counts": [
            {
                "category_id": category_id,
                "category_name": category_names.get(category_id),
                "item_count": count,
            }
            for category_id, count in sorted(
                categories.items(), key=lambda entry: (-entry[1], entry[0])
            )
        ],
        "items": summaries,
        "data_notes": [
            "This is descriptive analysis based on YouTube metadata only.",
            "It does not measure views, watch time, likes, or viewer behavior.",
            "Results are used for this request and are not saved.",
            "The analysis reads at most 1,000 playlist items across 20 pages.",
            "The total includes durations available from YouTube; check duration_complete.",
        ],
    }
