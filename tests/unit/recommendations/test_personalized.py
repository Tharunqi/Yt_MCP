from __future__ import annotations

from datetime import date

import pytest

from youtube_mcp.providers.youtube import VideoMetadata
from youtube_mcp.recommendations.personalized import (
    build_preference_profile,
    rank_personalized_recommendations,
)


def video(
    video_id: str,
    *,
    title: str,
    channel_id: str,
    published_at: str | None = "2026-11-20T00:00:00Z",
    tags: tuple[str, ...] = (),
) -> VideoMetadata:
    return VideoMetadata(
        video_id=video_id,
        title=title,
        description="",
        channel_id=channel_id,
        channel_title=channel_id,
        published_at=published_at,
        tags=tags,
        category_id=None,
        duration=None,
        default_language=None,
    )


def test_profile_uses_request_topic_interactions_and_exclusions() -> None:
    liked = video("liked-1", title="Python data science", channel_id="creator-1")
    saved = video("saved-1", title="Machine learning", channel_id="creator-2")

    profile = build_preference_profile(
        "Python tutorials",
        [liked, saved],
        liked_video_ids=["liked-1"],
        saved_video_ids=["saved-1"],
        subscribed_channel_ids=["creator-3"],
    )

    assert profile.topic_terms == {"python", "tutorials"}
    assert {"data", "science", "machine", "learning"} <= profile.interest_terms
    assert profile.creator_channel_ids == {"creator-1", "creator-2"}
    assert profile.subscribed_channel_ids == {"creator-3"}
    assert profile.excluded_video_ids == {"liked-1", "saved-1"}


def test_rank_combines_topic_creator_freshness_and_explanation() -> None:
    profile = build_preference_profile(
        "Python tutorial",
        [video("liked", title="Python data", channel_id="fav-creator")],
        liked_video_ids=["liked"],
        subscribed_channel_ids=["subscribed-creator"],
    )
    candidates = [
        video("topic", title="Python tutorial guide", channel_id="new-creator"),
        video("creator", title="Cooking basics", channel_id="fav-creator"),
        video("subscription", title="Travel vlog", channel_id="subscribed-creator"),
    ]

    ranked = rank_personalized_recommendations(
        candidates, profile, as_of=date.fromisoformat("2026-11-27")
    )

    assert [item.video.video_id for item in ranked] == ["topic", "creator", "subscription"]
    assert ranked[0].score > ranked[1].score > ranked[2].score
    assert ranked[0].reasons[0].startswith("Topic match:")
    assert ranked[1].reasons[0] == "From a creator in your liked or saved videos"
    assert ranked[0].url.endswith("?v=topic")


def test_rank_excludes_liked_saved_duplicates_and_applies_channel_diversity() -> None:
    profile = build_preference_profile(
        "Python",
        [],
        liked_video_ids=["liked"],
        saved_video_ids=["saved"],
    )
    candidates = [
        video("liked", title="Python", channel_id="creator-a"),
        video("saved", title="Python", channel_id="creator-a"),
        video("same-a", title="Python tips", channel_id="creator-a"),
        video("same-a", title="Python tutorial", channel_id="creator-a"),
        video("creator-b", title="Python tutorial", channel_id="creator-b"),
        video("creator-c", title="Python guide", channel_id="creator-c"),
    ]

    ranked = rank_personalized_recommendations(
        candidates,
        profile,
        limit=3,
        max_per_channel=1,
        as_of=date.fromisoformat("2026-11-27"),
    )

    assert [item.video.video_id for item in ranked] == ["creator-b", "creator-c", "same-a"]
    assert len({item.video.channel_id for item in ranked}) == 3


def test_rank_uses_video_id_for_stable_ties_and_rejects_invalid_limits() -> None:
    profile = build_preference_profile("Python", [])
    candidates = [
        video("z-video", title="Python basics", channel_id="creator-z"),
        video("a-video", title="Python basics", channel_id="creator-a"),
    ]

    ranked = rank_personalized_recommendations(
        candidates, profile, as_of=date.fromisoformat("2026-11-27")
    )

    assert [item.video.video_id for item in ranked] == ["a-video", "z-video"]
    with pytest.raises(ValueError, match="limit"):
        rank_personalized_recommendations(candidates, profile, limit=0)
    with pytest.raises(ValueError, match="max_per_channel"):
        rank_personalized_recommendations(candidates, profile, max_per_channel=0)


def test_rank_omits_fresh_candidates_without_a_personal_or_topic_match() -> None:
    profile = build_preference_profile("Python", [])
    unrelated = video("unrelated", title="Cooking basics", channel_id="creator-z")

    assert rank_personalized_recommendations(
        [unrelated], profile, as_of=date.fromisoformat("2026-11-27")
    ) == []
