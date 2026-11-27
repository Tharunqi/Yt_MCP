"""Request-time preference profiles and ranking for FR-3 recommendations."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Iterable

from youtube_mcp.providers.youtube import VideoMetadata

_TOKEN = re.compile(r"[^\W_][\w+#]*", flags=re.UNICODE)
_STOP_WORDS = {
    "a", "about", "an", "and", "are", "as", "at", "be", "but", "by",
    "for", "from", "how", "in", "into", "is", "it", "of", "on", "or",
    "that", "the", "this", "to", "using", "with", "you", "your",
}


@dataclass(frozen=True)
class PreferenceProfile:
    """Ephemeral interests and exclusions computed for one request."""

    topic_terms: frozenset[str]
    interest_terms: frozenset[str]
    creator_channel_ids: frozenset[str]
    subscribed_channel_ids: frozenset[str]
    excluded_video_ids: frozenset[str]


@dataclass(frozen=True)
class RankedRecommendation:
    """A candidate with its deterministic score and human-readable reasons."""

    video: VideoMetadata
    score: float
    reasons: tuple[str, ...]

    @property
    def url(self) -> str:
        """Return the canonical YouTube watch URL."""
        return f"https://www.youtube.com/watch?v={self.video.video_id}"


def build_preference_profile(
    topic: str,
    interaction_videos: Iterable[VideoMetadata],
    *,
    liked_video_ids: Iterable[str] = (),
    saved_video_ids: Iterable[str] = (),
    subscribed_channel_ids: Iterable[str] = (),
) -> PreferenceProfile:
    """Build a non-persistent profile from the current request's account data."""
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("topic must contain at least one nonblank character")

    videos = tuple(interaction_videos)
    topic_terms = frozenset(_tokens(topic))
    interest_terms = frozenset(
        _tokens(
            " ".join(
                value
                for video in videos
                for value in (video.title, video.description, *video.tags)
                if isinstance(value, str)
            )
        )
    )
    creator_channel_ids = frozenset(
        video.channel_id for video in videos if video.channel_id
    )
    subscribed_ids = frozenset(
        channel_id
        for channel_id in subscribed_channel_ids
        if isinstance(channel_id, str) and channel_id
    )
    excluded_ids = frozenset(
        video_id
        for video_id in (*liked_video_ids, *saved_video_ids)
        if isinstance(video_id, str) and video_id
    )
    return PreferenceProfile(
        topic_terms=topic_terms,
        interest_terms=interest_terms,
        creator_channel_ids=creator_channel_ids,
        subscribed_channel_ids=subscribed_ids,
        excluded_video_ids=excluded_ids,
    )


def rank_personalized_recommendations(
    candidates: Iterable[VideoMetadata],
    profile: PreferenceProfile,
    *,
    limit: int = 10,
    max_per_channel: int = 2,
    as_of: date | None = None,
) -> list[RankedRecommendation]:
    """Rank candidates by topic, creator affinity, freshness and diversity.

    Topic similarity contributes 45%, creator affinity 25%, freshness 20%, and
    overlap with prior liked/saved metadata 10%. Missing signals add no score.
    Selection is greedy so repeated creators receive a small diversity penalty;
    no channel contributes more than ``max_per_channel`` results.
    """
    if limit < 1:
        raise ValueError("limit must be a positive integer")
    if max_per_channel < 1:
        raise ValueError("max_per_channel must be a positive integer")

    reference_date = as_of or datetime.now(timezone.utc).date()
    scored: list[tuple[float, str, VideoMetadata, tuple[str, ...]]] = []
    seen_ids = set(profile.excluded_video_ids)
    for video in candidates:
        if not video.video_id or video.video_id in seen_ids:
            continue
        seen_ids.add(video.video_id)
        base_score, reasons = _score(video, profile, reference_date)
        if base_score > 0:
            scored.append((base_score, video.video_id, video, reasons))

    ranked: list[RankedRecommendation] = []
    channel_counts: dict[str, int] = {}
    while scored and len(ranked) < limit:
        eligible = [
            item
            for item in scored
            if not item[2].channel_id
            or channel_counts.get(item[2].channel_id, 0) < max_per_channel
        ]
        if not eligible:
            break
        base_score, video_id, video, reasons = min(
            eligible,
            key=lambda item: (
                -(item[0] - min(channel_counts.get(item[2].channel_id or "", 0) * 0.08, 0.24)),
                item[1],
            ),
        )
        scored.remove((base_score, video_id, video, reasons))
        prior_from_channel = channel_counts.get(video.channel_id or "", 0)
        adjusted_score = max(0.0, base_score - min(prior_from_channel * 0.08, 0.24))
        adjusted_reasons = reasons + (
            ("Channel diversity adjustment",) if prior_from_channel else ()
        )
        ranked.append(
            RankedRecommendation(
                video=video,
                score=round(adjusted_score, 4),
                reasons=adjusted_reasons,
            )
        )
        if video.channel_id:
            channel_counts[video.channel_id] = prior_from_channel + 1
    return ranked


def _score(
    video: VideoMetadata, profile: PreferenceProfile, reference_date: date
) -> tuple[float, tuple[str, ...]]:
    candidate_terms = set(
        _tokens(" ".join((video.title, video.description, *video.tags)))
    )
    topic_overlap = profile.topic_terms & candidate_terms
    topic_score = len(topic_overlap) / len(profile.topic_terms) if profile.topic_terms else 0.0
    interest_overlap = profile.interest_terms & candidate_terms
    interest_score = (
        len(interest_overlap) / len(candidate_terms)
        if profile.interest_terms and candidate_terms
        else 0.0
    )
    creator_score = 0.0
    creator_reason = None
    if video.channel_id in profile.creator_channel_ids:
        creator_score = 1.0
        creator_reason = "From a creator in your liked or saved videos"
    elif video.channel_id in profile.subscribed_channel_ids:
        creator_score = 0.7
        creator_reason = "From a channel you subscribe to"

    if not topic_overlap and not creator_score and not interest_overlap:
        return 0.0, ()

    age_days = _age_days(video.published_at, reference_date)
    freshness_score = max(0.0, 1.0 - age_days / 180) if age_days is not None else 0.0

    score = (
        0.45 * topic_score
        + 0.25 * creator_score
        + 0.20 * freshness_score
        + 0.10 * interest_score
    )
    reasons: list[str] = []
    if topic_overlap:
        reasons.append(f"Topic match: {', '.join(sorted(topic_overlap)[:3])}")
    if creator_reason:
        reasons.append(creator_reason)
    if age_days is not None and age_days <= 180:
        reasons.append(f"Published {age_days} days ago")
    if interest_overlap:
        examples = ", ".join(sorted(interest_overlap)[:3])
        reasons.append(f"Matches your liked or saved topics: {examples}")
    return score, tuple(reasons)


def _age_days(published_at: str | None, reference_date: date) -> int | None:
    if not published_at:
        return None
    try:
        published = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    if published.tzinfo is not None:
        published = published.astimezone(timezone.utc)
    age_days = (reference_date - published.date()).days
    return max(0, age_days)


def _tokens(value: str) -> set[str]:
    return {
        token.casefold()
        for token in _TOKEN.findall(value)
        if token.casefold() not in _STOP_WORDS and len(token) > 1
    }
