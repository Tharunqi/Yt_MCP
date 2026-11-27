# ADR-0003: Use SQLAlchemy with PostgreSQL for quota reservations

- **Status:** Accepted for current implementation; migrations deferred
- **Date:** 2026-11-27
- **Decision owner:** Sid
- **Requirement links:** NFR-QUOTA-01, NFR-QUOTA-02, NFR-QUOTA-03
- **Distilled Brain note:** [[brain/sid/resources/youtube-mcp-requirements#Quota model|quota model]]

## Context

Multiple application instances must avoid independently spending the same
remaining YouTube quota. The project already runs PostgreSQL through Docker
Compose. FR-1 `search.list` calls and other API calls are tracked in separate
quota buckets.

## Decision

Use a SQLAlchemy ledger with atomic reservations and settlements in the existing
PostgreSQL service. Track standard units and Search Queries calls separately,
preflight before provider calls, account for attempted API use, and use the
Pacific-time calendar date for daily limits. Create missing tables from model
metadata at startup until migrations are added.

## Consequences and limitations

The shared database coordinates reservations across processes when PostgreSQL
locking behaves as intended. Unit tests currently use SQLite; PostgreSQL
concurrency has not been verified. `create_all` is not a schema migration or
upgrade strategy. Production database topology, backups, and migrations remain
open decisions.
