# Skill Evaluation Records

Requirement: TQ-7 says evaluations run before each stage submission and their
results are recorded. This is the first consolidated evaluation for the current
branch, not evidence that earlier stage submissions were evaluated. Future
submissions must add dated results here. See [[brain/sid/resources/second-brain-conventions]].

## Evaluation rubric

For each skill, check that its inputs and sources are clear, it follows the
assigned workflow, avoids invented facts/secrets, cites distilled Brain notes,
and states completion evidence. A manual evaluation is not an automated E2E
test.

## 2026-11-27 branch baseline

| Skill | Scenario and evidence | Result | Remaining |
|---|---|---|---|
| `brain-ingest` | Used its source/date/link/no-secret rules while recording the live-check blocker in Sid's log; repository Brain validation passed. | Pass for this bounded note-ingest scenario. | Does not demonstrate every supported source type. |
| `brain-refine` | Checked PARA links and project references; validator accepted 14 notes and explicitly excluded two empty member placeholders without editing them. | Pass for existing-note/link validation. | Duplicate-merge behavior was not exercised. |
| `brain-query` | Used contributor index, distilled requirements, workflow note, and linked sources to answer the SDLC status question. | Pass for a sourced status answer. | Drafting a full ADR/SRS was not a standalone skill test. |
| `local-check` | Ruff, docs validator, and automated pytest suite ran; live test and Compose startup were attempted. | Partial / blocked: Ruff and validator pass; tests 68 passed/5 skipped; live MCP test passed with ten similar videos and nine similar channels; package build unavailable locally because `build` is absent; Docker daemon is not running, so app/db container smoke could not run. | Review lower-scoring channel matches; run package build and Docker/PostgreSQL smoke on a configured developer host/CI. |
| `youtube-provider-live-check` | Ran opt-in provider cases and registered MCP discovery tools with `8vRhCUPB6Jk`, before and after refining FR-2 queries. | Initial FR-2 run returned none; cleaned channel-description/tag/title queries now return nine channels, and the live MCP test passes. | Review result quality on representative seeds; no minimum quality threshold is set yet. |
| `video-to-playlist` | Reviewed against SK-1 ordering and confirmation requirements; required FR-6 and FR-7 tools are not present. | Not executable end-to-end yet. | Implement FR-6/FR-7, then test full MCP workflow including decline and confirm paths. |

## Before each stage submission

Re-run applicable skill scenarios on the candidate branch, attach test output or
manual evidence, record result and evaluator, and link the PR. No historical
results or PR IDs are fabricated here.


## 2026-11-28 Tharun final checks

| Skill | Scenario and evidence | Result | Remaining |
|---|---|---|---|
| `local-check` | Rebuilt the current Docker image, started the local stack, ran 105 automated tests, Ruff and the docs validator, then invoked FR-4, FR-5 preview, and FR-7 playlist/video tools through MCP. | Pass for these assigned-feature checks. | Full SK-1 product workflow, PR CI for the new changes, and team review remain. |
| `brain-query` | Traced FR-7.1–FR-7.6 from the SRS to analytics code, quota estimate, unit tests, and Tharun's FR-7 note. | Pass for this bounded requirement query. | A complete project-wide requirement query remains part of Stage 4. |
| `video-to-playlist` | FR-5 preview and confirmation refusal were live-checked; earlier confirmed creation is owner-reported. | Partial; not a full SK-1 run. | Run the complete FR-6 → FR-1 → FR-5 → confirmation → FR-7 sequence with team approval. |
