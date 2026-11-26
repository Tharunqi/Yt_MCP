from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from youtube_mcp.quota.ledger import (
    QuotaBudgetExceededError,
    QuotaLedgerStateError,
    SQLAlchemyQuotaLedger,
)
from youtube_mcp.quota.preflight import QuotaEstimate


@pytest.fixture
def ledger() -> SQLAlchemyQuotaLedger:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return SQLAlchemyQuotaLedger(engine, standard_daily_limit=10, search_daily_limit=5)


def test_reservation_reduces_remaining_and_settlement_releases_unused_quota(
    ledger: SQLAlchemyQuotaLedger,
) -> None:
    reservation = ledger.check_and_reserve(QuotaEstimate(4, 2))

    reserved = ledger.remaining_today()
    assert reserved["standard"].remaining == 6
    assert reserved["standard"].reserved == 4
    assert reserved["search"].remaining == 3
    assert reserved["search"].reserved == 2

    reservation.settle(QuotaEstimate(2, 1))

    settled = ledger.remaining_today()
    assert settled["standard"].remaining == 8
    assert settled["standard"].consumed == 2
    assert settled["standard"].reserved == 0
    assert settled["search"].remaining == 4
    assert settled["search"].consumed == 1
    assert settled["search"].reserved == 0


def test_reservation_rejects_if_either_bucket_is_short_and_rolls_back_both(
    ledger: SQLAlchemyQuotaLedger,
) -> None:
    first = ledger.check_and_reserve(QuotaEstimate(8, 1))

    with pytest.raises(QuotaBudgetExceededError, match="standard"):
        ledger.check_and_reserve(QuotaEstimate(3, 2))

    state = ledger.remaining_today()
    assert state["standard"].reserved == 8
    assert state["search"].reserved == 1
    first.settle(QuotaEstimate(8, 1))


def test_reservation_rejects_search_bucket_exhaustion_without_spending_standard(
    ledger: SQLAlchemyQuotaLedger,
) -> None:
    first = ledger.check_and_reserve(QuotaEstimate(1, 4))

    with pytest.raises(QuotaBudgetExceededError, match="search"):
        ledger.check_and_reserve(QuotaEstimate(1, 2))

    state = ledger.remaining_today()
    assert state["standard"].reserved == 1
    assert state["search"].reserved == 4
    first.settle(QuotaEstimate(1, 4))


def test_settlement_is_idempotent_for_the_same_actual_usage(
    ledger: SQLAlchemyQuotaLedger,
) -> None:
    reservation = ledger.check_and_reserve(QuotaEstimate(2, 1))
    actual = QuotaEstimate(1, 1)

    reservation.settle(actual)
    reservation.settle(actual)

    state = ledger.remaining_today()
    assert state["standard"].consumed == 1
    assert state["search"].consumed == 1


def test_settlement_rejects_a_conflicting_second_result(ledger: SQLAlchemyQuotaLedger) -> None:
    reservation = ledger.check_and_reserve(QuotaEstimate(2, 1))
    reservation.settle(QuotaEstimate(1, 1))

    with pytest.raises(QuotaLedgerStateError, match="already settled differently"):
        reservation.settle(QuotaEstimate(2, 1))


def test_actual_usage_above_estimate_is_recorded_to_block_future_requests(
    ledger: SQLAlchemyQuotaLedger,
) -> None:
    reservation = ledger.check_and_reserve(QuotaEstimate(2, 1))
    reservation.settle(QuotaEstimate(3, 2))

    state = ledger.remaining_today()
    assert state["standard"].consumed == 3
    assert state["search"].consumed == 2
    assert state["standard"].remaining == 7
    assert state["search"].remaining == 3


def test_quota_day_follows_midnight_pacific_time() -> None:
    before_midnight_pt = datetime(2026, 11, 26, 7, 59, tzinfo=timezone.utc)
    at_midnight_pt = datetime(2026, 11, 26, 8, 0, tzinfo=timezone.utc)

    assert SQLAlchemyQuotaLedger._quota_day(before_midnight_pt).isoformat() == "2026-11-25"
    assert SQLAlchemyQuotaLedger._quota_day(at_midnight_pt).isoformat() == "2026-11-26"
