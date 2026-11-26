# Tharun

## My work

- **FR-4:** Engagement analysis — complete.
- **FR-5:** Playlist suggestions and creation — implemented and checked.
- **FR-7:** Playlist and video analysis — next.

I will work only on these three FRs.

## FR-4 progress

- The analysis accepts a date range and an optional comparison range.
- It shows video, channel, category, duration, top-list, and weekly trend results.
- The results include date ranges, data sources, and missing dates or metadata.
- YouTube does not show when a video was liked, so likes use the video publish date for filtering.
- Results stay in memory for the request and are not saved. Earlier test snapshots were cleared.
- The API returns up to 1,000 liked videos.
- Unit checks and CI cover FR-4.

## FR-5 progress

- The preview takes a topic, total time, optional maximum video length, optional language, title, and privacy.
- It searches YouTube, checks video details, removes duplicates, and skips unavailable videos.
- The plan does not go over the time limit. It keeps YouTube's relevance order and skips videos that do not fit.
- Videos with unknown duration are skipped. If a language is requested, videos with unknown or different language are skipped.
- The preview shows the title, channel, length, link, reason, total time, and privacy. It also shows skipped videos and why.
- No playlist is created until the user confirms that preview. The preview expires after 15 minutes and can only be used once.
- Playlist write access is requested only after confirmation. The app checks for a YouTube channel first.
- The result says which videos were added and lists any that failed.
- Four new server-flow checks and planner/provider checks pass. The CI workflow runs the full tests folder.

## Decisions

- Keep the current project structure and use weekly trends for FR-4.
- Use read-only YouTube access for FR-4 and playlist previews. Ask for playlist write access only when creating.
- Keep search relevance order. Choose videos that fit the time budget and show any remaining time.
- Require a title and an explicit privacy choice: private, unlisted, or public.
- Work on the `tharun` branch. Do not edit `main`.

## Next steps

- Review the FR-5 commit and try it with your YouTube account when ready.
- Start FR-7 after FR-5 is reviewed.
