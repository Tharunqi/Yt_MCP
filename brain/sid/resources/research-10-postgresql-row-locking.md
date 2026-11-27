# Research 10 — PostgreSQL explicit row locking

- **Source:** [PostgreSQL explicit locking](https://www.postgresql.org/docs/current/explicit-locking.html)
- **Reviewed:** 2026-11-27
- **Requirements:** NFR-QUOTA-03, TQ-6

## Distilled findings

- PostgreSQL provides row-locking clauses such as `FOR UPDATE` to coordinate
  transactions that update shared rows.
- Conflicting operations wait until the locking transaction commits or rolls
  back; isolation and lock order affect behavior.
- Locks do not by themselves prove the application is race-free; the full
  reserve/settle transaction must be exercised concurrently.

## Project implication

The quota ledger's PostgreSQL locking is a design intent until verified with
concurrent integration tests. Keep the open verification item in ADR-0003 and
the [defect/risk log](../../docs/testing/defect-log.md).
