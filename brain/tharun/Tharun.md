# Tharun

## My work

- **FR-4:** Engagement analysis — complete and live-checked.
- **FR-5:** Playlist suggestions and creation — implemented, unit-checked, and previewed live. No playlist was created.
- **FR-7:** Playlist and video analysis — next.

I will work only on these three FRs. See [[brain/tharun/projects/youtube-mcp]] for project status and [[brain/tharun/log]] for run records.

## FR-4 progress

- The analysis accepts a date range and an optional comparison range.
- It shows video, channel, category, duration, top-list, and weekly trend results.
- The results include date ranges, data sources, and missing dates or metadata.
- YouTube does not show when a video was liked, so likes use the video publish date for filtering.
- Results stay in memory for the request and are not saved. Earlier test snapshots were cleared.
- The API returns up to 1,000 liked videos.
- Unit checks and CI cover FR-4. A live read-only check returned one video for 2026-11-01 to 2026-11-26.

## FR-5 progress

- The preview takes a topic, total time, optional maximum video length, optional language, title, and privacy.
- It searches YouTube, checks video details, removes duplicates, and skips unavailable videos.
- The plan does not go over the time limit. It keeps YouTube's relevance order and skips videos that do not fit.
- Videos with unknown duration are skipped. If a language is requested, videos with unknown or different language are skipped.
- The preview shows the title, channel, length, link, reason, total time, and privacy. It also shows skipped videos and why.
- No playlist is created until the user confirms that preview. The preview expires after 15 minutes and can only be used once.
- Playlist write access is requested only after confirmation. The app checks for a YouTube channel first.
- The result says which videos were added and lists any that failed.
- Unit checks passed. A live preview worked; playlist creation was not tested.

## Second Brain

- Start from [[brain/tharun/index]] and use the [[second-brain-workflow]] note.
- Use the [brain-ingest](../../skills/brain-ingest/SKILL.md), [brain-refine](../../skills/brain-refine/SKILL.md), and [brain-query](../../skills/brain-query/SKILL.md) skills.
- Keep Brain changes for a pull request. This update is still local and uncommitted.
- Sid and Viraj should write their own notes; I will not write notes for them.

## Decisions

- Keep the current project structure and use weekly trends for FR-4.
- Use read-only YouTube access for FR-4 and playlist previews. Ask for playlist write access only when creating.
- Keep search relevance order. Choose videos that fit the time budget and show any remaining time.
- Require a title and an explicit privacy choice: private, unlisted, or public.
- Work on the `tharun` branch. Do not edit `main`.
- Prepare the SRS and other software engineering documents at the end of the project.

## Next steps

- Review this Brain update and submit it through a PR, as required by SB-5.
- Ask each team member to author their own Brain note.
- Retry the Docker build and live check later.
- Start FR-7 after FR-5 is reviewed.
