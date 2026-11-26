# Second Brain Conventions

Distilled from Sid's Second Brain requirements supplied on 2026-11-25. This note is the operational reference for the repository's brain workflow.

## PARA placement

- Put unsorted material in `brain/sid/inbox/`.
- Put active work with a concrete outcome in `brain/sid/projects/`.
- Put ongoing responsibilities in `brain/sid/areas/`.
- Put reusable reference material in `brain/sid/resources/`.
- Move inactive work to `brain/sid/archive/`.
- Keep `brain/sid/index.md` as the entry point. Keep `brain/sid/log.md` to one entry per commit, consolidating intermediate checkpoints into that stage review. If the user asks to record uncommitted work, label it clearly as pending and do not invent a commit hash.

## Note quality and lifecycle

- Connect related notes with Obsidian wikilinks.
- Link requirements by their stable IDs. Add issue and PR references when those identifiers exist.
- End each implementation stage with a short review: what worked, what did not, and what should change.
- Every team member authors and maintains their own contribution notes; do not write another person's note on their behalf. Authorship should be visible in Git history.
- Brain changes are submitted through the project's pull-request workflow (SB-5). Keep them as working-tree changes until they are included in a reviewed PR.

## Workflow guides

- [[skills/brain-ingest/SKILL|brain-ingest]] captures new source material and produces a concise, traceable summary.
- [[skills/brain-refine/SKILL|brain-refine]] moves material into PARA, merges duplicates, and repairs links.
- [[skills/brain-query/SKILL|brain-query]] answers questions and drafts artifacts from distilled notes, with links back to evidence.

The workflow guides live under `skills/brain-*`. Each one cites this distilled conventions note, as required by SB-3. The FR-1 implementation is documented as the third commit stage. Do not add a commit hash to that entry because the log is included in the commit itself. Never invent commit IDs.
