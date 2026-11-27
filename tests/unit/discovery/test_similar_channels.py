from __future__ import annotations

import pytest

from youtube_mcp.common.errors import InvalidIdentifierError, ResourceNotFoundError
from youtube_mcp.discovery.similar_channels import (
    ChannelProfile,
    build_channel_search_queries,
    find_similar_channels,
    rank_similar_channels,
)
from youtube_mcp.providers.youtube import ChannelMetadata, VideoMetadata
from youtube_mcp.quota.preflight import (
    QuotaEstimate,
    estimate_similar_channels_quota,
)
from youtube_mcp.quota.usage import record_api_call

SEED_ID = "UC" + "a" * 22
CANDIDATE_ID = "UC" + "b" * 22


def channel(channel_id: str, title: str, description: str = "") -> ChannelMetadata:
    """Create compact channel fixtures with upload playlists for profile tests."""
    return ChannelMetadata(channel_id, title, description, None, f"UU{channel_id[2:]}")


def video(
    video_id: str,
    title: str,
    *,
    description: str = "",
    tags: tuple[str, ...] = (),
) -> VideoMetadata:
    """Create a video fixture representing a sampled channel upload."""
    return VideoMetadata(
        video_id=video_id,
        title=title,
        description=description,
        channel_id=SEED_ID,
        channel_title="Channel",
        published_at=None,
        tags=tags,
        category_id=None,
        duration="PT5M",
        default_language="en",
    )


class FakeReservation:
    """Capture actual usage submitted when the discovery request settles."""

    def __init__(self) -> None:
        self.actual: list[QuotaEstimate] = []

    def settle(self, actual: QuotaEstimate) -> None:
        self.actual.append(actual)


class FakeQuota:
    """Capture conservative quota estimates before provider access."""

    def __init__(self) -> None:
        self.estimates: list[QuotaEstimate] = []
        self.reservation = FakeReservation()

    def check_and_reserve(self, estimate: QuotaEstimate) -> FakeReservation:
        self.estimates.append(estimate)
        return self.reservation


class FakeChannelProvider:
    """Provide seed/candidate channel metadata and bounded upload samples."""

    def __init__(self) -> None:
        self.seed = channel(SEED_ID, "Python learning", "Python programming tutorials")
        self.candidate = channel(CANDIDATE_ID, "Python academy", "Learn Python programming")
        self.get_calls: list[str] = []
        self.search_calls: list[tuple[str, int | None]] = []
        self.upload_calls: list[tuple[str, int | None]] = []

    def get_channel(self, identifier: str) -> ChannelMetadata:
        record_api_call("standard")
        self.get_calls.append(identifier)
        return self.seed

    def search_channels(
        self, query: str, *, max_results: int | None = None
    ) -> list[ChannelMetadata]:
        record_api_call("search")
        record_api_call("standard")
        self.search_calls.append((query, max_results))
        return [self.seed, self.candidate, self.candidate]

    def list_channel_uploads(
        self, resolved_channel: ChannelMetadata, *, max_results: int | None = None
    ) -> list[VideoMetadata]:
        record_api_call("standard")
        record_api_call("standard")
        self.upload_calls.append((resolved_channel.channel_id, max_results))
        title = (
            "Python async programming guide"
            if resolved_channel.channel_id == SEED_ID
            else "Python async tutorial"
        )
        return [video(f"{resolved_channel.channel_id[-1]}" * 11, title, tags=("python", "async"))]


def test_build_channel_search_queries_uses_uploads_and_description() -> None:
    seed = channel(SEED_ID, "General Channel", "Practical Rust and systems programming")
    uploads = [
        video("a" * 11, "Python concurrency", tags=("asyncio", "tutorial")),
        video("b" * 11, "Python networking"),
    ]

    queries = build_channel_search_queries(seed, uploads, max_queries=3)

    assert queries == [
        "practical rust systems programming",
        "python",
    ]


