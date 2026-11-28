# Tharun

## My work

- **FR-4:** Engagement analysis — complete and live-checked.
- **FR-5:** Playlist suggestions and creation — implemented, unit-checked, previewed live, and manually created after confirmation.
- **FR-7:** Playlist and single-video analysis are implemented, unit-checked, and live-checked; policy review remains.

I will work only on these three FRs. See [[brain/tharun/projects/youtube-mcp]] for project status and [[brain/tharun/log]] for run records.

## FR-4 progress

- The analysis accepts a date range and an optional comparison range. Both ends of each date range count.
- Likes use the video publish date because YouTube does not provide when a video was liked. The API result is limited to the latest 1,000 liked videos.
- Subscription trends use YouTube subscription-created dates. Playlist trends use the added dates for the selected playlists. Trends are weekly.
- To limit API use, reads cover up to 1,000 subscriptions and up to five selected playlists, with 1,000 items and 20 pages per source.
- A video that appears in likes and playlists counts once in video totals. Playlist trend counts each playlist item.
- FR-4 and FR-5 reserve quota before YouTube data calls and settle the actual usage.
- Results show their date ranges, sources, missing dates, and missing metadata. They describe liked or saved content, not watch time. Results are not saved.
- Unit checks and CI cover FR-4. The live read-only check passed; account result details are not kept here.

## FR-5 progress

- The preview takes a topic, total time, optional maximum video length, optional language, title, and privacy.
- It searches YouTube, checks video details, removes duplicates, and skips unavailable videos.
- The preview searches up to 50 videos and keeps YouTube's relevance order. It skips unknown duration, mismatched or unknown requested language, and items that do not fit. It continues checking later videos after an item does not fit.
- A video that exactly fills the remaining time is included. If several videos could fit, the first one in YouTube's relevance order is considered first.
- Playlist visibility must be private, unlisted, or public. The preview shows the title, channel, length, link, reason, total time, privacy, and skipped items.
- No playlist is created until the user confirms the one-time preview. The preview expires after 15 minutes. Write access is requested after confirmation, and the app checks for a YouTube channel first.
- The result lists videos added and any that failed. Unit checks, live preview, and playlist creation after user confirmation passed.

## FR-7 progress

- `analyze_playlist` checks one playlist ID, then reads up to 1,000 items across 20 pages. `analyze_video` checks one video ID or supported URL.
- The result includes known total duration, five duration ranges, channel/category counts, and each playlist item’s metadata and link.
- Repeated videos count as separate playlist items. Missing videos and durations are shown; the duration total uses known values only.
- The result says it is descriptive metadata, does not measure viewing behavior, and is not saved. Quota is reserved before client setup and YouTube reads.
- Unit tests cover playlist and video counts, missing metadata, repeated videos, empty playlists, ID checks, quota rejection, and result output.
- Read-only playlist and single-video checks passed through MCP. The YouTube API policy review is still needed before release or storage.

## Second Brain

- Start from [[brain/tharun/index]] and use the [[second-brain-workflow]] note.
- Use the [brain-ingest](../../skills/brain-ingest/SKILL.md), [brain-refine](../../skills/brain-refine/SKILL.md), and [brain-query](../../skills/brain-query/SKILL.md) skills.
- Keep Brain changes in the pull request. Current review: [PR #10](https://github.com/Tharunqi/Yt_MCP/pull/10).
- Sid and Viraj should write their own notes; I will not write notes for them.

## Decisions

- Use weekly trends for FR-4. Filter likes by video publish date, since YouTube does not return like dates.
- Use read-only access for analysis and previews. Ask for write access only after playlist confirmation.
- Keep FR-5 candidates in YouTube relevance order. Include a video when it fits the remaining time, including an exact fit.
- Accept private, unlisted, or public as the playlist visibility.
- Keep our notes and feature diagrams in `brain/tharun/`. The FR-4/FR-5 design note records the UML, data flow, and existing database model.
- Work on the `tharun` branch. Do not edit `main`.

## Next steps

- Review this Brain update and submit it through a PR, as required by SB-5.
- Ask each team member to author their own Brain note.
- FR-4 and FR-5 live checks are recorded.
- Finish the SRS/SDLC review of FR-4, FR-5, and FR-7. The YouTube API policy review remains open before release or storage.
