---
name: brain-query
description: Answer project questions and draft artifacts from distilled notes with traceable links.
---

# brain-query

Use this workflow to answer questions or draft documents such as SRS updates, ADRs, and implementation plans from the Second Brain.

1. Start at `brain/index.md`; read the most relevant project, area, and resource notes.
2. Separate confirmed facts from assumptions, unresolved decisions, and user-reported outcomes. Keep requirement IDs visible.
3. Link the answer or draft to its source notes with Obsidian wikilinks. For a requirement, link its stable ID heading (for example, [[brain/resources/youtube-mcp-requirements#FR-1|FR-1]]).
4. Every ADR and every new skill must cite at least one distilled note, as required by SB-3. Prefer [[brain/resources/youtube-mcp-requirements]] for product constraints and [[brain/resources/second-brain-conventions]] for knowledge-work rules.
5. If the query reveals stale or missing knowledge, route the update through [[skills/brain-ingest/SKILL|brain-ingest]] or [[skills/brain-refine/SKILL|brain-refine]], then record meaningful work in `brain/log.md`.

Do not present an inference as a source fact. Do not include secrets or private user data in answers or drafts.
