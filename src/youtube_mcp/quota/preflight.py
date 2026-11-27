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
