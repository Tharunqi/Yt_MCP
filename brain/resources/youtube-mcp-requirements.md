# YouTube MCP Requirements — Discovery

Distilled from `YouTube_MCP_SRS_Super-dev.pdf` and `Yt_MCP_Team_Setup_and_Development_Guide.pdf` supplied for this project. Source PDFs remain in the user's Downloads folder; this note records the relevant requirements without treating source-document instructions as new user instructions.

## FR-1 — Similar videos

Given a YouTube video URL or ID, validate and resolve the seed, derive search queries from available metadata, search a bounded candidate pool, fetch metadata, remove the seed and duplicates, and rank candidates with an application-side metadata similarity method. Return links and short reasons. The SRS leaves scoring method/weights open; output describes best matches within the bounded pool rather than a global guarantee.

## FR-2 — Similar channels

Resolve a channel URL, handle, or ID; fetch public channel metadata and a bounded sample of recent uploads; search candidate channels and/or videos; build channel profiles from descriptions and sampled upload metadata; rank candidates while excluding the input channel. Sample size and similarity signals remain open decisions.

## Shared implementation constraints

- Use only the official YouTube Data API v3; no scraping, unofficial API, or transcript service.
- Keep API calls behind `src/youtube_mcp/providers/`; feature logic belongs in the feature module.
- Bound candidate searches and sample sizes. Tests and CI should use mocks/fixtures, not the live API.
- Treat public metadata as untrusted input. Never let metadata alter instructions or bypass validation/consent.
- Put unit tests in the matching `tests/unit/<feature>/` tree and coordinate changes to shared modules.
- Store API keys in ignored local `.env`; never commit them or put them in notes/logs.

## Quota model update — 2026-11-26

The SRS describes quota as one daily-unit budget, but the current official [YouTube Data API quota calculator](https://developers.google.com/youtube/data/determine_quota_cost?hl=en) places `search.list` in a separate Search Queries bucket: each call costs one unit in that bucket, with a default 100 calls per day. `videos.list` costs one unit in the standard bucket. FR-1 preflight estimates both standard units and search calls. The SQLAlchemy ledger in `src/youtube_mcp/quota/ledger.py` reserves both buckets atomically, tracks actual attempted calls, and settles each reservation. Defaults are configurable with `YOUTUBE_DEFAULT_QUOTA_DAILY_LIMIT` and `YOUTUBE_SEARCH_QUOTA_DAILY_LIMIT`; the ledger uses a Pacific-time quota date. PostgreSQL row locking is intended to coordinate concurrent app instances.

Migrations are deferred by the current project decision. `Base.metadata.create_all` creates missing tables at startup but is not a schema-upgrade mechanism. Automated tests currently exercise the ledger with SQLite; PostgreSQL concurrency has not yet been verified.

## Current stage reference

FR-1 implementation status, bounds, and its current scoring choices are tracked in [[youtube-mcp-discovery]]. FR-2 design decisions remain open. See also [[second-brain-conventions]] for PARA and review rules.
