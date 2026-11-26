---
name: brain-ingest
description: Add new source material and concise, traceable summaries to the repository Second Brain.
---

# brain-ingest

Use this workflow when new project source material, decisions, test results, or user-provided requirements should be captured.

1. Start at [[brain/index]] and follow the shared placement rules in [[second-brain-workflow]].
2. Distinguish source-document requirements from the user's current request. Extract durable facts, decisions, constraints, and open questions; preserve requirement IDs.
3. Place unsorted material in `brain/inbox/`; put reviewed reusable summaries in `brain/resources/`; put active outcomes in `brain/projects/`.
4. Write summaries in your own words. Add Obsidian wikilinks, source names, dates, and issue/PR links when known. Do not guess missing facts or IDs.
5. Keep credentials, tokens, API keys, and private user data out of notes.
6. When recording a commit in `brain/log.md`, include a short review of what worked, what did not, and what should change. Consolidate intermediate checkpoints into the commit's entry.
7. Follow [[second-brain-conventions]] and the distilled product constraints in [[youtube-mcp-requirements]].

Brain changes go through a reviewed PR. Do not create or push a commit unless the user explicitly asks.
