# Test and Acceptance Plan

This plan maps TQ-1–TQ-8 and SEC-T to verification evidence. CI must stay
independent of live YouTube. Live tests are opt-in and supplemental.

| Requirement | Verification approach | Current evidence | Remaining |
|---|---|---|---|
| TQ-1 unit | Deterministic unit tests for feature logic, validators, ranking, quota, planner, and tools | Before merging the latest FR-7 work, GitHub CI passed: 89 passed, 5 opt-in live tests skipped; FR-3 service tests are in `tests/unit/recommendations/test_service.py` | Rerun full suite on the updated branch; add remaining feature coverage |
| TQ-2 integration | Fakes/fixtures across provider and feature boundaries | `tests/integration/test_discovery_mcp.py`; FR-3 MCP flow in `tests/integration/test_recommendations_mcp.py`; GitHub CI passed before latest merge | Rerun on updated branch; broader auth, engagement, playlist, and provider integration matrix |
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

## FR-3 stage check — 2026-11-28

- Added deterministic service tests for bounded inputs, interaction exclusions,
  missing channels, quota estimates/settlement, and provider failures.
- Added MCP integration tests for tool registration, successful results,
  authorization denial, and quota rejection before OAuth.
- Fixed subscribed-channel sampling so no more than five channel lookups are
  attempted, even when some channel IDs are unavailable.
- Local Python tests, Ruff, package build, and documentation validation could
  not run because this Windows environment has no installed Python interpreter.
  `git diff --check` passed. CI remains the execution gate for the added tests.

- Follow-up: GitHub CI passed on commit `23a4d59` (89 passed, 5 opt-in live
  tests skipped). Ruff, package build, repository-doc validation, and secret
  scanning also passed. The PR remains a draft pending maintainer review.

## Final Tharun FR checks — 2026-11-28

- Full automated suite: 105 passed, 5 opt-in live checks skipped.
- Ruff, repository docs/Brain validation, and `git diff --check`: passed.
- Docker image build and local MCP service startup: passed.
- FR-4: live account analysis with two equal-length periods and a selected playlist returned both analysis and comparison results. Full account results were not saved in project notes.
- FR-5: live constrained preview returned a private preview. A no-confirmation create request returned `confirmation_required` and made no changes. The user confirmed that a prior preview was explicitly approved and the playlist was created in their account.
- FR-7: live playlist and single-video analyses returned metadata through MCP. Derived results were not saved.
- The standalone local `python -m build` command is unavailable because `build` is not installed on the host. The Docker image built and packaged the current code. The existing CI workflow runs the full package build on PRs.
- PR #10 is open. Its GitHub Actions checks and the required teammate review are pending.
