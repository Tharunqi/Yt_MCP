# YouTube MCP

## Similar video and channel discovery

### Current status — 2026-11-25

First implementation slice establishes the public YouTube Data API v3 provider boundary for the planned similar-video and similar-channel features. It is intended as the first of five focused commits.

- `src/youtube_mcp/common/config.py` reads `YOUTUBE_API_KEY`, `YOUTUBE_MAX_SEARCH_RESULTS` (default 25), and `YOUTUBE_MAX_UPLOAD_SAMPLE` (default 20). Result limits are capped at 50.
- `src/youtube_mcp/common/identifiers.py` parses YouTube video IDs/URLs and channel IDs, handles, and `/user/` URLs.
- `src/youtube_mcp/common/errors.py` defines shared validation, not-found, and API error types.
- `src/youtube_mcp/providers/youtube.py` provides typed video/channel metadata and methods for video/channel details, bounded candidate searches, and bounded recent-upload sampling. The API client can be injected for isolated tests.
- `.env.example` documents the YouTube settings. Keep the actual API key in the ignored local `.env`; never put it in notes or commits.

### Verification

- `python -m pytest -q`: 8 passed. Tests use a fake API client; no live YouTube API calls were made.
- Ruff lint and format checks pass for the changed Python files.
- This is a local branch commit; it has not been pushed to GitHub.

### Next slices

1. Implement metadata-based similar-video ranking over bounded candidates, excluding the seed and duplicates; document the initial scoring choice because the SRS leaves it open.
2. Implement channel profile construction and candidate ranking from public channel metadata and sampled uploads; exclude the input channel.
3. Expose discovery functions as MCP tools, then add MCP/integration coverage and usage documentation.

### Open decisions

- Similar-video scoring signals and weights.
- Similar-channel profile signals and sample size.
- Handle/channel URL coverage beyond channel IDs, handles, and legacy `/user/` URLs.
