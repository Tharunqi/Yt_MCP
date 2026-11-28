"""Request-time account retrieval and bounded FR-3 recommendations."""

from __future__ import annotations

from typing import Protocol

from youtube_mcp.common.errors import ResourceNotFoundError
from youtube_mcp.providers.youtube import (
    ChannelMetadata,
    PlaylistItemDetails,
    SubscriptionDetails,
    VideoMetadata,
)
from youtube_mcp.quota.preflight import (
    QuotaPreflight,
    QuotaReservation,
    estimate_personalized_recommendation_quota,
)
from youtube_mcp.quota.usage import QuotaUsage, quota_usage_context
from youtube_mcp.recommendations.personalized import (
    build_preference_profile,
    rank_personalized_recommendations,
)

_MAX_PLAYLISTS = 3
_PLAYLIST_ITEMS_PER_LIST = 50
_MAX_SUBSCRIPTIONS = 50
_MAX_UPLOAD_CHANNELS = 5
_UPLOADS_PER_CHANNEL = 5
_MAX_CANDIDATES = 25
_MAX_RESULTS = 10


class RecommendationAccountProvider(Protocol):
    """Authorized account operations needed to build a request-time profile."""

    def list_liked_video_ids(self) -> list[str]: ...

    def list_subscriptions(
        self, *, max_results: int | None = None
    ) -> list[SubscriptionDetails]: ...

    def list_playlist_items(
        self, playlist_id: str, *, max_results: int | None = None
    ) -> list[PlaylistItemDetails]: ...


class RecommendationMetadataProvider(Protocol):
    """Public metadata and bounded discovery operations for FR-3."""

    def get_videos(self, video_ids: list[str]) -> list[VideoMetadata]: ...

    def search_videos(
        self, query: str, *, max_results: int | None = None
    ) -> list[VideoMetadata]: ...

    def get_channel(self, identifier: str) -> ChannelMetadata: ...

    def list_channel_uploads(
        self, channel: ChannelMetadata, *, max_results: int | None = None
    ) -> list[VideoMetadata]: ...