def test_build_channel_search_queries_filters_brand_tags_and_keeps_topic_terms() -> None:
    seed = channel(
        SEED_ID,
        "TheCubicle",
        "Official YouTube channel. High quality puzzles and speedcubing champions.",
    )
    uploads = [
        video(
            "a" * 11,
            "QiYi is So Back! MFG G3 Review",
            tags=(
                "cube", "cuber", "speed", "solve", "3x3", "thecubicle.com",
                "speedcuber", "speedcube", "puzzle",
            ),
        ),
    ]

    queries = build_channel_search_queries(seed, uploads, max_queries=3)

    assert queries == [
        "high quality puzzles speedcubing champions",
        "qiyi so back mfg review",
    ]
    assert all("thecubicle" not in query and "3x3" not in query for query in queries)


def test_rank_similar_channels_scores_upload_and_description_overlap() -> None:
    seed = ChannelProfile(
        channel(SEED_ID, "Python Learning", "Python tutorials for developers"),
        (video("a" * 11, "Python async patterns", tags=("async", "tutorial")),),
    )
    strong = ChannelProfile(
        channel(CANDIDATE_ID, "Python Academy", "Learn Python tutorials"),
        (video("b" * 11, "Python async programming", tags=("async", "tutorial")),),
    )
    weak = ChannelProfile(
        channel("UC" + "c" * 22, "Cooking Channel", "Python programming sometimes"),
        (video("c" * 11, "Bread baking"),),
    )

    ranked = rank_similar_channels(seed, [weak, strong])

    assert [item.channel.channel_id for item in ranked] == [CANDIDATE_ID, "UC" + "c" * 22]
    assert ranked[0].score > ranked[1].score
    assert ranked[0].sampled_upload_count == 1
    assert any("Recent upload terms" in reason for reason in ranked[0].reasons)


def test_rank_similar_channels_excludes_seed_duplicates_and_empty_matches() -> None:
    seed = ChannelProfile(channel(SEED_ID, "Science learning", "Physics and chemistry"), ())
    other = ChannelProfile(channel(CANDIDATE_ID, "Python coding", "Software projects"), ())

    ranked = rank_similar_channels(seed, [seed, other, other])

    assert ranked == []


def test_find_similar_channels_applies_one_candidate_cap_and_settles_usage() -> None:
    provider = FakeChannelProvider()
    quota = FakeQuota()

    result = find_similar_channels(
        "@seed_channel",
        provider,
        quota_preflight=quota,
        candidate_limit=2,
        result_limit=2,
        max_queries=2,
        upload_sample_size=4,
    )

    assert provider.get_calls == ["@seed_channel"]
    assert len(provider.search_calls) == 2
    assert [limit for _, limit in provider.search_calls] == [1, 1]
    assert provider.upload_calls == [(SEED_ID, 4), (CANDIDATE_ID, 4)]
    assert quota.estimates == [estimate_similar_channels_quota(candidate_limit=2, max_queries=2)]
    assert quota.reservation.actual == [QuotaEstimate(default_bucket_units=7, search_query_calls=2)]
    assert result.seed.channel_id == SEED_ID
    assert result.channels[0].channel.channel_id == CANDIDATE_ID
    assert result.search_queries


def test_find_similar_channels_rejects_malformed_identifier_before_reserving() -> None:
    quota = FakeQuota()
    provider = FakeChannelProvider()

    with pytest.raises(InvalidIdentifierError):
        find_similar_channels("https://example.com/channel", provider, quota_preflight=quota)

    assert quota.estimates == []
    assert provider.get_calls == []


def test_find_similar_channels_fails_without_search_when_seed_is_unavailable() -> None:
    class MissingChannelProvider(FakeChannelProvider):
        def get_channel(self, identifier: str) -> ChannelMetadata:
            record_api_call("standard")
            raise ResourceNotFoundError("missing")

    provider = MissingChannelProvider()
    quota = FakeQuota()

    with pytest.raises(ResourceNotFoundError):
        find_similar_channels(SEED_ID, provider, quota_preflight=quota)

    assert provider.search_calls == []
    assert quota.reservation.actual == [QuotaEstimate(1, 0)]


def test_similar_channel_quota_estimate_is_bounded_and_validated() -> None:
    assert estimate_similar_channels_quota(candidate_limit=4, max_queries=2) == QuotaEstimate(13, 2)
    with pytest.raises(ValueError):
        estimate_similar_channels_quota(candidate_limit=0)
