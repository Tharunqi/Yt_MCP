# FR-3 and FR-6 implementation prep

Source: YouTube_MCP_SRS_Super-dev.pdf, repository README, source tree, provider/auth code, and traceability notes reviewed on 2026-11-27.

Requirements: FR-3, FR-6.

## Scope

- **FR-3:** Recommend videos using the authorized user's likes, subscriptions, and selected playlists. Build the preference profile for the current request, rank with topic similarity, creator affinity, freshness, and diversity, exclude videos already liked or saved, and explain each recommendation.
- **FR-6:** Return available title, channel, description, category, publication date, and duration. Label the result as metadata-based; do not claim it summarizes spoken content.

## Repository findings

- The README reported FR-1, FR-2, FR-4, and implemented portions of FR-5 as current functionality before Session 2.
- The server registers tools that call feature logic through a provider and quota preflight.
- The authorized provider has methods for likes, subscriptions, playlist items by playlist ID, video search, and video details. Confirm how selected playlist IDs will be supplied before implementing FR-3.
- YouTube credential loading defaults to read-only access and checks granted scopes.

## Constraints to carry into implementation

- Use the official YouTube Data API through the provider boundary.
- Keep inferred profiles request-scoped; do not persist them.
- Account for the API limit of up to 1,000 liked videos.
- Use mocked or recorded data for automated checks. Never put credentials, tokens, or real personal data in notes or fixtures.

## Session 1 review

- **Worked:** Updated main, returned to feature/viraj-fr3-fr6, and confirmed the feature branch was clean. Mapped the feature modules, server pattern, provider methods, auth setup, and test locations.
- **Still to confirm:** How users select playlists and provide those playlist IDs to FR-3.

## Session 2: FR-6 implementation

- Added src/youtube_mcp/summarization/metadata_summary.py and registered the summarize_video_metadata MCP tool.
- The result includes available title, channel, description, category name and ID, publication date, and formatted plus original ISO-8601 duration. Missing values remain explicit. The result states that it is metadata-based and does not summarize spoken content.
- Added quota preflight for up to two standard API calls (video details and optional category-name lookup) and focused unit/integration test files. Updated the README, MCP tool reference, and traceability row.
- **Verification:** Python syntax parsing and git diff --check passed. Pytest and Ruff could not run in this environment: the repository virtual environment contains Linux executables, WSL has no installed distribution, and the bundled Python has neither pytest nor Ruff.
- **Verification update:** The corrected implementation passed GitHub CI in PR [#8](https://github.com/Tharunqi/Yt_MCP/pull/8).
- **Next:** Continue with FR-3. The selected-playlist input path remains to be confirmed.

## Session 3: FR-3 ranking core

- Added an ephemeral preference profile built from the request topic and current liked/saved video metadata. No inferred profile is persisted.
- Added a deterministic score with topic similarity (45%), creator affinity (25%), freshness (20%), and prior-interest overlap (10%). Liked/saved IDs are excluded, explanations are included, and channel repetition is limited for diversity.
- Added unit cases for profile inputs, ranking signals, exclusion, diversity, stable ties, and limit validation.
- **Verification:** GitHub CI passed on commit `4780721` in PR [#8](https://github.com/Tharunqi/Yt_MCP/pull/8). Local test execution remains unavailable without Python.
- **Stage review:** The ranking logic is isolated and deterministic. Account retrieval and the MCP tool remain; local execution of the test suite was unavailable. Continue by wiring those pieces through the existing OAuth, provider, and quota boundaries.
- **Next:** Add bounded authorized account retrieval, quota preflight, candidate searches/channel samples, and the MCP tool; update docs alongside that integration.

Related notes: [[brain/tharun/resources/second-brain-workflow]], [[docs/requirements/srs]], [[docs/traceability]].

PR: [#8](https://github.com/Tharunqi/Yt_MCP/pull/8). No GitHub issue ID has been created.

## Session 3 continued: FR-3 request workflow

- Added `recommend_videos` with read-only OAuth, optional user-selected playlist IDs, request-time profile construction, bounded topic search, optional samples from subscribed-channel uploads, liked/saved exclusions, ranking, and explanation output.
- Added request caps of 1,000 likes, 50 subscriptions, three selected playlists with 50 items each, 25 topic search candidates, and five sampled subscription channels with five uploads each. Added quota preflight estimates before OAuth/API work and request-scoped accounting for account-provider reads.
- Updated the tool reference, architecture, development plan, README, and FR-3 traceability. PR [#8](https://github.com/Tharunqi/Yt_MCP/pull/8) contains the earlier ranking and FR-6 work; this Session 3 branch still needs its own PR.
- **Worked:** The workflow uses the existing provider and OAuth boundaries; inferred profile data is held only for the request and is not returned or stored.
- **Still to verify:** Orchestration/MCP coverage, quota bounds, authorization, empty data, exclusions, and account API failures need focused checks before FR-3 is complete.
- **Next:** Add focused provider/service/MCP coverage, run the project's checks, and resolve any failures before opening a PR.
- Related notes: [[docs/requirements/srs]], [[docs/api/mcp-tools]], [[docs/traceability]].
