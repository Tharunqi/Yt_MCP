"""Per-request accounting for attempted YouTube API calls."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Iterator, Literal

from youtube_mcp.quota.preflight import QuotaEstimate

QuotaBucket = Literal["standard", "search"]
_CURRENT_USAGE: ContextVar[QuotaUsage | None] = ContextVar("youtube_quota_usage", default=None)


@dataclass
class QuotaUsage:
    """Mutable counts for one workflow's attempted requests by quota bucket."""

    default_bucket_units: int = 0
    search_query_calls: int = 0

    def record(self, bucket: QuotaBucket) -> None:
        """Count one API request in the correct quota bucket."""
        if bucket == "standard":
            self.default_bucket_units += 1
        elif bucket == "search":
            self.search_query_calls += 1

    def estimate(self) -> QuotaEstimate:
        """Return an immutable snapshot for settling the request reservation."""
        return QuotaEstimate(
            default_bucket_units=self.default_bucket_units,
            search_query_calls=self.search_query_calls,
        )


@contextmanager
def quota_usage_context(usage: QuotaUsage) -> Iterator[None]:
    """Make a request-local usage recorder available to provider calls."""
    token: Token[QuotaUsage | None] = _CURRENT_USAGE.set(usage)
    try:
        yield
    finally:
        _CURRENT_USAGE.reset(token)


def record_api_call(bucket: QuotaBucket) -> None:
    """Count an API attempt when a workflow recorder is active."""
    usage = _CURRENT_USAGE.get()
    if usage is not None:
        usage.record(bucket)
