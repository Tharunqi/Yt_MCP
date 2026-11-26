"""Pure metadata query and ranking logic for FR-1 similar-video discovery."""

import re
from dataclasses import dataclass
from typing import Protocol

from youtube_mcp.common.identifiers import parse_video_id
from youtube_mcp.providers.youtube import VideoMetadata
from youtube_mcp.quota.preflight import QuotaPreflight, estimate_similar_video_quota
from youtube_mcp.quota.usage import QuotaUsage, quota_usage_context

_TOKEN = re.compile(r"[^\W_][\w+#]*", flags=re.UNICODE)
_STOP_WORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "how",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "using",
    "with",
    "you",
    "your",
}

_FIELD_WEIGHTS = {
    "title": 0.45,
    "tags": 0.30,
    "description": 0.20,
    "category": 0.05,
}


@dataclass(frozen=True)
class RankedVideo:
    """A candidate video with a deterministic similarity score and explanation."""

    video: VideoMetadata
    score: float
    reasons: tuple[str, ...]

    @property
    def url(self) -> str:
        """Return the canonical watch URL for this candidate."""
        return f"https://www.youtube.com/watch?v={self.video.video_id}"


class SimilarVideoProvider(Protocol):
    """Provider operations required by the similar-video orchestration."""

    def get_video(self, video_id_or_url: str) -> VideoMetadata:
        """Resolve a video identifier and return its public metadata."""
        ...

    def search_videos(self, query: str, *, max_results: int | None = None) -> list[VideoMetadata]:
        """Search for public videos while honoring the requested result bound."""
        ...


@dataclass(frozen=True)
class SimilarVideosResult:
    """Seed metadata, attempted queries, and ranked candidate videos."""

    seed: VideoMetadata
    search_queries: tuple[str, ...]
    videos: tuple[RankedVideo, ...]


def build_search_queries(seed: VideoMetadata, *, max_queries: int = 3) -> list[str]:
    """Build title, tag, and description queries in priority order.

    Blank and case-insensitive duplicate queries are removed, and the result is
    capped at ``max_queries`` so the caller can bound external search calls.
    """
    if max_queries <= 0:
        return []

    queries: list[str] = []
    title = seed.title.strip()
    if title:
        queries.append(title[:200])

    tag_query = " ".join(tag.strip() for tag in seed.tags if tag.strip())
    if tag_query:
        queries.append(tag_query[:200])

    description_terms = _ordered_tokens(seed.description)
    if description_terms:
        queries.append(" ".join(description_terms[:6]))

    unique_queries: list[str] = []
    seen: set[str] = set()
    for query in queries:
        normalized = query.casefold()
        if normalized not in seen:
            seen.add(normalized)
            unique_queries.append(query)
            if len(unique_queries) == max_queries:
                break
    return unique_queries


def find_similar_videos(
    seed_identifier: str,
    provider: SimilarVideoProvider,
    *,
    quota_preflight: QuotaPreflight,
    candidate_limit: int = 25,
    result_limit: int = 10,
    max_queries: int = 3,
) -> SimilarVideosResult:
    """Fetch a seed, search a bounded candidate pool, and rank its videos.

    Local validation runs before reservation. The quota gate reserves a
    conservative worst-case amount before the first API call; actual provider
    requests are recorded and settled afterward, even when a provider call
    fails. Candidate capacity is divided across remaining queries; duplicate
    IDs and the seed are discarded while enforcing one total cap.
    """
    if candidate_limit < 1:
        raise ValueError("candidate_limit must be a positive integer")
    if result_limit < 1:
        raise ValueError("result_limit must be a positive integer")
    if max_queries < 1:
        raise ValueError("max_queries must be a positive integer")

    # Validate locally before reserving quota or contacting the provider.
    seed_video_id = parse_video_id(seed_identifier)

    # Reserve the worst-case cost because seed metadata is not known yet.
    reservation = quota_preflight.check_and_reserve(
        estimate_similar_video_quota(max_queries=max_queries)
    )
    usage = QuotaUsage()
    try:
        with quota_usage_context(usage):
            # Resolve the seed first; a failed lookup must not trigger searches.
            seed = provider.get_video(seed_video_id)

            # Prefer title, then tags, then description; stop if no query is possible.
            queries = build_search_queries(seed, max_queries=max_queries)

            # Track IDs across queries because result sets can overlap.
            candidates: list[VideoMetadata] = []
            candidate_ids = {seed.video_id}
            searched_queries: list[str] = []

            for index, query in enumerate(queries):
                remaining_slots = candidate_limit - len(candidates)
                if remaining_slots <= 0:
                    break

                # Spread the remaining capacity across the queries still to run.
                remaining_queries = len(queries) - index
                query_limit = (remaining_slots + remaining_queries - 1) // remaining_queries
                searched_queries.append(query)
                search_results = provider.search_videos(query, max_results=query_limit)
                for candidate in search_results:
                    if not candidate.video_id or candidate.video_id in candidate_ids:
                        continue
                    candidate_ids.add(candidate.video_id)
                    candidates.append(candidate)
                    if len(candidates) == candidate_limit:
                        break

            ranked = rank_similar_videos(seed, candidates, limit=result_limit)
            result = SimilarVideosResult(
                seed=seed,
                search_queries=tuple(searched_queries),
                videos=tuple(ranked),
            )
    except BaseException:
        reservation.settle(usage.estimate())
        raise
    reservation.settle(usage.estimate())
    return result


