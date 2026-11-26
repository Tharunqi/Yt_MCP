"""PostgreSQL-backed atomic reservations for YouTube quota buckets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import Engine, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session, sessionmaker

from youtube_mcp.database.models import Base, QuotaBucketUsage, QuotaReservationRecord
from youtube_mcp.quota.preflight import QuotaEstimate

_QUOTA_TIMEZONE = ZoneInfo("America/Los_Angeles")
_STANDARD_BUCKET = "standard"
_SEARCH_BUCKET = "search"


class QuotaBudgetExceededError(RuntimeError):
    """Raised when either daily quota bucket cannot cover a reservation."""


class QuotaLedgerStateError(RuntimeError):
    """Raised when a reservation cannot be settled consistently."""


@dataclass(frozen=True)
class QuotaBucketState:
    """Snapshot of a daily bucket's limit, usage, and reserved capacity."""

    daily_limit: int
    consumed: int
    reserved: int

    @property
    def remaining(self) -> int:
        """Return quota that is neither consumed nor reserved."""
        return max(0, self.daily_limit - self.consumed - self.reserved)


@dataclass(frozen=True)
class SQLAlchemyQuotaReservation:
    """Handle returned after a successful, committed quota reservation."""

    ledger: SQLAlchemyQuotaLedger
    request_id: str
    estimate: QuotaEstimate

    def settle(self, actual: QuotaEstimate) -> None:
        """Record actual request usage and release unused reserved capacity."""
        self.ledger._settle(self.request_id, self.estimate, actual)


