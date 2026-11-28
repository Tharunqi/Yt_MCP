# Requirement Traceability

This is the project-level mapping from requirement to modules, tests, skill,
Brain evidence, and review tracking. Requirement details are in the
[SRS](requirements/srs.md); design choices are in [ADRs](adr/).

| Requirement | Code / owner | Verification currently present | Skill / Brain note | Issue / PR |
|---|---|---|---|---|
| FR-1 | `discovery/similar_videos.py`, `providers/`, `quota/`; Sid | `tests/unit/discovery/test_similar_videos.py`; `tests/integration/test_discovery_mcp.py`; provider live tests are network-blocked in this environment | `youtube-provider-live-check`; [[brain/sid/projects/youtube-mcp-discovery]] | Not created |
| FR-2 | `discovery/similar_channels.py`, provider; Sid | `tests/unit/discovery/test_similar_channels.py`; provider tests; `tests/integration/test_discovery_mcp.py`; opt-in channel-search smoke added | `youtube-provider-live-check`; [[brain/sid/projects/youtube-mcp-discovery]] | Not created |
| FR-3 | `recommendations/personalized.py`, `recommendations/service.py`, `auth/`, `providers/`, `quota/`; Viraj | Ranking and service unit tests in `tests/unit/recommendations/`; MCP orchestration coverage in `tests/integration/test_recommendations_mcp.py`; GitHub CI passed on merged branch `ba3e2bb` | `recommend_videos`; shared requirements in [[brain/sid/resources/youtube-mcp-requirements]] and [[brain/viraj/projects/fr3-fr6-prep]] | PR [#11](https://github.com/Tharunqi/Yt_MCP/pull/11) draft; PR #8 merged |
| FR-4 | `engagement/`, `auth/`, `quota/`; Tharun | `tests/unit/engagement/`; `tests/unit/test_server.py`; `tests/unit/quota/test_preflight.py` covers bounded estimate and reject-before-fetch; live read passed | [[brain/tharun/projects/youtube-mcp]]; [[brain/tharun/projects/fr4-fr5-design]] | PR #3 merged |
| FR-5 | `playlists/`, `auth/`, `quota/`; Tharun | `tests/unit/playlists/`; `tests/unit/test_youtube_playlist_provider.py` checks search/write costs; `tests/unit/quota/test_preflight.py`; preview and confirmed creation passed (owner confirmed) | [[brain/tharun/projects/youtube-mcp]]; [[brain/tharun/projects/fr4-fr5-design]] | PR #3 merged |
| FR-6 | `summarization/`, `providers/`; Viraj | `tests/unit/summarization/test_metadata_summary.py`; `tests/unit/providers/test_youtube_provider.py`; `tests/integration/test_summarization_mcp.py` | Metadata-only summary tool; shared requirements in [[brain/sid/resources/youtube-mcp-requirements]] | Not created |
| FR-7 | `analytics/`, `providers/`, `quota/`; Tharun | `tests/unit/analytics/` covers playlist/video summaries, duplicates, missing metadata, empty playlists, validation and tool quota checks; `tests/unit/quota/test_preflight.py` covers both estimates; playlist and video tools passed live checks | [[brain/tharun/projects/fr7-playlist-analysis]]; [[brain/tharun/projects/youtube-mcp]] | [Issue #9](https://github.com/Tharunqi/Yt_MCP/issues/9); [PR #10](https://github.com/Tharunqi/Yt_MCP/pull/10) |
| SK-1 | `skills/video-to-playlist/`; shared | FR-6 and FR-7 tools exist, but the complete product skill workflow has not been run | Product skill and [[brain/tharun/resources/second-brain-workflow]] | Team tracking pending |
| NFR-QUOTA-01–03 | `quota/`, `database/`; Sid | `tests/unit/quota/test_ledger.py`, `tests/unit/quota/test_preflight.py`, and feature tests for FR-1/2/3/4/5/6/7; PostgreSQL concurrency remains untested | [[brain/sid/resources/youtube-mcp-requirements#Quota model|quota note]]; ADR-0003; [[brain/tharun/projects/fr4-fr5-design]] | Not created |
| NFR-MAINT-01 / COMP-01 | `providers/`; team | Provider unit tests with fakes; docs validation | `local-check`; ADR-0001 | Not created |
| NFR-SEC-01–04 / PRIV-01 | `auth/`, provider, playlist server; team | Unit tests cover some OAuth and confirmation paths; full SEC-T review pending | `youtube-provider-live-check`; ADR-0004 | Not created |
| NFR-COMP-03 | Product policy and privacy; team | Official policy research recorded; team review not completed | [[brain/sid/resources/research-07-youtube-policy]] | Not created |
| NFR-REL-01/02 | playlist/provider error handling; team | Playlist unit tests cover partial failure and missing channel; broader API-error matrix pending | `local-check`; owner project note | Not created |
| NFR-OPS-01 / CI-T | Docker Compose and CI; team | CI runs build, Ruff, pytest, secret scan and docs checks; full local stack smoke not recorded | `local-check`; [[brain/sid/resources/second-brain-conventions]] | Not created |
| NFR-TEST-01–03 / TQ-1–8 | tests, CI, testing docs; team | Unit/integration pass locally; no complete FR-1–7 MCP E2E; TQ-7 results in `testing/skill-evaluations.md` | Skills and contributor Brain logs | Not created |
| REV-T / SB-5 | branch/PR process; all | FR-3 is in draft PR #11 with CI passed on the implementation commit; maintainer review is pending. FR-7 was delivered in PR #10. | [[brain/sid/areas/team-collaboration]] | [PR #11](https://github.com/Tharunqi/Yt_MCP/pull/11); [PR #10](https://github.com/Tharunqi/Yt_MCP/pull/10) |

## Evidence limits

The 2026-11-28 final check invoked FR-4, FR-5 preview/refusal, and FR-7
playlist/video analysis through the live MCP server. The owner also confirmed
the earlier FR-5 playlist creation succeeded in their account. No new playlist
was created during the final check. PostgreSQL concurrency, production OAuth
security, and a full FR-1–FR-7 / SK-1 E2E remain unverified.

## Example end-to-end trace (FR-1)

`[[brain/sid/resources/youtube-mcp-requirements#FR-1|FR-1 distilled requirement]]`
→ [ADR-0002](adr/0002-fr1-metadata-ranking.md)
→ `src/youtube_mcp/discovery/similar_videos.py`
→ `tests/unit/discovery/test_similar_videos.py` and
`tests/integration/test_discovery_mcp.py`
→ [[brain/sid/projects/youtube-mcp-discovery]].

The corresponding GitHub Issue and reviewed PR are not created yet, so the
trace is incomplete for the issue/PR links required by the broader project
traceability workflow.