def rank_similar_videos(
    seed: VideoMetadata,
    candidates: list[VideoMetadata],
    *,
    limit: int = 10,
) -> list[RankedVideo]:
    """Score, explain, deduplicate, and order candidates using seed metadata.

    Text signals use Jaccard overlap over normalized token sets. The score is a
    weighted sum of title (45%), tags (30%), description (20%), and exact
    category match (5%). Missing fields contribute no evidence; the score stays
    on a stable 0-1 scale instead of boosting sparse metadata to a perfect match.

    Candidates with no shared signal are omitted. Remaining ties are broken by
    video ID so repeated calls with the same metadata return the same order.
    """
    if limit < 1:
        raise ValueError("limit must be a positive integer")

    seed_signals = _signals(seed)
    if not any(seed_signals.values()):
        return []

    ranked: list[RankedVideo] = []
    seen_ids = {seed.video_id}
    for candidate in candidates:
        if not candidate.video_id or candidate.video_id in seen_ids:
            continue
        seen_ids.add(candidate.video_id)

        candidate_signals = _signals(candidate)
        weighted_score = 0.0
        reasons: list[str] = []

        for field in ("title", "tags", "description"):
            seed_terms = seed_signals[field]
            if not seed_terms:
                continue
            candidate_terms = candidate_signals[field]
            overlap = seed_terms & candidate_terms
            weighted_score += _FIELD_WEIGHTS[field] * _jaccard(seed_terms, candidate_terms)
            if overlap:
                examples = _ordered_overlap(
                    _field_text(seed, field), _field_text(candidate, field), overlap
                )[:3]
                label = "Shared tags" if field == "tags" else f"{field.title()} terms"
                reasons.append(f"{label}: {', '.join(examples)}")

        same_category = bool(seed.category_id and seed.category_id == candidate.category_id)
        if seed.category_id:
            weighted_score += _FIELD_WEIGHTS["category"] * same_category
        if same_category:
            reasons.append("Same category")

        if weighted_score == 0:
            continue

        ranked.append(
            RankedVideo(
                video=candidate,
                score=round(weighted_score, 4),
                reasons=tuple(reasons),
            )
        )

    ranked.sort(key=lambda result: (-result.score, result.video.video_id))
    return ranked[:limit]


def _signals(video: VideoMetadata) -> dict[str, set[str]]:
    """Convert video fields into token sets plus an exact category signal."""
    return {
        "title": _tokens(video.title),
        "tags": _tokens(" ".join(video.tags)),
        "description": _tokens(video.description),
        "category": {video.category_id} if video.category_id else set(),
    }


def _tokens(value: str) -> set[str]:
    """Normalize text into unique case-folded terms without common stop words."""
    return {token for token in _TOKEN.findall(value.casefold()) if token not in _STOP_WORDS}


def _ordered_tokens(value: str) -> list[str]:
    """Extract unique normalized terms in source order for readable queries."""
    return list(
        dict.fromkeys(
            token for token in _TOKEN.findall(value.casefold()) if token not in _STOP_WORDS
        )
    )


def _field_text(video: VideoMetadata, field: str) -> str:
    """Get a signal field as text, joining tags into one searchable string."""
    if field == "tags":
        return " ".join(video.tags)
    return getattr(video, field)


def _ordered_overlap(seed_text: str, candidate_text: str, overlap: set[str]) -> list[str]:
    """Keep shared terms in first-seen order for concise ranking explanations."""
    order = dict.fromkeys(
        _TOKEN.findall(seed_text.casefold()) + _TOKEN.findall(candidate_text.casefold())
    )
    return [term for term in order if term in overlap]


def _jaccard(left: set[str], right: set[str]) -> float:
    """Return the intersection-over-union similarity for two token sets."""
    union = left | right
    return len(left & right) / len(union) if union else 0.0