class SQLAlchemyQuotaLedger:
    """Atomically reserve and settle daily quota in a SQLAlchemy database.

    The ledger creates tables from model metadata because migrations are not
    configured. In production, use PostgreSQL so row locks serialize competing
    reservations across requests and app instances.
    """

    def __init__(
        self,
        engine: Engine,
        *,
        standard_daily_limit: int = 10_000,
        search_daily_limit: int = 100,
    ) -> None:
        if standard_daily_limit < 1 or search_daily_limit < 1:
            raise ValueError("daily quota limits must be positive")
        self._engine = engine
        self._session_factory = sessionmaker(engine, expire_on_commit=False)
        self._limits = {
            _STANDARD_BUCKET: standard_daily_limit,
            _SEARCH_BUCKET: search_daily_limit,
        }
        Base.metadata.create_all(engine)

    def check_and_reserve(self, estimate: QuotaEstimate) -> SQLAlchemyQuotaReservation:
        """Check and reserve both quota buckets in one transaction."""
        if estimate.default_bucket_units < 0 or estimate.search_query_calls < 0:
            raise ValueError("quota estimates cannot be negative")

        quota_day = self._quota_day()
        request_id = str(uuid4())
        amounts = {
            _STANDARD_BUCKET: estimate.default_bucket_units,
            _SEARCH_BUCKET: estimate.search_query_calls,
        }

        with self._session_factory.begin() as session:
            for bucket_name in sorted(amounts):
                self._insert_bucket_if_missing(session, quota_day, bucket_name)

            rows = session.scalars(
                select(QuotaBucketUsage)
                .where(
                    QuotaBucketUsage.quota_day == quota_day,
                    QuotaBucketUsage.bucket_name.in_(amounts),
                )
                .order_by(QuotaBucketUsage.bucket_name)
                .with_for_update()
            ).all()
            buckets = {row.bucket_name: row for row in rows}

            for bucket_name, amount in amounts.items():
                bucket = buckets[bucket_name]
                if bucket.consumed + bucket.reserved + amount > bucket.daily_limit:
                    raise QuotaBudgetExceededError(
                        f"Insufficient remaining quota in the {bucket_name} bucket."
                    )

            for bucket_name, amount in amounts.items():
                buckets[bucket_name].reserved += amount

            session.add(
                QuotaReservationRecord(
                    request_id=request_id,
                    quota_day=quota_day,
                    estimated_default_bucket_units=estimate.default_bucket_units,
                    estimated_search_query_calls=estimate.search_query_calls,
                )
            )

        return SQLAlchemyQuotaReservation(self, request_id, estimate)

    def remaining_today(self) -> dict[str, QuotaBucketState]:
        """Return current daily limits and remaining capacity for both buckets."""
        quota_day = self._quota_day()
        with self._session_factory() as session:
            rows = session.scalars(
                select(QuotaBucketUsage).where(QuotaBucketUsage.quota_day == quota_day)
            ).all()
            recorded = {row.bucket_name: row for row in rows}

        return {
            bucket_name: QuotaBucketState(
                daily_limit=(
                    recorded[bucket_name].daily_limit if bucket_name in recorded else limit
                ),
                consumed=(recorded[bucket_name].consumed if bucket_name in recorded else 0),
                reserved=(recorded[bucket_name].reserved if bucket_name in recorded else 0),
            )
            for bucket_name, limit in self._limits.items()
        }

    def _settle(self, request_id: str, estimate: QuotaEstimate, actual: QuotaEstimate) -> None:
        """Atomically move reserved usage to consumed usage for both buckets."""
        if actual.default_bucket_units < 0 or actual.search_query_calls < 0:
            raise ValueError("actual quota usage cannot be negative")

        with self._session_factory.begin() as session:
            reservation = session.scalar(
                select(QuotaReservationRecord)
                .where(QuotaReservationRecord.request_id == request_id)
                .with_for_update()
            )
            if reservation is None:
                raise QuotaLedgerStateError("Quota reservation was not found.")
            if reservation.status == "settled":
                if (
                    reservation.actual_default_bucket_units == actual.default_bucket_units
                    and reservation.actual_search_query_calls == actual.search_query_calls
                ):
                    return
                raise QuotaLedgerStateError("Quota reservation was already settled differently.")

            amounts = {
                _STANDARD_BUCKET: (estimate.default_bucket_units, actual.default_bucket_units),
                _SEARCH_BUCKET: (estimate.search_query_calls, actual.search_query_calls),
            }
            rows = session.scalars(
                select(QuotaBucketUsage)
                .where(
                    QuotaBucketUsage.quota_day == reservation.quota_day,
                    QuotaBucketUsage.bucket_name.in_(amounts),
                )
                .order_by(QuotaBucketUsage.bucket_name)
                .with_for_update()
            ).all()
            buckets = {row.bucket_name: row for row in rows}

            for bucket_name, (reserved_amount, actual_amount) in amounts.items():
                bucket = buckets[bucket_name]
                if bucket.reserved < reserved_amount:
                    raise QuotaLedgerStateError(
                        "Quota reservation exceeds the bucket's reserved amount."
                    )
                bucket.reserved -= reserved_amount
                bucket.consumed += actual_amount

            reservation.actual_default_bucket_units = actual.default_bucket_units
            reservation.actual_search_query_calls = actual.search_query_calls
            reservation.status = "settled"
            reservation.settled_at = datetime.now(timezone.utc)

    def _insert_bucket_if_missing(
        self, session: Session, quota_day: date, bucket_name: str
    ) -> None:
        """Create a daily bucket row safely when concurrent calls initialize it."""
        values: dict[str, Any] = {
            "quota_day": quota_day,
            "bucket_name": bucket_name,
            "daily_limit": self._limits[bucket_name],
            "consumed": 0,
            "reserved": 0,
        }
        dialect = session.get_bind().dialect.name
        table = QuotaBucketUsage.__table__
        if dialect == "postgresql":
            statement = (
                pg_insert(table)
                .values(**values)
                .on_conflict_do_nothing(index_elements=["quota_day", "bucket_name"])
            )
        elif dialect == "sqlite":
            statement = (
                sqlite_insert(table)
                .values(**values)
                .on_conflict_do_nothing(index_elements=["quota_day", "bucket_name"])
            )
        else:
            raise RuntimeError(f"Quota ledger does not support database dialect {dialect!r}.")
        session.execute(statement)

    @staticmethod
    def _quota_day(now: datetime | None = None) -> date:
        """Use YouTube's Pacific-time quota reset date, including DST changes."""
        current = now or datetime.now(_QUOTA_TIMEZONE)
        return current.astimezone(_QUOTA_TIMEZONE).date()
