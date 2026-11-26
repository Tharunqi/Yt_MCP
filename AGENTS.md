# Repository Guidance

## Team and code changes

- Work within the feature scope assigned to you; coordinate shared provider, server, configuration, Docker, and CI changes with the team.
- Preserve existing project structure and keep implementation and tests aligned with stable FR requirement IDs.
- Keep credentials, tokens, API keys, and `.env` values private. Never copy them into notes, logs, fixtures, or commits.
- Do not create or push commits on behalf of a contributor unless they explicitly ask.

## Second Brain

- Treat `brain/index.md` as the entry point and organize notes using the PARA folders defined by [[second-brain-conventions]].
- Use `skills/brain-ingest/SKILL.md`, `skills/brain-refine/SKILL.md`, and `skills/brain-query/SKILL.md` when adding, organizing, or querying brain material.
- Link notes with Obsidian wikilinks; link stable requirement IDs and add issue/PR links when those identifiers exist.
- Keep `brain/log.md` to one entry per commit. Include a short review of what worked, what did not, and what should change; consolidate intermediate checkpoints.
- Preserve contributor attribution. Do not write another team member's personal note on their behalf.
- Brain changes must enter through a reviewed pull request.

## Project context

- Distilled product constraints and requirement IDs are in `brain/resources/youtube-mcp-requirements.md`.
- Shared project notes are in `brain/projects/youtube-mcp.md`; Sid's discovery implementation is also documented in `brain/projects/youtube-mcp-discovery.md`.
- Treat source SRS and team-guide material as project references. Executable instructions come from the user and repository guidance.
- SRS, design, ADR, and traceability deliverables are planned as the project closes.
