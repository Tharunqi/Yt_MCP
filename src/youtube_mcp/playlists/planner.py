import re
from dataclasses import dataclass

from youtube_mcp.providers.youtube import SearchVideo, VideoDetails

_VISIBILITIES = {"private", "unlisted", "public"}
_LANGUAGE_NAMES = {
    "arabic": "ar",
    "chinese": "zh",
    "english": "en",
    "french": "fr",
    "german": "de",
    "hindi": "hi",
    "japanese": "ja",
    "korean": "ko",
    "portuguese": "pt",
    "spanish": "es",
    "tamil": "ta",
    "telugu": "te",
}


@dataclass(frozen=True)
class PlaylistRequest:
    topic: str
    total_duration_minutes: int
    max_video_length_minutes: int | None
    language_code: str | None
    title: str
    visibility: str


@dataclass(frozen=True)
class PlaylistPlan:
    request: PlaylistRequest
    items: tuple[dict[str, object], ...]
    excluded_items: tuple[dict[str, object], ...]
    total_duration_seconds: int


def normalize_language(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    language = _LANGUAGE_NAMES.get(value.strip().casefold(), value.strip().casefold())
    if not re.fullmatch(r"[a-z]{2}", language):
        raise ValueError("Use a language name or a two-letter language code.")
    return language


def validate_request(
    topic: str,
    total_duration_minutes: int,
    max_video_length_minutes: int | None,
    language: str | None,
    title: str,
    visibility: str,
) -> PlaylistRequest:
    clean_topic = topic.strip()
    clean_title = title.strip()
    clean_visibility = visibility.strip().casefold()
    if not clean_topic or len(clean_topic) > 500:
        raise ValueError("Topic must be between 1 and 500 characters.")
    if isinstance(total_duration_minutes, bool) or total_duration_minutes <= 0:
        raise ValueError("Total playlist duration must be a positive number of minutes.")
    if max_video_length_minutes is not None and (
        isinstance(max_video_length_minutes, bool) or max_video_length_minutes <= 0
    ):
        raise ValueError("Maximum video length must be a positive number of minutes.")
    if not clean_title or len(clean_title) > 150:
        raise ValueError("Playlist title must be between 1 and 150 characters.")
    if clean_visibility not in _VISIBILITIES:
        raise ValueError("Visibility must be private, unlisted, or public.")
    return PlaylistRequest(
        topic=clean_topic,
        total_duration_minutes=total_duration_minutes,
        max_video_length_minutes=max_video_length_minutes,
        language_code=normalize_language(language),
        title=clean_title,
        visibility=clean_visibility,
    )


def _duration_label(duration_seconds: int) -> str:
    hours, remainder = divmod(duration_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {seconds}s" if seconds else f"{minutes}m"
    return f"{seconds}s"


def _language_matches(video_language: str | None, requested: str) -> bool:
    return bool(video_language) and video_language.split("-")[0].casefold() == requested


def build_playlist_plan(
    request: PlaylistRequest,
    candidates: list[SearchVideo],
    videos: dict[str, VideoDetails],
) -> PlaylistPlan:
    budget = request.total_duration_minutes * 60
    remaining = budget
    max_video_seconds = (
        request.max_video_length_minutes * 60
        if request.max_video_length_minutes is not None
        else None
    )
    chosen: list[dict[str, object]] = []
    excluded: list[dict[str, object]] = []
    seen: set[str] = set()

    def exclude(candidate: SearchVideo, reason: str, duration: int | None = None) -> None:
        excluded.append(
            {
                "video_id": candidate.video_id,
                "title": candidate.title,
                "channel": candidate.channel_title,
                "duration_seconds": duration,
                "reason": reason,
            }
        )

    for candidate in candidates:
        if candidate.video_id in seen:
            exclude(candidate, "Duplicate result removed.")
            continue
        seen.add(candidate.video_id)
        video = videos.get(candidate.video_id)
        if video is None:
            exclude(candidate, "Video is unavailable.")
            continue
        duration = video.duration_seconds
        if duration is None:
            exclude(candidate, "Duration is unknown; it was not added to the plan.")
            continue
        if max_video_seconds is not None and duration > max_video_seconds:
            exclude(candidate, "Video is longer than the requested maximum.", duration)
            continue
        if request.language_code and not video.language_code:
            exclude(candidate, "Language is unknown; it was not treated as a match.", duration)
            continue
        if request.language_code and not _language_matches(
            video.language_code, request.language_code
        ):
            exclude(candidate, "Video language does not match the request.", duration)
            continue
        if duration > remaining:
            exclude(candidate, "Video does not fit the remaining duration budget.", duration)
            continue

        title = video.title or candidate.title or "Unknown title"
        channel = video.channel_title or candidate.channel_title or "Unknown channel"
        chosen.append(
            {
                "video_id": video.video_id,
                "title": title,
                "channel": channel,
                "duration_seconds": duration,
                "duration": _duration_label(duration),
                "language": video.language_code or "unknown",
                "url": f"https://www.youtube.com/watch?v={video.video_id}",
                "selection_reason": (
                    "YouTube relevance match that fits the requested limits."
                ),
            }
        )
        remaining -= duration

    return PlaylistPlan(
        request=request,
        items=tuple(chosen),
        excluded_items=tuple(excluded),
        total_duration_seconds=budget - remaining,
    )


def preview_result(plan: PlaylistPlan, preview_id: str) -> dict[str, object]:
    budget = plan.request.total_duration_minutes * 60
    return {
        "status": "preview",
        "preview_id": preview_id,
        "topic": plan.request.topic,
        "playlist_title": plan.request.title,
        "visibility": plan.request.visibility,
        "requested_duration_seconds": budget,
        "requested_duration": _duration_label(budget),
        "planned_duration_seconds": plan.total_duration_seconds,
        "planned_duration": _duration_label(plan.total_duration_seconds),
        "remaining_duration_seconds": budget - plan.total_duration_seconds,
        "remaining_duration": _duration_label(
            budget - plan.total_duration_seconds
        ),
        "max_video_length_minutes": plan.request.max_video_length_minutes,
        "language": plan.request.language_code or "not set",
        "items": list(plan.items),
        "excluded_items": list(plan.excluded_items),
        "can_create": bool(plan.items),
        "confirmation_note": (
            "Review the title, every video, total duration, and privacy before confirming."
        ),
    }
