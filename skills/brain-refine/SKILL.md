---
name: brain-refine
description: Organize brain notes using PARA, merge duplicates, and repair links without losing attribution.
---

# brain-refine

Use this workflow when inbox material needs sorting or existing notes need cleanup.

1. Review `brain/inbox/` and choose the correct PARA destination: `projects/`, `areas/`, `resources/`, or `archive/`.
2. Search for an existing note before creating a duplicate. Merge overlapping facts and preserve source references, requirement IDs, decisions, and contributor attribution.
3. Repair Obsidian wikilinks; confirm every link resolves to a note or a heading. Add explicit issue/PR links when identifiers are available, and leave them marked TBD when they are not.
4. Update `brain/index.md` when adding or moving an entry point note.
5. Add a dated review to `brain/log.md` at the end of the stage: what worked, what did not, and what to change.
6. Check [[brain/resources/second-brain-conventions]] for PARA and PR requirements; use [[brain/resources/youtube-mcp-requirements]] when refining YouTube MCP notes.

Keep source PDFs and external records unchanged. Brain changes go through a reviewed PR.
