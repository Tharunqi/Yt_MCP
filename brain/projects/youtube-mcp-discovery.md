# YouTube MCP — Similar Video and Channel Discovery

- **Status:** Active; FR-1 implementation is complete and awaiting PR review. FR-2 is not implemented.
- **Deadline:** TBD; confirm before scheduling the next stages.
- **Contributor:** [[Sid]]
- **Requirements:** [[youtube-mcp-requirements#FR-1|FR-1]], [[youtube-mcp-requirements#FR-2|FR-2]]
- **Issue:** TBD
- **PR:** TBD (brain and code changes must enter through a reviewed PR per [[second-brain-conventions]]).

## Current implementation

The provider foundation in `src/youtube_mcp/` supplies environment-backed YouTube API settings, identifier parsing, shared provider errors, typed public metadata, and an injectable client for official YouTube Data API v3 reads. It supports video/channel details, bounded searches, and recent-upload sampling. Live provider smoke tests are opt-in and pass on Sid's local machine when enabled with a valid key.

FR-1 is implemented in `src/youtube_mcp/discovery/similar_videos.py` and registered in `src/youtube_mcp/server.py`. It validates the seed locally, builds up to three metadata-derived queries, fetches the seed, searches a bounded candidate pool, removes the seed and duplicate IDs, and returns ranked results with short reasons. Ranking uses token-set Jaccard overlap (title 45%, tags 30%, description 20%) plus exact category match (5%); missing signals contribute zero, and video ID is the deterministic tie-breaker. These are the current implementation choices for the open scoring details in [[youtube-mcp-requirements#FR-1|FR-1]].

The MCP tool accepts a video URL or ID plus `max_results` (1-25). Results include seed metadata, query strings, and candidate IDs, titles, channels, durations, scores, explanations, and watch links. Search and candidate limits keep the external work bounded.

The quota preflight is backed by `src/youtube_mcp/quota/ledger.py` and SQLAlchemy models in `src/youtube_mcp/database/models.py`. It reserves both standard and Search Queries capacity atomically, records attempted API calls by bucket, and settles actual usage after success or failure. The default daily limits are configurable. The quota day follows midnight Pacific Time. PostgreSQL is the production locking target; unit tests currently use SQLite. Tables are created with SQLAlchemy metadata at startup because migrations are deferred. See [[youtube-mcp-requirements]].

Unit and integration coverage lives in `tests/unit/` and `tests/integration/`; quota ledger tests use an in-memory SQLite database. Optional public-data smoke tests are in `tests/live/test_youtube_provider_live.py`; they require `YOUTUBE_API_KEY` plus `RUN_YOUTUBE_LIVE_TESTS=1`, and normal pytest runs skip them. Sid confirmed these provider tests pass locally when enabled. The current full suite reports 32 passed and 3 skipped, and Ruff passes. PostgreSQL concurrency and the complete FR-1 flow against live services remain unverified.

The local `.env` key was rotated after an earlier failed HTTP diagnostic exposed it in a request URL. The key itself is not recorded here. Keep `.env` ignored and out of commits. Docker Compose currently injects the database URL but not `YOUTUBE_API_KEY`; provide the key securely in the runtime environment when the container needs YouTube API access.

## Next stages

1. Push branch `sid` to the selected remote and open a reviewed PR for FR-1.
2. Run PostgreSQL-backed reservation/concurrency verification before relying on the ledger in deployment.
3. Decide how to inject `YOUTUBE_API_KEY` into the app container for deployments that use Compose.
4. Implement FR-2 channel profile construction and ranking from bounded recent-upload samples; exclude the input channel.
5. Update acceptance evidence and issue/PR links when those identifiers exist.

## Open decisions

- FR-2 channel profile signals, upload sample size, candidate limit, and tie-breaking.
- Identifier support for channel URLs beyond channel IDs, handles, and legacy `/user/` URLs.

## Stage review

- **Worked:** FR-1 now has an MCP tool, bounded provider orchestration, explainable deterministic ranking, and a persistent two-bucket quota reservation/settlement path. Unit/integration tests and Ruff pass.
- **Did not work:** The ledger has not been exercised against PostgreSQL concurrency, and live tests do not cover the full FR-1 flow.
- **Change next:** Commit and publish the reviewed FR-1 change, then verify PostgreSQL-backed concurrency before relying on it in deployment; keep migrations deferred as decided.

See [[youtube-mcp-requirements]] for the distilled SRS constraints and [[log]] for stage reviews.
