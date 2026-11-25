# Second Brain Conventions

Distilled from Sid's Second Brain requirements supplied on 2026-11-25. This note is the operational reference for the repository's brain workflow.

## PARA placement

- Put unsorted material in `brain/inbox/`.
- Put active work with a concrete outcome in `brain/projects/`.
- Put ongoing responsibilities in `brain/areas/`.
- Put reusable reference material in `brain/resources/`.
- Move inactive work to `brain/archive/`.
- Keep `brain/index.md` as the entry point and record each work session in `brain/log.md`.

## Note quality and lifecycle

- Connect related notes with Obsidian Obsidian wikilinks.
- Link requirements by their stable IDs. Add issue and PR references when those identifiers exist.
- End each implementation stage with a short review: what worked, what did not, and what should change.
- Every team member authors and maintains their own contribution notes; authorship should be visible in Git history.
- Brain changes are submitted through the project's pull-request workflow (SB-5). Keep them as working-tree changes until they are included in a reviewed PR.

## Workflow guides

- [[skills/brain-ingest/SKILL|brain-ingest]] captures new source material and produces a concise, traceable summary.
- [[skills/brain-refine/SKILL|brain-refine]] moves material into PARA, merges duplicates, and repairs links.
- [[skills/brain-query/SKILL|brain-query]] answers questions and drafts artifacts from distilled notes, with links back to evidence.

The workflow guides live under `skills/brain-*`. Each one cites this distilled conventions note, as required by SB-3.
