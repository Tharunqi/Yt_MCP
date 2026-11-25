# YouTube MCP — Similar Video and Channel Discovery

- **Status:** Active; provider foundation implemented.
- **Deadline:** TBD; confirm before scheduling the next stages.
- **Contributor:** [[Sid]]
- **Requirements:** [[youtube-mcp-requirements#FR-1|FR-1]], [[youtube-mcp-requirements#FR-2|FR-2]]
- **Issue:** TBD
- **PR:** TBD (brain and code changes must enter through a reviewed PR per [[second-brain-conventions]]).

## Current implementation

The provider foundation in `src/youtube_mcp/` supplies environment-backed YouTube API settings, identifier parsing, shared provider errors, typed public metadata, and an injectable client for official YouTube Data API v3 reads. It supports video/channel details, bounded searches, and recent-upload sampling.

The isolated unit tests are in `tests/unit/providers/test_youtube_provider.py`. Optional public-data smoke tests are in `tests/live/test_youtube_provider_live.py`; they require `YOUTUBE_API_KEY` plus `RUN_YOUTUBE_LIVE_TESTS=1`, and normal pytest runs skip them. Sid confirmed the live tests passed after the API key was rotated. The Codex execution environment's initial live run could not resolve Google's API host due to its network restriction.

The local `.env` key was rotated after an earlier failed HTTP diagnostic exposed it in a request URL. The key itself is not recorded here. Keep `.env` ignored and out of commits.

## Next stages

1. Implement FR-1 metadata query construction and deterministic candidate ranking; document the chosen signals and weights.
2. Implement FR-2 channel profile construction and ranking from bounded recent-upload samples; exclude the input channel.
3. Register discovery tools over MCP and add interface/integration coverage.
4. Review the full flow and update acceptance evidence before the PR.

## Open decisions

- FR-1 similarity signals, scoring method, weights, tie-breaking, and candidate limit.
- FR-2 channel profile signals, upload sample size, candidate limit, and tie-breaking.
- Identifier support for channel URLs beyond channel IDs, handles, and legacy `/user/` URLs.

See [[youtube-mcp-requirements]] for the distilled SRS constraints and [[log]] for stage reviews.
