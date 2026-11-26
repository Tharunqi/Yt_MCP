from __future__ import annotations

import pytest

from youtube_mcp.common.errors import InvalidIdentifierError, ResourceNotFoundError
from youtube_mcp.discovery.similar_videos import (
    build_search_queries,
    find_similar_videos,
    rank_similar_videos,
)
from youtube_mcp.providers.youtube import VideoMetadata
from youtube_mcp.quota.preflight import QuotaEstimate, estimate_similar_video_quota
from youtube_mcp.quota.usage import record_api_call


def video(
    video_id: str,
    *,
    title: str = "",
    description: str = "",
    tags: tuple[str, ...] = (),
    category_id: str | None = None,
) -> VideoMetadata:
    return VideoMetadata(
        video_id=video_id,
        title=title,
        description=description,
        channel_id="channel-id",
        channel_title="Channel",
        published_at=None,
        tags=tags,
        category_id=category_id,
        duration=None,
        default_language=None,
    )


def test_build_search_queries_uses_title_tags_and_description_keywords() -> None:
    seed = video(
        "seed-id",
        title="  Python async tutorial  ",
        tags=("asyncio", "python"),
        description="Learn Python async patterns and asyncio tools.",
    )

    assert build_search_queries(seed) == [
        "Python async tutorial",
        "asyncio python",
        "learn python async patterns asyncio tools",
    ]


def test_build_search_queries_removes_duplicate_queries_and_obeys_limit() -> None:
    seed = video("seed-id", title="Python", tags=("python",), description="Python is useful")

    assert build_search_queries(seed, max_queries=2) == ["Python", "python useful"]
    assert build_search_queries(seed, max_queries=0) == []


def test_rank_similar_videos_scores_and_explains_metadata_matches() -> None:
    seed = video(
        "seed-id",
        title="Python async tutorial",
        description="Build concurrent applications with asyncio",
        tags=("python", "asyncio"),
        category_id="27",
    )
    strong_match = video(
        "candidate-a",
        title="Advanced Python async tutorial",
        description="Build applications with asyncio",
        tags=("python", "asyncio", "concurrency"),
        category_id="27",
    )
    category_only_match = video("candidate-b", title="Gardening basics", category_id="27")

    ranked = rank_similar_videos(seed, [category_only_match, strong_match])

    assert [result.video.video_id for result in ranked] == ["candidate-a", "candidate-b"]
    assert ranked[0].score > ranked[1].score > 0
    assert ranked[0].reasons == (
        "Title terms: python, async, tutorial",
        "Shared tags: python, asyncio",
        "Description terms: build, applications, asyncio",
        "Same category",
    )
    assert ranked[0].url == "https://www.youtube.com/watch?v=candidate-a"
    assert ranked[1].reasons == ("Same category",)


def test_rank_similar_videos_excludes_seed_empty_and_duplicate_ids() -> None:
    seed = video("seed-id", title="Python async")
    candidates = [
        seed,
        video("", title="Python async"),
        video("candidate", title="Python async"),
        video("candidate", title="Python async tutorial"),
    ]

    ranked = rank_similar_videos(seed, candidates)

    assert [result.video.video_id for result in ranked] == ["candidate"]


def test_rank_similar_videos_has_deterministic_ties_and_respects_limit() -> None:
    seed = video("seed-id", title="Python async")
    candidates = [video("z-video", title="Python async"), video("a-video", title="Python async")]

    ranked = rank_similar_videos(seed, candidates, limit=1)

    assert len(ranked) == 1
    assert ranked[0].video.video_id == "a-video"
    assert ranked[0].score == 0.45


def test_rank_similar_videos_keeps_weak_category_only_match_low() -> None:
    seed = video("seed-id", category_id="27")
    candidate = video("candidate", title="Unrelated title", category_id="27")

    ranked = rank_similar_videos(seed, [candidate])

    assert ranked[0].score == 0.05
    assert ranked[0].reasons == ("Same category",)


def test_rank_similar_videos_returns_empty_when_seed_has_no_usable_signals() -> None:
    seed = video("seed-id", title="The and with", tags=("and",), description="about it")

    assert rank_similar_videos(seed, [video("candidate", title="Python async")]) == []


def test_rank_similar_videos_requires_positive_limit() -> None:
    with pytest.raises(ValueError, match="positive"):
        rank_similar_videos(video("seed-id", title="Python"), [], limit=0)


class FakeVideoProvider:
    def __init__(
        self,
        seed: VideoMetadata | Exception,
        search_results: dict[str, list[VideoMetadata]] | None = None,
    ) -> None:
        self.seed = seed
        self.search_results = search_results or {}
        self.get_video_calls: list[str] = []
        self.search_calls: list[tuple[str, int | None]] = []
        self.events: list[str] = []

    def get_video(self, video_id_or_url: str) -> VideoMetadata:
        record_api_call("standard")
        self.events.append("get_video")
        self.get_video_calls.append(video_id_or_url)
        if isinstance(self.seed, Exception):
            raise self.seed
        return self.seed

    def search_videos(self, query: str, *, max_results: int | None = None) -> list[VideoMetadata]:
        record_api_call("search")
        self.events.append("search_videos")
        self.search_calls.append((query, max_results))
        results = self.search_results.get(query, [])
        if results:
            record_api_call("standard")
        return results


