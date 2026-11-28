# Project log

## 2026-11-27 - FR-3 and FR-6 implementation preparation

- Updated local main from origin/main, switched back to feature/viraj-fr3-fr6, and fast-forwarded the feature branch. The working tree was clean afterward.
- Reviewed AGENTS.md, the README, traceability, the server tool pattern, provider methods, authentication code, and the feature test folders.
- FR-3 and FR-6 implementation folders and unit-test folders existed but contained only placeholders.
- The authorized provider supports likes, subscriptions, and playlist items when given a playlist ID. How selected playlist IDs are supplied remains to be confirmed.
- Git displayed directory deletion retry prompts while switching branches. The prompts were declined, and Git completed the switch; the subsequent status check was clean.
- **Review:** The project structure and implementation boundaries are clear. No source code was changed in Session 1.
- Related notes: [[brain/viraj/projects/fr3-fr6-prep]], [[brain/tharun/resources/second-brain-workflow]].

## 2026-11-27 - FR-6 metadata summary

- Implemented and registered the summarize_video_metadata MCP tool on feature/viraj-fr3-fr6.
- Added request-time validation, quota preflight/accounting for video details and optional category-name lookup, explicit missing values, readable duration, and a notice that the result uses metadata only and does not summarize spoken content.
- Added focused unit and MCP integration test files. Updated the README, MCP tool reference, and requirement traceability.
- **Worked:** The existing provider supplies the required fields through the official API, and the new tool follows the server's provider/quota pattern.
- **Could not verify:** Pytest and Ruff could not run because this Windows session cannot execute the repository's Linux .venv; WSL has no distribution, and bundled Python lacks those packages. AST parsing and git diff --check passed.
- **Verification update:** PR [#8](https://github.com/Tharunqi/Yt_MCP/pull/8) passed GitHub CI after correcting the quota test reference and replacing an 11-character syntactically valid ID in the invalid-ID test.
- **Next:** Continue FR-3 by confirming the selected-playlist input contract and integrating the request-time ranker with authorized account data.
- Related notes: [[brain/viraj/projects/fr3-fr6-prep]], [[brain/tharun/resources/second-brain-workflow]].

## 2026-11-27 - FR-3 ranking core

- Confirmed `origin/main` had not advanced before starting the FR-3 work.
- Added a request-scoped preference profile and deterministic ranking core in `src/youtube_mcp/recommendations/personalized.py`. It scores topic overlap, creator affinity, freshness, and liked/saved metadata overlap; excludes liked and selected-playlist video IDs; limits repeated creators; and gives short reasons.
- Added focused unit cases in `tests/unit/recommendations/test_personalized.py` for profile construction, ranking signals, exclusions, diversity, stable ordering, and invalid bounds.
- **Verification:** `git diff --check` passed. GitHub CI passed on commit `4780721` for PR [#8](https://github.com/Tharunqi/Yt_MCP/pull/8). Local Python tests were unavailable because Python is not installed in this Windows environment.
- **Stage review:** The pure ranking layer is isolated and deterministic. Account retrieval and the MCP tool remain incomplete; local test execution was unavailable. Next session should wire those layers through the existing OAuth/provider and quota boundaries.
- **Next:** Integrate account data and bounded candidate acquisition with the OAuth and quota patterns; wire the MCP tool and update shared docs.
- Related notes: [[brain/viraj/projects/fr3-fr6-prep]], [[docs/requirements/srs]], [[docs/traceability]].

## 2026-11-28 - FR-3 request workflow integration

- Started from updated `main` at merge commit `b4912ce` on branch `feature/viraj-fr3-integration`.
- Added a request-time recommendation service and registered the `recommend_videos` MCP tool. It reads bounded likes, subscriptions, and explicitly selected playlists; optionally samples subscribed-channel uploads; fetches metadata; ranks and explains candidates; and excludes liked/saved video IDs.
- Added fail-closed quota reservation estimates and request-scoped API-call accounting, then updated shared FR-3 documentation and traceability.
- **Worked:** Existing OAuth/provider abstractions supported the integration without persisting inferred profiles or requesting playlist-write access.
- **Could not verify yet:** Orchestration/MCP tests have not been added or run. Quota edge cases and provider/API error behavior need focused checks before the PR.
- **Next:** Add focused tests and execute build, Ruff, docs validation, and pytest when the supported Python environment is available.
- Related notes: [[brain/viraj/projects/fr3-fr6-prep]], [[docs/requirements/srs#FR-3]], [[docs/api/mcp-tools]], [[docs/traceability]].

## 2026-11-28 - FR-3 workflow verification and draft review

- Added unit coverage for request orchestration, bounded account reads, selected-playlist inputs, exclusions, quota settlement, invalid requests, and provider failures.
- Added MCP integration coverage for tool registration, successful explained recommendations, authorization denial, and quota rejection before OAuth.
- Review found that unavailable subscription channels could allow more than five channel lookups; capped lookup attempts at five to match the quota estimate and added a regression assertion.
- Updated test-plan, development-plan, and traceability evidence. Opened draft PR [#11](https://github.com/Tharunqi/Yt_MCP/pull/11).
- **Worked:** The service now limits lookup attempts consistently with reserved quota, and deterministic tests cover the main success and failure paths.
- **Could not verify locally:** No Python interpreter is installed in this environment, so pytest, Ruff, package build, and repository-doc validation could not run. `git diff --check` passed; GitHub CI must execute the suite.
- **Next:** Review CI results and fix any failures before marking PR #11 ready for review.
- Related notes: [[brain/viraj/projects/fr3-fr6-prep]], [[docs/requirements/srs#FR-3]], [[docs/testing/test-plan]], [[docs/traceability]].
