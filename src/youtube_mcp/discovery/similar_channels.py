"""Bounded channel discovery and application-side metadata ranking for FR-2."""

import re
from dataclasses import dataclass
from typing import Protocol

from youtube_mcp.common.identifiers import parse_channel_identifier
from youtube_mcp.providers.youtube import ChannelMetadata, VideoMetadata
from youtube_mcp.quota.preflight import (
    QuotaPreflight,
    estimate_similar_channels_quota,
)
from youtube_mcp.quota.usage import QuotaUsage, quota_usage_context

_TOKEN = re.compile(r"[^\W_][\w+#]*", flags=re.UNICODE)
_STOP_WORDS = {
    "a", "about", "an", "and", "are", "as", "at", "be", "but", "by", "for",
    "from", "how", "in", "into", "is", "it", "of", "on", "or", "that", "the",
    "this", "to", "with", "you", "your",
}
_CHANNEL_QUERY_STOP_WORDS = _STOP_WORDS | {
    "channel", "com", "official", "subscribe", "youtube",
}

_FIELD_WEIGHTS = {
    "title": 0.10,
    "description": 0.45,
    "recurring_uploads": 0.30,
    "uploads": 0.15,
}


class SimilarChannelProvider(Protocol):
    """Provider operations needed to build bounded channel profiles."""

    def get_channel(self, identifier: str) -> ChannelMetadata:
        """Resolve a channel identifier and return public metadata."""
        ...

    def search_channels(
        self, query: str, *, max_results: int | None = None
    ) -> list[ChannelMetadata]:
        """Search for public channels under the requested result bound."""
        ...

    def list_channel_uploads(
        self, channel: ChannelMetadata, *, max_results: int | None = None
    ) -> list[VideoMetadata]:
        """Read a bounded sample of recent uploads for a resolved channel."""
        ...


@dataclass(frozen=True)
class ChannelProfile:
    """A channel and its bounded recent-upload sample used for ranking."""

    channel: ChannelMetadata
    uploads: tuple[VideoMetadata, ...]


@dataclass(frozen=True)
class RankedChannel:
    """A candidate channel, score, and human-readable metadata match reasons."""

    channel: ChannelMetadata
    score: float
    reasons: tuple[str, ...]
    sampled_upload_count: int

    @property
    def url(self) -> str:
        """Return a stable channel URL from its canonical channel ID."""
        return f"https://www.youtube.com/channel/{self.channel.channel_id}"


@dataclass(frozen=True)
class SimilarChannelsResult:
    """Seed channel, executed queries, and ranked bounded candidates."""

    seed: ChannelMetadata
    search_queries: tuple[str, ...]
    channels: tuple[RankedChannel, ...]


def build_channel_search_queries(
    seed: ChannelMetadata,
    uploads: list[VideoMetadata],
    *,
    max_queries: int = 3,
) -> list[str]:
    """Build queries from channel identity and recurring sampled-upload terms.

    Description terms come first, followed by terms recurring across uploads.
    Tags and titles are fallback signals for sparse channel profiles.
    """
    if max_queries < 1:
        return []

    proposed: list[str] = []
    # Prefer the channel's topic description over generic brand/promotion words.
    brand_phrases = _channel_brand_phrases(seed)
    description_terms = _channel_query_terms(seed.description, brand_phrases=brand_phrases)
    if description_terms:
        proposed.append(" ".join(description_terms[:5]))

    recurring_terms = _recurring_upload_terms(uploads, brand_phrases)
    if recurring_terms:
        proposed.append(" ".join(recurring_terms[:5]))

    # Use upload terms once as a fallback when recurring terms are unavailable.
    if len(proposed) < min(max_queries, 2):
        fallback_terms: list[str] = []
        for upload in uploads:
            fallback_terms.extend(
                _channel_query_terms(upload.title, brand_phrases=brand_phrases)
            )
            for tag in upload.tags:
                fallback_terms.extend(_channel_query_terms(tag, brand_phrases=brand_phrases))
        fallback_terms = list(dict.fromkeys(fallback_terms))
        if fallback_terms:
            proposed.append(" ".join(fallback_terms[:5]))
    unique: list[str] = []
    seen: set[str] = set()
    for query in proposed:
        normalized = query.casefold()
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique.append(query)
            if len(unique) == max_queries:
                break
    return unique


