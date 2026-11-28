# Development Plan and Issue Backlog

This plan is derived from the [SRS](requirements/srs.md). Every work item should
be created as a GitHub Issue, implemented on a contributor branch, and reviewed
through a PR. Issue links remain marked **not created** until the team creates
them; this document does not invent issue identifiers. Contributor ownership
follows [[brain/Team]].

## Stages

| Stage | Goal | Exit evidence | Status |
|---|---|---|---|
| 1. Requirements and repository | SRS, Brain workflow, CI skeleton, research notes | Reviewed SRS; >=10 distilled research notes; AGENTS; CI green | Artifacts and ten notes present; team review pending |
| 2. Design | Architecture, data model, ADRs, local-check, traceability | Reviewed diagrams/ADRs; checked local workflow | Docs and diagrams are present; Docker Compose and the FR-7 read-only MCP check now passed; team review pending |
| 3. Feature delivery | FR-1–FR-7 incrementally with regression tests and skill evaluations | Per-feature acceptance tests; defect log; stage reviews; CI green | In progress; FR-1/2/4/5/6/7 present; FR-3, FR-7 PR review, skill E2E, and team review remain |
| 4. Product validation and release | SK-1 E2E, live demo, end-to-end trace, release | All features demonstrated; review/approval; changelog and tag | Not ready; FR-3, SK-1 end-to-end validation, policy review, and team approval remain |

## Work items

| Work item | Owner | Requirements | Acceptance / verification | Issue |
|---|---|---|---|---|
| Complete FR-1 current-branch review and regression | Sid | FR-1, TQ-1/2/4/6 | Unit/integration/negative checks and quota preflight evidence | Not created |
| Implement FR-2 bounded channel discovery | Sid | FR-2.1–2.5 | Implemented: 5-upload samples, up to 3 queries, 10 candidates; unit/MCP tests pass | Not created |
| Implement FR-3 request-time recommendations | Viraj | FR-3.1–3.7 | OAuth scope, source aggregation, exclusions, explanations; tests | Not created |
| Complete FR-4 acceptance and timestamp verification | Tharun | FR-4.1–4.7, NFR-QUOTA-01–03 | Date rules, source limits, comparison, and quota preflight have unit coverage; PostgreSQL concurrency remains open | Not created |
| Complete FR-5 edge cases and write safety | Tharun | FR-5.1–5.9, NFR-QUOTA-01–03 | Exact fit, candidate order, visibility, confirmation, partial writes, and quota accounting have unit coverage; live creation confirmed by owner | Not created |
| Implement FR-6 metadata-only summary | Viraj | FR-6.1–6.3 | Metadata output labels; tests prohibit spoken-content claims | Not created |
| Implement FR-7 playlist/video analysis | Tharun | FR-7.1–7.6 | `analyze_playlist` and `analyze_video` implemented; unit/quota checks and live FR-4, FR-5 preview, FR-7 playlist/video checks passed; policy review remains | [Issue #9](https://github.com/Tharunqi/Yt_MCP/issues/9); [PR #10](https://github.com/Tharunqi/Yt_MCP/pull/10) |
| Build SK-1 video-to-playlist workflow | Team/skill owner TBD | SK-1.1–1.6 | MCP E2E covers summary through confirmed creation and final analysis | Not created |
| Verify PostgreSQL quota concurrency and decide migrations | Sid/DB owner TBD | NFR-QUOTA-03, TBD-1/2 | Concurrent integration evidence; migration decision | Not created |
| Security and policy review | Team | NFR-SEC-01–04, NFR-PRIV-01, SEC-T | Scope/storage/log/retention review recorded | Not created |
| Complete CI and repository checks | Team | CI-T, TQ-5, TQ-8 | Build, lint, tests, secret scan, skill and Brain checks pass on PR | Not created |
| Run skill evaluations and stage reviews | Each skill owner | TQ-7, SB-2 | Evaluation results and worked/did-not/change notes recorded | Not created |
| Product E2E demo and release prep | Team | TQ-3, REV-T | Live demo, trace complete, changelog, approved release tag | Not created |

## Open decisions to resolve as Issues

Production SQL and deployment; schema migrations; OAuth app type/redirect and
token encryption; FR-1/FR-2 ranking-quality evaluation; FR-6 eligible source;
FR-7 retention; final MCP schemas/resources; supported skill hosts;
response-time/availability targets; and derived-data retention/deletion.
