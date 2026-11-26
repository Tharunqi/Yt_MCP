# YouTube MCP — Similar Video and Channel Discovery

- **Status:** Active; Sid's provider and FR-1 implementation have been restored on `sid-brain-separated` and need verification against the fetched `origin/main`.
- **Contributor:** [[brain/sid/Sid]]
- **Requirements:** [[brain/sid/resources/youtube-mcp-requirements#FR-1|FR-1]], [[brain/sid/resources/youtube-mcp-requirements#FR-2|FR-2]]
- **Issue:** TBD
- **PR:** TBD; changes should go through a reviewed pull request.

## Restored implementation

The provider in `src/youtube_mcp/providers/youtube.py` retains Tharun's `YouTubeDataProvider` for the existing FR-4/FR-5 tools and adds Sid's API-key-based `YouTubeProvider` for public metadata discovery. Sid's configuration, identifier parsing, and shared provider errors are in `src/youtube_mcp/common/`.

FR-1 is implemented in `src/youtube_mcp/discovery/similar_videos.py` and registered alongside the existing tools in `src/youtube_mcp/server.py`. It validates a video URL or ID, resolves the seed, builds up to three metadata-derived search queries, gathers a bounded candidate pool, removes the seed and duplicate IDs, and returns ranked results with short reasons. Ranking uses Jaccard overlap for title (45%), tags (30%), description (20%), and an exact category match (5%). Missing signals contribute zero; video ID breaks score ties deterministically.

Quota preflight and accounting use `src/youtube_mcp/quota/`. The SQLAlchemy ledger reserves the standard and Search Queries buckets atomically, tracks attempted calls, and settles reservations after success or failure. The quota day follows Pacific Time. PostgreSQL is the production locking target; ledger unit tests use SQLite. Tables are created from SQLAlchemy metadata because migrations are deferred.

Provider live tests are opt-in through `RUN_YOUTUBE_LIVE_TESTS=1` and require `YOUTUBE_API_KEY`. Unit and integration tests are restored in `tests/`. The earlier combined branch passed 32 tests with 3 live tests skipped, and Ruff passed. These checks have not yet been rerun against the newly fetched `origin/main`.

## Next work

1. Run the project test suite and Ruff on `sid-brain-separated` and resolve any integration issues with current FR-4/FR-5 code.
2. Verify PostgreSQL reservation and concurrency behavior before relying on it in deployment.
3. Decide how to inject `YOUTUBE_API_KEY` securely into the app container; the current Compose app environment only passes the database URL and MCP port.
4. Implement FR-2 channel-profile construction and ranking from bounded recent-upload samples, excluding the input channel.

## Review

- **Worked:** The restored provider and FR-1 code come from the previous branch that already combined FR-1 with Tharun's FR-4/FR-5 MCP tools and provider.
- **Not verified yet:** Tests and Ruff have not been rerun after restoring the code onto the latest `origin/main`; PostgreSQL concurrency has not been exercised.
- **Next change:** Verify this combined branch before committing, keep migrations deferred, and keep Sid's notes under `brain/sid/`.

See [[brain/sid/resources/youtube-mcp-requirements]] for distilled requirements and [[brain/sid/log]] for historical work records.
