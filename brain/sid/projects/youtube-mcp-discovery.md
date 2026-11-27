# YouTube MCP — Similar Video and Channel Discovery

- **Status:** Active on branch `siddharth`; FR-1 and FR-2 are present alongside shared FR-4/FR-5 code. Local automated tests and Ruff passed on 2026-11-27. This work remains uncommitted and needs PR review.
- **Contributor:** [[brain/sid/Sid]]
- **Requirements:** [[brain/sid/resources/youtube-mcp-requirements#FR-1|FR-1]], [[brain/sid/resources/youtube-mcp-requirements#FR-2|FR-2]]
- **Issue:** TBD
- **PR:** TBD; changes should go through a reviewed pull request.

## Restored implementation

The provider in `src/youtube_mcp/providers/youtube.py` retains Tharun's `YouTubeDataProvider` for the existing FR-4/FR-5 tools and adds Sid's API-key-based `YouTubeProvider` for public metadata discovery. Sid's configuration, identifier parsing, and shared provider errors are in `src/youtube_mcp/common/`.

FR-1 is implemented in `src/youtube_mcp/discovery/similar_videos.py` and registered alongside the existing tools in `src/youtube_mcp/server.py`. It validates a video URL or ID, resolves the seed, builds up to three metadata-derived search queries, gathers a bounded candidate pool, removes the seed and duplicate IDs, and returns ranked results with short reasons. Ranking uses Jaccard overlap for title (45%), tags (30%), description (20%), and an exact category match (5%). Missing signals contribute zero; video ID breaks score ties deterministically.

Quota preflight and accounting use `src/youtube_mcp/quota/`. The SQLAlchemy ledger reserves the standard and Search Queries buckets atomically, tracks attempted calls, and settles reservations after success or failure. The quota day follows Pacific Time. PostgreSQL is the production locking target; ledger unit tests use SQLite. Tables are created from SQLAlchemy metadata because migrations are deferred.

Provider and MCP live checks are opt-in through `RUN_YOUTUBE_LIVE_TESTS=1` and require `YOUTUBE_API_KEY`. On 2026-11-27, the automated suite reported 68 passed and 5 skipped; Ruff and repository documentation validation passed. After refining FR-2 queries, the live MCP test for `8vRhCUPB6Jk` returned ten similar videos and nine similar channels for TheCubicle. Package build and Docker MCP smoke remain unverified. See [[brain/sid/log]] and [[docs/testing/test-plan]].

### FR-2 channel-level revision

FR-2 accepts a channel URL, handle, or ID. Its live check now uses a direct
channel URL (`https://www.youtube.com/@gameranxTV`) independently from the FR-1
video seed. The earlier combined live check derived the channel ID from a video
before calling FR-2, which obscured the actual tool input. The revised profile
samples ten uploads, prioritizes the channel description and terms recurring
across uploads, and uses isolated upload terms as a smaller fallback signal.
Weights are title 10%, description 45%, recurring upload terms 30%, and all
sampled upload terms 15%. This remains lexical metadata similarity; it cannot
infer content format beyond terms present in the profile. The live run with
`safeSearch=none` produced queries `we make videos video games` and `gta things
we do game`; its ten results still included a kids' gaming channel. This is not
a same-query comparison with YouTube's default safety setting, so it does not
isolate the effect of `safeSearch`.

## Next work

1. Have the team review and commit this branch through a PR; create GitHub Issues from [[docs/development-plan]].
2. Verify PostgreSQL reservation and concurrency behavior before relying on it in deployment.
3. Verify the `.env`-provided API key is available to the app container without appearing in logs, CI, or committed files.
4. Run the revised FR-2 check against representative channel URLs and evaluate whether description and recurring upload signals distinguish creator format from one-off topics.

## Review

- **Worked:** The restored provider and FR-1 code come from the previous branch that already combined FR-1 with Tharun's FR-4/FR-5 MCP tools and provider.
- **Worked:** Automated suite (68 passed, 5 live skipped), Ruff, and documentation validation pass on this branch. Ten official-source research notes and shared engineering docs are linked from [[brain/sid/index]].
- **Worked:** FR-2 now has a bounded channel profile/search/rank MCP flow, quota estimation, unit/provider/integration coverage, and ADR-0005.
- **Not verified yet:** Live API calls work and FR-2 now returns channel candidates; lower-scoring matches and FR-1 sponsor-description noise still need quality review. Package build, Docker/MCP smoke, PostgreSQL concurrency, and policy review remain open.
- **FR-2 review:** The prior GTA-focused output showed that one-off topics can dominate channel matches. The revised scoring emphasizes channel description and recurring upload terms; the direct-channel live check is pending.
- **Next change:** Review discovery quality against representative channel URLs, then run Docker/PostgreSQL verification and submit the branch through a PR.

See [[brain/sid/resources/youtube-mcp-requirements]] for distilled requirements and [[brain/sid/log]] for historical work records.
