# Requirement Traceability

This is the project-level mapping from requirement to modules, tests, skill,
Brain evidence, and review tracking. **Not created** means the team still needs a
GitHub Issue/PR; no identifiers are fabricated. Requirement details are in the
[SRS](requirements/srs.md); design choices are in [ADRs](adr/).

| Requirement | Code / owner | Verification currently present | Skill / Brain note | Issue / PR |
|---|---|---|---|---|
| FR-1 | `discovery/similar_videos.py`, `providers/`, `quota/`; Sid | `tests/unit/discovery/test_similar_videos.py`; `tests/integration/test_discovery_mcp.py`; provider live tests are network-blocked in this environment | `youtube-provider-live-check`; [[brain/sid/projects/youtube-mcp-discovery]] | Not created |
| FR-2 | `discovery/similar_channels.py`, provider; Sid | `tests/unit/discovery/test_similar_channels.py`; provider tests; `tests/integration/test_discovery_mcp.py`; opt-in channel-search smoke added | `youtube-provider-live-check`; [[brain/sid/projects/youtube-mcp-discovery]] | Not created |
| FR-3 | `recommendations/personalized.py`, `recommendations/service.py`, `auth/`, `providers/`, `quota/`; Viraj | Ranking and service unit tests in `tests/unit/recommendations/`; MCP orchestration coverage in `tests/integration/test_recommendations_mcp.py`; execution pending CI | `recommend_videos`; shared requirements in [[brain/sid/resources/youtube-mcp-requirements]] and [[brain/viraj/projects/fr3-fr6-prep]] | PR [#11](https://github.com/Tharunqi/Yt_MCP/pull/11) draft; PR #8 merged |
| FR-4 | `engagement/`, `auth/`; Tharun | `tests/unit/engagement/`; `tests/unit/test_server.py`; live account check documented by owner | Owner-maintained [[brain/tharun/projects/youtube-mcp]] | Not created |
| FR-5 | `playlists/`, `auth/`; Tharun | `tests/unit/playlists/`; `tests/unit/test_youtube_playlist_provider.py`; prior live preview in owner note | Owner-maintained [[brain/tharun/projects/youtube-mcp]] | Not created |
| FR-6 | `summarization/`, `providers/`; Viraj | `tests/unit/summarization/test_metadata_summary.py`; `tests/unit/providers/test_youtube_provider.py`; `tests/integration/test_summarization_mcp.py` | Metadata-only summary tool; shared requirements in [[brain/sid/resources/youtube-mcp-requirements]] | Not created |
| FR-7 | `analytics/`; Tharun | No feature tests identified | Owner-maintained [[brain/tharun/projects/youtube-mcp]] | Not created |
| SK-1 | `skills/video-to-playlist/`; shared | Skill evaluation and MCP E2E still blocked on FR-6/FR-7 implementation | Product skill and [[brain/tharun/resources/second-brain-workflow]] | Not created |
| NFR-QUOTA-01–03 | `quota/`, `database/`; Sid | `tests/unit/quota/test_ledger.py`; no PostgreSQL concurrency test yet | [[brain/sid/resources/youtube-mcp-requirements#Quota model|quota note]]; ADR-0003 | Not created |
| NFR-MAINT-01 / COMP-01 | `providers/`; team | Provider unit tests with fakes; docs validation | `local-check`; ADR-0001 | Not created |
| NFR-SEC-01–04 / PRIV-01 | `auth/`, provider, playlist server; team | Unit tests cover some OAuth and confirmation paths; full SEC-T review pending | `youtube-provider-live-check`; ADR-0004 | Not created |
| NFR-COMP-03 | Product policy and privacy; team | Official policy research recorded; team review not completed | [[brain/sid/resources/research-07-youtube-policy]] | Not created |
| NFR-REL-01/02 | playlist/provider error handling; team | Playlist unit tests cover partial failure and missing channel; broader API-error matrix pending | `local-check`; owner project note | Not created |
| NFR-OPS-01 / CI-T | Docker Compose and CI; team | CI runs build, Ruff, pytest, secret scan and docs checks; full local stack smoke not recorded | `local-check`; [[brain/sid/resources/second-brain-conventions]] | Not created |
| NFR-TEST-01–03 / TQ-1–8 | tests, CI, testing docs; team | Unit/integration pass locally; no complete FR-1–7 MCP E2E; TQ-7 results in `testing/skill-evaluations.md` | Skills and contributor Brain logs | Not created |
| REV-T / SB-5 | branch/PR process; all | FR-3 implementation and tests are on a draft PR pending checks and review | [[brain/sid/areas/team-collaboration]] | [PR #11](https://github.com/Tharunqi/Yt_MCP/pull/11) |

## Evidence limits

The current live-provider attempt could not resolve `youtube.googleapis.com`;
this is a blocked run, not a pass/fail evaluation of API behavior. FR-4/5 live
results are transcribed from Tharun's notes and have not been independently
repeated here. PostgreSQL concurrency, production OAuth security, and a full
FR-1–FR-7 E2E remain unverified.

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
