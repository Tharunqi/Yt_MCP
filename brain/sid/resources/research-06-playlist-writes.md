# Research 06 — YouTube playlist writes

- **Sources:** [Playlists: insert](https://developers.google.com/youtube/data/reference/rest/v3/playlists/insert), [PlaylistItems: insert](https://developers.google.com/youtube/data/reference/rest/v3/playlistItems/insert)
- **Reviewed:** 2026-11-27
- **Requirements:** FR-5.5–5.9, SK-1.4–1.5, NFR-UX-01

## Distilled findings

- `playlists.insert` creates a playlist and requires OAuth; the title is
  required, and privacy status is a writable property.
- `playlistItems.insert` is a separate authorized write to add a video.
- Current reference costs are 50 quota units per playlist create and 50 per
  playlist-item insertion.
- Because creation and item insertion are separate requests, a playlist may
  exist even if one or more insertions fail.

## Project implication

Preview the exact title, contents, and visibility before consent. Report partial
results rather than claiming all items were added. See [[brain/tharun/projects/youtube-mcp]] and [[brain/sid/resources/youtube-mcp-requirements]].
