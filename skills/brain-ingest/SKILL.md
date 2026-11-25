---
name: brain-ingest
description: Add new source material and concise, traceable summaries to the repository Second Brain.
---

# brain-ingest

Use this workflow when new project source material, decisions, test results, or user-provided requirements should be captured.

1. Identify the source and distinguish source-document requirements from the user's current request.
2. Extract only durable facts, decisions, constraints, and open questions. Preserve stable requirement IDs such as FR-1 and FR-2.
3. Place unprocessed material in `brain/inbox/`; place reviewed reusable summaries in `brain/resources/`; put active outcomes in `brain/projects/`.
4. Add Obsidian wikilinks to related notes and requirement headings. Record source names and dates without copying secrets or personal data.
5. Add a dated record to `brain/log.md` when the intake is part of a work stage, including what worked, what did not, and what should change.
6. Follow [[brain/resources/second-brain-conventions]] and the distilled product constraints in [[brain/resources/youtube-mcp-requirements]].

Do not commit brain edits directly. They must enter through the reviewed PR workflow in [[brain/resources/second-brain-conventions]].