class FakeQuotaReservation:
    def __init__(self) -> None:
        self.settlements: list[QuotaEstimate] = []

    def settle(self, actual: QuotaEstimate) -> None:
        self.settlements.append(actual)


class FakeQuotaPreflight:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.estimates: list[QuotaEstimate] = []
        self.events: list[str] = []
        self.reservation = FakeQuotaReservation()

    def check_and_reserve(self, estimate: QuotaEstimate) -> FakeQuotaReservation:
        self.events.append("preflight")
        self.estimates.append(estimate)
        if self.error:
            raise self.error
        return self.reservation


def test_estimate_similar_video_quota_covers_each_api_bucket() -> None:
    assert estimate_similar_video_quota(max_queries=3) == QuotaEstimate(
        default_bucket_units=4,
        search_query_calls=3,
    )


def test_find_similar_videos_searches_queries_with_one_total_candidate_cap() -> None:
    seed = video(
        "abcdefghijk",
        title="Python async tutorial",
        tags=("asyncio",),
        description="Learn concurrent Python programming",
    )
    first = video("candidate-a", title="Python async tutorial basics")
    second = video("candidate-b", title="Python asyncio tutorial")
    third = video("candidate-c", title="Concurrent Python async")
    fourth = video("candidate-d", title="Async programming in Python")
    queries = build_search_queries(seed)
    provider = FakeVideoProvider(
        seed,
        {
            queries[0]: [seed, first, second],
            queries[1]: [second, third],
            queries[2]: [fourth],
        },
    )
    quota = FakeQuotaPreflight()

    result = find_similar_videos(
        "abcdefghijk",
        provider,
        quota_preflight=quota,
        candidate_limit=3,
        result_limit=2,
    )

    assert provider.get_video_calls == ["abcdefghijk"]
    assert [query for query, _ in provider.search_calls] == queries[:2]
    assert [limit for _, limit in provider.search_calls] == [1, 1]
    assert result.seed.video_id == "abcdefghijk"
    assert result.search_queries == tuple(queries[:2])
    assert len(result.videos) == 2
    assert all(ranked.video.video_id != "abcdefghijk" for ranked in result.videos)
    assert quota.estimates == [estimate_similar_video_quota(max_queries=3)]
    assert quota.reservation.settlements == [QuotaEstimate(3, 2)]
    assert quota.events + provider.events == [
        "preflight",
        "get_video",
        "search_videos",
        "search_videos",
    ]


def test_find_similar_videos_rejects_malformed_id_before_preflight() -> None:
    provider = FakeVideoProvider(video("abcdefghijk", title="Python"))
    quota = FakeQuotaPreflight()

    with pytest.raises(InvalidIdentifierError):
        find_similar_videos("not-a-video-id", provider, quota_preflight=quota)

    assert quota.estimates == []
    assert provider.get_video_calls == []
    assert provider.search_calls == []


def test_find_similar_videos_does_not_search_if_seed_is_unavailable() -> None:
    provider = FakeVideoProvider(ResourceNotFoundError("unavailable seed"))
    quota = FakeQuotaPreflight()

    with pytest.raises(ResourceNotFoundError):
        find_similar_videos("abcdefghijk", provider, quota_preflight=quota)

    assert len(quota.estimates) == 1
    assert quota.reservation.settlements == [QuotaEstimate(1, 0)]
    assert provider.search_calls == []


def test_find_similar_videos_stops_before_api_if_quota_is_unavailable() -> None:
    provider = FakeVideoProvider(video("abcdefghijk", title="Python"))
    quota = FakeQuotaPreflight(error=RuntimeError("quota budget exceeded"))

    with pytest.raises(RuntimeError, match="quota budget exceeded"):
        find_similar_videos("abcdefghijk", provider, quota_preflight=quota)

    assert provider.get_video_calls == []
    assert provider.search_calls == []


def test_find_similar_videos_does_not_search_without_queryable_metadata() -> None:
    seed = video("abcdefghijk", title="", tags=(), description="")
    provider = FakeVideoProvider(seed)
    quota = FakeQuotaPreflight()

    result = find_similar_videos("abcdefghijk", provider, quota_preflight=quota)

    assert result.search_queries == ()
    assert result.videos == ()
    assert provider.search_calls == []
    assert quota.reservation.settlements == [QuotaEstimate(1, 0)]


def test_find_similar_videos_validates_limits_before_provider_calls() -> None:
    provider = FakeVideoProvider(video("abcdefghijk", title="Python"))
    quota = FakeQuotaPreflight()

    with pytest.raises(ValueError, match="candidate_limit"):
        find_similar_videos("abcdefghijk", provider, quota_preflight=quota, candidate_limit=0)

    assert provider.get_video_calls == []
    assert quota.estimates == []
