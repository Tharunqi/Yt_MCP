# Project guidance

- Respect contributor assignments and the user's current task. Tharun's assigned features remain FR-4, FR-5, and FR-7.
- Keep writing simple and preserve the existing project structure.
- Treat credentials, tokens, and `.env` values as private. Never copy them into notes or chat.
- Start Brain work in the relevant contributor folder under `brain/{sid,tharun,viraj}/`; the existing notes and index are currently under `brain/tharun/`. Keep `brain/Team.md` at the root. Use the `brain-ingest`, `brain-refine`, and `brain-query` skills in `skills/`.
- Keep Brain notes linked with Obsidian wikilinks and add requirement, issue, and PR links when those IDs exist.
- Record significant runs and stage reviews in the relevant contributor's `brain/<name>/log.md`.
- Brain changes must be submitted through a pull request. Do not author notes for another team member.
- Shared requirements, architecture, ADRs, API, plan, traceability, test, and release documents belong in `docs/`; update them alongside implementation changes.
- Keep the root `brain/index.md` deferred until contributors finish their notes; use the contributor indexes in the meantime. `brain/log.md` links to each contributor's canonical log.