def find_similar_channels(
    seed_identifier: str,
    provider: SimilarChannelProvider,
    *,
    quota_preflight: QuotaPreflight,
    candidate_limit: int = 10,
    result_limit: int = 10,
    max_queries: int = 3,
    upload_sample_size: int = 10,
) -> SimilarChannelsResult:
    """Resolve a channel, search bounded candidates, sample, and rank profiles.

    Identifier and limits are checked before quota reservation. The preflight
    reserves a conservative upper bound for seed/candidate uploads and searches
    before the first YouTube API request. Actual provider calls are settled even
    when a later call fails.
    """
    if candidate_limit < 1:
        raise ValueError("candidate_limit must be a positive integer")
    if result_limit < 1:
        raise ValueError("result_limit must be a positive integer")
    if max_queries < 1:
        raise ValueError("max_queries must be a positive integer")
    if upload_sample_size < 1:
        raise ValueError("upload_sample_size must be a positive integer")

    # Reject malformed input locally before quota reservation or API access.
    parse_channel_identifier(seed_identifier)
    reservation = quota_preflight.check_and_reserve(
        estimate_similar_channels_quota(
            candidate_limit=candidate_limit,
            max_queries=max_queries,
        )
    )
    usage = QuotaUsage()
    try:
        with quota_usage_context(usage):
            seed = provider.get_channel(seed_identifier)
            seed_uploads = provider.list_channel_uploads(
                seed, max_results=upload_sample_size
            )
            queries = build_channel_search_queries(seed, seed_uploads, max_queries=max_queries)

            candidates: list[ChannelMetadata] = []
            candidate_ids = {seed.channel_id}
            searched_queries: list[str] = []

            # Divide one total candidate cap across queries and remove duplicates.
            for index, query in enumerate(queries):
                remaining = candidate_limit - len(candidates)
                if remaining <= 0:
                    break
                queries_left = len(queries) - index
                query_limit = (remaining + queries_left - 1) // queries_left
                searched_queries.append(query)
                for channel in provider.search_channels(query, max_results=query_limit):
                    if not channel.channel_id or channel.channel_id in candidate_ids:
                        continue
                    candidate_ids.add(channel.channel_id)
                    candidates.append(channel)
                    if len(candidates) >= candidate_limit:
                        break

            # Build profiles only for the bounded candidate set.
            profiles = [
                ChannelProfile(
                    channel=channel,
                    uploads=tuple(
                        provider.list_channel_uploads(
                            channel, max_results=upload_sample_size
                        )
                    ),
                )
                for channel in candidates
            ]
            ranked = rank_similar_channels(
                ChannelProfile(seed, tuple(seed_uploads)), profiles, limit=result_limit
            )
            result = SimilarChannelsResult(
                seed=seed,
                search_queries=tuple(searched_queries),
                channels=tuple(ranked),
            )
    except BaseException:
        reservation.settle(usage.estimate())
        raise
    reservation.settle(usage.estimate())
    return result


def rank_similar_channels(
    seed: ChannelProfile,
    candidates: list[ChannelProfile],
    *,
    limit: int = 10,
) -> list[RankedChannel]:
    """Rank channels by identity, description, recurring themes, and uploads.

    Channel title contributes 10%, description 45%, terms recurring across
    sampled uploads 30%, and all sampled upload terms 15%. Missing fields
    contribute zero.
    Candidates with no shared metadata signal are omitted; ties use channel ID.
    """
    if limit < 1:
        raise ValueError("limit must be a positive integer")

    seed_signals = _profile_signals(seed)
    if not any(seed_signals.values()):
        return []

    ranked: list[RankedChannel] = []
    seen = {seed.channel.channel_id}
    for candidate in candidates:
        channel_id = candidate.channel.channel_id
        if not channel_id or channel_id in seen:
            continue
        seen.add(channel_id)
        signals = _profile_signals(candidate)
        score = 0.0
        reasons: list[str] = []
        labels = {
            "title": "Channel title terms",
            "description": "Channel description terms",
            "recurring_uploads": "Recurring upload themes",
            "uploads": "Recent upload terms",
        }
        for field, weight in _FIELD_WEIGHTS.items():
            left = seed_signals[field]
            right = signals[field]
            if not left:
                continue
            overlap = left & right
            score += weight * _jaccard(left, right)
            if overlap:
                ordered = _ordered_overlap(
                    _profile_text(seed, field), _profile_text(candidate, field), overlap
                )[:3]
                reasons.append(f"{labels[field]}: {', '.join(ordered)}")
        if score:
            ranked.append(
                RankedChannel(
                    channel=candidate.channel,
                    score=round(score, 4),
                    reasons=tuple(reasons),
                    sampled_upload_count=len(candidate.uploads),
                )
            )

    ranked.sort(key=lambda item: (-item.score, item.channel.channel_id))
    return ranked[:limit]


