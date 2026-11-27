"""Metadata-only video summary orchestration for FR-6."""

from __future__ import annotations

import re
from typing import Protocol

from youtube_mcp.common.identifiers import parse_video_id
from youtube_mcp.providers.youtube import VideoMetadata
from youtube_mcp.quota.preflight import (
    QuotaPreflight,
    estimate_metadata_summary_quota,
)
from youtube_mcp.quota.usage import QuotaUsage, quota_usage_context

_DURATION_PATTERN = re.compile(
    r"P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?"
)


class MetadataSummaryProvider(Protocol):
    """Provider operation required by the FR-6 workflow."""

    def get_video(self, video_id_or_url: str) -> VideoMetadata:
        """Resolve a public video and return its available metadata."""
        ...

    def get_video_category_name(self, category_id: str) -> str | None:
        """Resolve an API category ID to its display name when available."""
        ...


def summarize_video_metadata(
    video_url_or_id: str,
    provider: MetadataSummaryProvider,
    *,
    quota_preflight: QuotaPreflight,
) -> dict[str, object]:
    """Fetch one video's metadata and return a clearly labeled metadata summary."""
    video_id = parse_video_id(video_url_or_id)
    reservation = quota_preflight.check_and_reserve(estimate_metadata_summary_quota())
    usage = QuotaUsage()

    try:
        with quota_usage_context(usage):
            video = provider.get_video(video_id)
            category_name = (
                provider.get_video_category_name(video.category_id)
                if video.category_id
                else None
            )
            result = _summary_payload(video, category_name)
    except BaseException:
        reservation.settle(usage.estimate())
        raise

    reservation.settle(usage.estimate())
    return result


def format_duration(duration: str | None) -> str | None:
    """Convert a YouTube ISO-8601 duration to a compact display value."""
    if not duration:
        return None

    match = _DURATION_PATTERN.fullmatch(duration)
    if match is None:
        return None

    parts: list[str] = []
    for key, suffix in (("days", "d"), ("hours", "h"), ("minutes", "m"), ("seconds", "s")):
        value = match.group(key)
        if value is not None and int(value) > 0:
            parts.append(f"{int(value)}{suffix}")

    return " ".join(parts) if parts else "0s"


def _summary_payload(
    video: VideoMetadata, category_name: str | None
) -> dict[str, object]:
    category = (
        {"id": video.category_id, "name": _optional_text(category_name)}
        if video.category_id
        else None
    )
    return {
        "summary_type": "metadata-based",
        "notice": "This summary uses video metadata only; it does not summarize spoken content.",
        "video": {
            "video_id": video.video_id,
            "url": f"https://www.youtube.com/watch?v={video.video_id}",
            "title": _optional_text(video.title),
            "channel": {
                "channel_id": _optional_text(video.channel_id),
                "title": _optional_text(video.channel_title),
            },
            "description": _optional_text(video.description),
            "category": category,
            "published_at": _optional_text(video.published_at),
            "duration": format_duration(video.duration),
            "duration_iso8601": _optional_text(video.duration),
        },
    }


def _optional_text(value: str | None) -> str | None:
    """Return nonblank metadata as text, keeping unavailable values explicit."""
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None
