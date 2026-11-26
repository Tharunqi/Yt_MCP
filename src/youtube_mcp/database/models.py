"""SQLAlchemy models for shared application database records."""

from datetime import date, datetime, timezone

from sqlalchemy import CheckConstraint, Date, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base metadata used to create the application's tables."""


class QuotaBucketUsage(Base):
    """Daily consumed and reserved quota for one YouTube quota bucket."""

    __tablename__ = "quota_bucket_usage"
    __table_args__ = (
        CheckConstraint("daily_limit > 0", name="ck_quota_bucket_positive_limit"),
        CheckConstraint("consumed >= 0", name="ck_quota_bucket_consumed_nonnegative"),
        CheckConstraint("reserved >= 0", name="ck_quota_bucket_reserved_nonnegative"),
    )

    quota_day: Mapped[date] = mapped_column(Date, primary_key=True)
    bucket_name: Mapped[str] = mapped_column(String(40), primary_key=True)
    daily_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    consumed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reserved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class QuotaReservationRecord(Base):
    """Per-workflow quota estimate and final recorded usage."""

    __tablename__ = "quota_reservation"
    __table_args__ = (
        CheckConstraint(
            "estimated_default_bucket_units >= 0",
            name="ck_quota_reservation_estimated_default_nonnegative",
        ),
        CheckConstraint(
            "estimated_search_query_calls >= 0",
            name="ck_quota_reservation_estimated_search_nonnegative",
        ),
        CheckConstraint(
            "actual_default_bucket_units IS NULL OR actual_default_bucket_units >= 0",
            name="ck_quota_reservation_actual_default_nonnegative",
        ),
        CheckConstraint(
            "actual_search_query_calls IS NULL OR actual_search_query_calls >= 0",
            name="ck_quota_reservation_actual_search_nonnegative",
        ),
    )

    request_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    quota_day: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    estimated_default_bucket_units: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_search_query_calls: Mapped[int] = mapped_column(Integer, nullable=False)
    actual_default_bucket_units: Mapped[int | None] = mapped_column(Integer)
    actual_search_query_calls: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="reserved")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