def _profile_signals(profile: ChannelProfile) -> dict[str, set[str]]:
    """Extract normalized comparison terms from one bounded channel profile."""
    upload_documents = [
        _tokens(" ".join([video.title, video.description, *video.tags]))
        for video in profile.uploads
    ]
    upload_terms = set().union(*upload_documents) if upload_documents else set()
    recurring_upload_terms = {
        term
        for term in upload_terms
        if sum(term in document for document in upload_documents) >= 2
    }
    return {
        "title": _tokens(profile.channel.title),
        "description": _tokens(profile.channel.description),
        "recurring_uploads": recurring_upload_terms,
        "uploads": upload_terms,
    }


def _profile_text(profile: ChannelProfile, field: str) -> str:
    """Return source text for stable, readable overlap reasons."""
    if field == "title":
        return profile.channel.title
    if field == "description":
        return profile.channel.description
    return " ".join(
        " ".join([video.title, video.description, *video.tags]) for video in profile.uploads
    )


def _recurring_upload_terms(
    uploads: list[VideoMetadata], brand_phrases: tuple[tuple[str, ...], ...]
) -> list[str]:
    """Return terms appearing in at least two sampled uploads, in sample order."""
    documents = [
        _channel_query_terms(
            " ".join([upload.title, upload.description, *upload.tags]),
            brand_phrases=brand_phrases,
        )
        for upload in uploads
    ]
    frequencies: dict[str, int] = {}
    for document in documents:
        for term in set(document):
            frequencies[term] = frequencies.get(term, 0) + 1
    return list(
        dict.fromkeys(
            term
            for document in documents
            for term in document
            if frequencies[term] >= 2
        )
    )


def _tokens(value: str) -> set[str]:
    """Normalize text into unique terms and remove common stop words."""
    return {token for token in _TOKEN.findall(value.casefold()) if token not in _STOP_WORDS}


def _channel_brand_phrases(channel: ChannelMetadata) -> tuple[tuple[str, ...], ...]:
    """Extract the seed's name and handle as phrases for query filtering."""
    return tuple(
        tokens
        for value in (channel.title, channel.custom_url or "")
        if (tokens := tuple(_TOKEN.findall(value.casefold())))
    )


def _channel_query_terms(
    value: str,
    *,
    brand_phrases: tuple[tuple[str, ...], ...] = (),
) -> list[str]:
    """Keep topical terms after removing boilerplate, the seed's brand, and IDs."""
    tokens = _remove_brand_phrases(_TOKEN.findall(value.casefold()), brand_phrases)
    return list(
        dict.fromkeys(
            token
            for token in tokens
            if token not in _CHANNEL_QUERY_STOP_WORDS
            and not any(char.isdigit() for char in token)
        )
    )


def _remove_brand_phrases(
    tokens: list[str], brand_phrases: tuple[tuple[str, ...], ...]
) -> list[str]:
    """Remove exact brand-name sequences while preserving standalone topic words."""
    result: list[str] = []
    index = 0
    while index < len(tokens):
        phrase = next(
            (
                phrase
                for phrase in brand_phrases
                if tokens[index : index + len(phrase)] == list(phrase)
            ),
            None,
        )
        if phrase:
            index += len(phrase)
        else:
            result.append(tokens[index])
            index += 1
    return result


def _ordered_tokens(value: str) -> list[str]:
    """Return unique useful terms in source order for readable search queries."""
    return list(
        dict.fromkeys(
            token for token in _TOKEN.findall(value.casefold()) if token not in _STOP_WORDS
        )
    )


def _ordered_overlap(left: str, right: str, overlap: set[str]) -> list[str]:
    """Order shared words by their first appearance across the two profiles."""
    ordered = dict.fromkeys(_TOKEN.findall(left.casefold()) + _TOKEN.findall(right.casefold()))
    return [term for term in ordered if term in overlap]


def _jaccard(left: set[str], right: set[str]) -> float:
    """Return intersection-over-union similarity for two normalized term sets."""
    union = left | right
    return len(left & right) / len(union) if union else 0.0
