# Tharun

## My work

- **FR-4:** Engagement analysis
- **FR-5:** Playlist suggestions and creation
- **FR-7:** Playlist and video analysis

I will work only on these three FRs.

## FR-4 progress

- The analysis accepts a date range and an optional comparison range.
- When comparing periods, it shows changes in video, channel, category, and duration results.
- It shows the top channels and categories for liked videos and selected playlists.
- It shows duration totals, averages, medians, and groups videos by duration.
- It shows weekly trends from subscription dates and playlist item dates.
- The results include the date ranges, data sources, and any missing dates or metadata.
- YouTube does not show when a video was liked, so likes use the video's publish date for the date filter.
- Results stay in memory for the request and are not saved. Earlier test snapshots were cleared.
- The API only returns up to 1,000 liked videos.
- Unit checks and CI cover FR-4.

## Decisions

- Keep the current project structure and use weekly trends.
- Use read-only YouTube access for FR-4.
- Work on the `tharun` branch. Do not edit `main`.
- Keep FR-5 and FR-7 for later.

## Next steps

- Try the analysis with a date range and one selected playlist.
- Start FR-5 after FR-4 is reviewed.