def recommend_personalized_videos(
    topic: str,
    selected_playlist_ids: list[str] | None,
    account_provider: RecommendationAccountProvider,
    metadata_provider: RecommendationMetadataProvider,
    *,
    quota_preflight: QuotaPreflight,
    include_subscription_uploads: bool = True,
    max_results: int = 10,
    quota_reservation: QuotaReservation | None = None,
) -> dict[str, object]:
    """Read current account signals and return bounded, explained recommendations.

    All profile data remains in memory for this call. Account IDs and preference
    terms are not included in the returned payload or persisted.
    """
    topic, playlist_ids = validate_recommendation_request(
        topic,
        selected_playlist_ids,
        include_subscription_uploads=include_subscription_uploads,
        max_results=max_results,
    )
    reservation = quota_reservation or quota_preflight.check_and_reserve(
        estimate_personalized_recommendation_quota(
            playlist_count=len(playlist_ids),
            include_subscription_uploads=include_subscription_uploads,
        )
    )
    usage = QuotaUsage()
    try:
        with quota_usage_context(usage):
            liked_ids = list(dict.fromkeys(account_provider.list_liked_video_ids()))
            subscriptions = account_provider.list_subscriptions(
                max_results=_MAX_SUBSCRIPTIONS
            )
            playlist_items = [
                item
                for playlist_id in playlist_ids
                for item in account_provider.list_playlist_items(
                    playlist_id, max_results=_PLAYLIST_ITEMS_PER_LIST
                )
            ]
            saved_ids = list(
                dict.fromkeys(item.video_id for item in playlist_items if item.video_id)
            )
            interaction_ids = list(dict.fromkeys([*liked_ids, *saved_ids]))
            interaction_videos = metadata_provider.get_videos(interaction_ids)
            subscribed_ids = [
                subscription.channel_id
                for subscription in subscriptions
                if subscription.channel_id
            ]
            profile = build_preference_profile(
                topic,
                interaction_videos,
                liked_video_ids=liked_ids,
                saved_video_ids=saved_ids,
                subscribed_channel_ids=subscribed_ids,
            )

            candidates = metadata_provider.search_videos(
                topic.strip(), max_results=_MAX_CANDIDATES
            )
            candidate_ids = {video.video_id for video in candidates if video.video_id}
            sampled_channels: list[str] = []
            if include_subscription_uploads:
                channel_attempts = 0
                for channel_id in dict.fromkeys(subscribed_ids):
                    if channel_attempts >= _MAX_UPLOAD_CHANNELS:
                        break
                    channel_attempts += 1
                    try:
                        channel = metadata_provider.get_channel(channel_id)
                    except ResourceNotFoundError:
                        continue
                    sampled_channels.append(channel.channel_id or channel_id)
                    for video in metadata_provider.list_channel_uploads(
                        channel, max_results=_UPLOADS_PER_CHANNEL
                    ):
                        if video.video_id and video.video_id not in candidate_ids:
                            candidate_ids.add(video.video_id)
                            candidates.append(video)

            ranked = rank_personalized_recommendations(
                candidates,
                profile,
                limit=max_results,
                max_per_channel=2,
            )
            result: dict[str, object] = {
                "status": "ok",
                "topic": topic.strip(),
                "result_count": len(ranked),
                "results": [
                    {
                        "video_id": item.video.video_id,
                        "title": item.video.title,
                        "channel_id": item.video.channel_id,
                        "channel_title": item.video.channel_title,
                        "published_at": item.video.published_at,
                        "score": item.score,
                        "reasons": list(item.reasons),
                        "url": item.url,
                    }
                    for item in ranked
                ],
                "sources": {
                    "liked_video_count": len(liked_ids),
                    "saved_video_count": len(saved_ids),
                    "subscription_count": len(subscriptions),
                    "selected_playlist_count": len(playlist_ids),
                    "sampled_subscription_channels": len(sampled_channels),
                    "topic_candidate_limit": _MAX_CANDIDATES,
                    "uploads_per_sampled_channel": _UPLOADS_PER_CHANNEL,
                },
                "notes": [
                    "Recommendations use liked videos (up to 1,000), subscriptions, and only the playlist IDs supplied for this request.",
                    "The preference profile is calculated for this request and is not saved.",
                    "YouTube watch history and a global recommendation feed are not used.",
                ],
            }
    except BaseException:
        reservation.settle(usage.estimate())
        raise

    reservation.settle(usage.estimate())
    return result


def validate_recommendation_request(
    topic: str,
    selected_playlist_ids: list[str] | None,
    *,
    include_subscription_uploads: bool,
    max_results: int,
) -> tuple[str, list[str]]:
    """Validate tool inputs before OAuth or API calls begin."""
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("topic must contain at least one nonblank character")
    if len(topic.strip()) > 200:
        raise ValueError("topic must be 200 characters or fewer")
    if (
        isinstance(max_results, bool)
        or not isinstance(max_results, int)
        or not 1 <= max_results <= _MAX_RESULTS
    ):
        raise ValueError(f"max_results must be between 1 and {_MAX_RESULTS}")
    if not isinstance(include_subscription_uploads, bool):
        raise ValueError("include_subscription_uploads must be a boolean")
    return topic.strip(), _validate_playlist_ids(selected_playlist_ids)


def _validate_playlist_ids(playlist_ids: list[str] | None) -> list[str]:
    if playlist_ids is None:
        return []
    if not isinstance(playlist_ids, list):
        raise ValueError("selected_playlist_ids must be a list of playlist IDs")
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")
    if any(
        not isinstance(playlist_id, str)
        or not 1 <= len(playlist_id) <= 128
        or not set(playlist_id) <= allowed
        for playlist_id in playlist_ids
    ):
        raise ValueError("Playlist IDs must contain 1 to 128 letters, numbers, _ or -.")
    unique_ids = list(dict.fromkeys(playlist_ids))
    if len(unique_ids) > _MAX_PLAYLISTS:
        raise ValueError(f"At most {_MAX_PLAYLISTS} selected playlists are allowed.")
    return unique_ids
