"""Quota estimation and fail-closed preflight contract for API workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class QuotaEstimate:
    """Worst-case request usage across YouTube's standard and search buckets."""

    default_bucket_units: int
    search_query_calls: int


class QuotaPreflight(Protocol):
    """Quota gate required before a workflow makes any API request.

    The eventual database-backed implementation must check and reserve both
    buckets atomically. This protocol deliberately has no permissive default.
    """

    def check_and_reserve(self, estimate: QuotaEstimate) -> QuotaReservation:
        """Atomically reserve both buckets or raise before external API calls."""
        ...


class QuotaReservation(Protocol):
    """Handle used to settle or release a successful quota reservation."""

    def settle(self, actual: QuotaEstimate) -> None:
        """Record actual usage and release any unused reserved amount."""
        ...


class QuotaPreflightNotConfiguredError(RuntimeError):
    """Raised when a live workflow has no quota ledger configured."""


class UnavailableQuotaPreflight:
    """Fail-closed placeholder used until a persistent quota ledger is wired."""

    def check_and_reserve(self, estimate: QuotaEstimate) -> QuotaReservation:
        """Reject the workflow before API access because no ledger is available."""
        del estimate
        raise QuotaPreflightNotConfiguredError(
            "YouTube quota tracking is not configured; this workflow cannot run yet."
        )


def estimate_metadata_summary_quota() -> QuotaEstimate:
    """Reserve video details and the optional category-name lookup used by FR-6."""
    return QuotaEstimate(default_bucket_units=2, search_query_calls=0)


def estimate_similar_video_quota(*, max_queries: int = 3) -> QuotaEstimate:
    """Estimate the maximum quota for seed lookup and bounded video searches.

    Each FR-1 run can call ``videos.list`` once for the seed and once to fetch
    candidate details for each search query. Each query also uses one separate
    ``search.list`` call. The estimate is conservative because the seed's
    available metadata is unknown until after its lookup.
    """
    if max_queries < 1:
        raise ValueError("max_queries must be a positive integer")
    return QuotaEstimate(
        default_bucket_units=1 + max_queries,
        search_query_calls=max_queries,
    )


def estimate_similar_channels_quota(
    *, candidate_limit: int = 10, max_queries: int = 3
) -> QuotaEstimate:
    """Reserve quota for seed/candidate upload samples and channel searches.

    Each sampled channel may use one uploads-playlist request and one batched
    videos.list request. Each channel search may also fetch matching channel
    details once. The estimate assumes all bounded candidates have uploads.
    """
    if candidate_limit < 1:
        raise ValueError("candidate_limit must be a positive integer")
    if max_queries < 1:
        raise ValueError("max_queries must be a positive integer")
    return QuotaEstimate(
        default_bucket_units=3 + max_queries + 2 * candidate_limit,
        search_query_calls=max_queries,
    )


def estimate_personalized_recommendation_quota(
    *, playlist_count: int, include_subscription_uploads: bool = True
) -> QuotaEstimate:
    """Reserve a worst-case FR-3 request across account, metadata and search calls.

    The request caps liked videos at 1,000, selected playlists at three with 50
    items each, subscriptions at 50, candidate search at 25 videos, and upload
    sampling at five subscriptions with five uploads each.
    """
    if not 0 <= playlist_count <= 3:
        raise ValueError("playlist_count must be between 0 and 3")

    # Twenty liked pages, one subscriptions page, selected playlist pages,
    # metadata batches for the maximum liked and saved IDs, and one standard
    # call to fetch topic-search candidate details. Search itself is separate.
    interaction_batches = 20 + playlist_count
    standard_calls = 20 + 1 + playlist_count + interaction_batches + 1
    if include_subscription_uploads:
        # Each sampled channel can require a channel lookup, uploads page,
        # and video metadata batch.
        standard_calls += 5 * 3
    return QuotaEstimate(
        default_bucket_units=standard_calls,
        search_query_calls=1,
    )
