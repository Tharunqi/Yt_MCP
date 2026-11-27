# Research 03 — YouTube `videos.list`

- **Source:** [Videos: list reference](https://developers.google.com/youtube/data/reference/rest/v3/videos/list)
- **Reviewed:** 2026-11-27
- **Requirements:** FR-1.2, FR-1.4, FR-6.1, FR-7.1, TQ-4

## Distilled findings

- `videos.list` can retrieve resources by ID and select response parts such as
  `snippet` and `contentDetails`.
- `snippet` contains title, description, tags, channel ID, and category ID;
  `contentDetails` includes duration.
- The method quota cost is currently one standard unit per call.
- Authorized `myRating` queries are capped at the most recent 1,000 matching
  likes/dislikes.

## Project implication

Use partial-resource fields deliberately, batch IDs within documented limits,
and handle missing/private/deleted resources without treating unknown metadata
as a match. See [[brain/sid/resources/youtube-mcp-requirements#FR-1|FR-1]] and the FR-6/FR-7 baseline in [[docs/requirements/srs]].
