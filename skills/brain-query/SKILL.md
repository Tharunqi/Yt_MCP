---
name: brain-query
description: Answer project questions and draft artifacts from distilled notes with traceable links.
---

# brain-query

Use this workflow to answer project questions or draft documents such as SRS updates, ADRs, and implementation plans.

1. Start at [[brain/index]] and read [[second-brain-workflow]]. Search relevant project, area, resource, and person notes.
2. Separate confirmed facts from assumptions, unresolved decisions, and user-reported outcomes. Keep requirement IDs visible.
3. Link answers and drafts to supporting notes with Obsidian wikilinks. For requirements, use stable heading links such as [[youtube-mcp-requirements#FR-1|FR-1]].
4. Every ADR and every skill must cite at least one distilled note, as required by SB-3. Prefer [[youtube-mcp-requirements]] for product constraints and [[second-brain-conventions]] for knowledge-work rules.
5. Say when a fact or issue/PR link is missing instead of guessing. Never include credentials, tokens, or secrets.
6. When asked what has been committed, verify `git log` and distinguish commit history from working-tree changes.
7. If the query reveals stale or missing knowledge, route the update through [[skills/brain-ingest/SKILL|brain-ingest]] or [[skills/brain-refine/SKILL|brain-refine]]. Add or update a PARA note when the user asks to keep the result.
