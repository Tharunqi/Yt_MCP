# Research 09 — SQLAlchemy transaction boundaries

- **Source:** [SQLAlchemy 2.0 transaction management](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)
- **Reviewed:** 2026-11-27
- **Requirements:** NFR-QUOTA-03, TQ-6

## Distilled findings

- SQLAlchemy sessions maintain transaction state; explicit `Session.begin()`
  context managers commit on successful exit and roll back on exceptions.
- A session must be scoped to a bounded unit of work and closed/released after
  use to return connections to the pool.
- SQL transaction handling does not remove the need to verify database-specific
  locking and isolation semantics.

## Project implication

Quota reserve/update/settle operations need clear transaction boundaries and
rollback behavior. Exercise the actual PostgreSQL backend in concurrency tests;
SQLite unit tests do not prove production locking. See [[brain/sid/resources/youtube-mcp-requirements#Quota model|quota model]] and [[docs/adr/0003-sqlalchemy-quota-ledger]].
