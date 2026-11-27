# Test and Acceptance Plan

This plan maps TQ-1–TQ-8 and SEC-T to verification evidence. CI must stay
independent of live YouTube. Live tests are opt-in and supplemental.

| Requirement | Verification approach | Current evidence | Remaining |
|---|---|---|---|
| TQ-1 unit | Deterministic unit tests for feature logic, validators, ranking, quota, planner, and tools | Current run: 90 passed; 5 opt-in live tests skipped | Add missing feature coverage for FR-3/6/7 |
| TQ-2 integration | Fakes/fixtures across provider and feature boundaries | `tests/integration/test_discovery_mcp.py`, including FR-1 and FR-2 MCP tool flows | Broader auth, engagement, playlist, and provider integration matrix |
| TQ-3 system/E2E | Invoke tools through MCP for FR-1–FR-7 | No complete FR-1–FR-7 E2E currently | Build E2E per implemented feature and SK-1 |
| TQ-4 negative | Invalid/unavailable IDs, missing metadata, quota, expired OAuth, API errors | Existing FR-1 and playlist negatives | Complete error matrix for each feature/provider |
| TQ-5 CI isolation | Run mocks/fixtures without live API credentials | CI runs pytest with live tests skipped unless opted in | Keep live tests out of required CI path |
| TQ-6 quota preflight | Assert insufficient quota rejects before any provider call | FR-1 unit/integration tests, FR-4 reject-before-fetch test, FR-4/FR-5 estimates and accounting tests, and quota ledger tests | Verify PostgreSQL concurrency |
| TQ-7 skill evaluation | Manual/automated scenarios before each stage submission | [skill evaluations](skill-evaluations.md) | Repeat and attach evidence for future stage PRs |
| TQ-8 regression | For each significant defect, add a regression test and preserve suite | Unit suite exists; current known gaps in [defect log](defect-log.md) | Add tests when those defects/gaps are addressed |
| SEC-T security | Scope, token storage, no secret/log leakage, validation, metadata isolation, consent paths | Some OAuth/confirmation unit tests and Gitleaks CI step | Security review and negative tests for each control |

## Local result — 2026-11-27

- Ruff: passed.
- Brain/skill validator: passed (6 skills; 26 notes; two intentional empty
  member placeholders excluded).
- Automated suite: 68 passed, 5 opt-in live tests skipped.
- Live MCP discovery test for `8vRhCUPB6Jk`: after prioritizing focused
  channel-topic queries, YouTube returned ten FR-1 candidates and nine FR-2
  channels; the test passed. Some channel scores are low and still need
  representative quality review.
- An earlier sandboxed provider-live attempt was blocked by DNS resolution for
  `youtube.googleapis.com`; the later MCP test reached the API.
- Package build: not run because `build` is not installed in this local venv.
- Docker Compose startup and MCP read-only fetch: blocked because Docker Desktop's
  daemon was not running; no containers were started.

The later verification also confirmed `docker compose config --quiet` and
`git diff --check` passed. After FR-2 implementation, Ruff and the repository
documentation validator passed again. The exact package build and secret scan
remain CI checks and have not yet completed in this local environment.

See [local-check](../../skills/local-check/SKILL.md),
[provider live check](../../skills/youtube-provider-live-check/SKILL.md), and
[skill evaluation records](skill-evaluations.md).
