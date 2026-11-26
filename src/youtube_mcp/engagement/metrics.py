from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from statistics import median


@dataclass(frozen=True)
class DurationStats:
    count: int
    total_seconds: int
    average_seconds: float | None
    median_seconds: float | None
    distribution: dict[str, int]


def summarize_durations(durations_seconds: Iterable[int]) -> DurationStats:
    durations = list(durations_seconds)
    if any(duration < 0 for duration in durations):
        raise ValueError("Durations must be zero or greater.")

    buckets = Counter()
    for duration in durations:
        if duration < 5 * 60:
            buckets["under_5_minutes"] += 1
        elif duration < 15 * 60:
            buckets["5_to_under_15_minutes"] += 1
        elif duration < 30 * 60:
            buckets["15_to_under_30_minutes"] += 1
        elif duration < 60 * 60:
            buckets["30_to_under_60_minutes"] += 1
        else:
            buckets["60_minutes_or_more"] += 1

    count = len(durations)
    total = sum(durations)
    return DurationStats(
        count=count,
        total_seconds=total,
        average_seconds=round(total / count, 2) if count else None,
        median_seconds=median(durations) if count else None,
        distribution={
            label: buckets[label]
            for label in (
                "under_5_minutes",
                "5_to_under_15_minutes",
                "15_to_under_30_minutes",
                "30_to_under_60_minutes",
                "60_minutes_or_more",
            )
        },
    )
