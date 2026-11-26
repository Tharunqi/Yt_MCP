# Work Log

Keep one entry per commit and fold intermediate implementation checkpoints
into that stage review. The FR-4/FR-5 live-check details are retained in
[[brain/tharun/projects/ai-session-2026-11-26-fr4-fr5-live-check]].

## 2026-11-25 — Commit 1: YouTube provider foundation

**Commit:** `8b6fbf7` — `feat: add YouTube provider`.

**Worked:** Added the official YouTube Data API provider boundary, environment-backed API key settings, video/channel identifier parsing, shared errors, typed public metadata, and fake-client unit tests. The provider supports video and channel details, bounded searches, and recent-upload sampling. Unit tests and Ruff passed.

**Did not work:** Live API behavior was not exercised in this commit; provider coverage used a fake client. FR-1 discovery was not implemented.

**Change for next stage:** Add explicitly opt-in live smoke tests while keeping ordinary tests and CI independent of YouTube availability.

Related: [[brain/sid/projects/youtube-mcp-discovery]], [[brain/sid/resources/youtube-mcp-requirements#FR-1|FR-1]], [[brain/sid/resources/youtube-mcp-requirements#FR-2|FR-2]].

## 2026-11-25 — Commit 2: live tests and Second Brain foundation

**Commit:** `4f66b54` — `docs: organize second brain and add live API tests`.

**Worked:** Added three opt-in public-data smoke tests for video details, channel details, and recent uploads. Established the PARA brain structure, entry point, distilled requirements and conventions, project and area notes, workflow skills, and root `AGENTS.md`. Sid later confirmed the live tests passed after setting `RUN_YOUTUBE_LIVE_TESTS=1` and rotating the API key.

**Did not work:** Live tests intentionally skip without the opt-in flag. An earlier failed request exposed the API key in a request URL; Sid rotated the key, and test failures now suppress request details. No issue or PR identifiers were available. Tharun and Viraj author their own contributor notes.

**Change for next stage:** Implement FR-1 as bounded metadata search and ranking, with quota preflight before API access. Keep live calls optional and secrets out of tracked files.

Related: [[brain/sid/projects/youtube-mcp-discovery]], [[brain/sid/resources/youtube-mcp-requirements]], [[brain/sid/index]], [[brain/sid/areas/team-collaboration]], [[brain/sid/resources/second-brain-conventions]].

## 2026-11-26 — Commit 3: FR-1 implementation

**Worked:** Completed the FR-1 MCP flow: seed validation, metadata-derived queries, bounded candidate collection, duplicate and seed removal, deterministic weighted ranking with reasons, and structured tool output. Added atomic SQLAlchemy quota reservations for separate standard and Search Queries buckets using the existing PostgreSQL service, per-request attempted-call accounting, settlement on success or failure, and Pacific-time quota days. Normal verification reports 32 passed and 3 opt-in live tests skipped; Ruff passes. Sid confirmed the provider live tests pass when explicitly enabled.

**Did not work:** Automated ledger tests use SQLite; PostgreSQL concurrency has not been verified against the running service. The ledger creates missing tables with SQLAlchemy metadata because migrations are deferred. Live tests cover the provider, not the complete FR-1 flow with PostgreSQL. Issue and PR identifiers remain TBD.

**Change for next stage:** Sync branch `sid` with `main`, preserve parallel FR-4/FR-5 work during conflict resolution, and submit the combined changes for review. Verify the ledger against PostgreSQL before relying on it in deployment. Keep the API key out of the container image and tracked files; inject it through the runtime environment when needed.

Related: [[brain/sid/projects/youtube-mcp-discovery]], [[brain/sid/resources/youtube-mcp-requirements#FR-1|FR-1]], [[brain/sid/resources/youtube-mcp-requirements#Quota model|Quota model]], [[brain/tharun/projects/ai-session-2026-11-26-fr4-fr5-live-check]], [[brain/sid/resources/second-brain-conventions]].
