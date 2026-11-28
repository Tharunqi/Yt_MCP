# MCP Tool Reference

This reference documents tools registered in the current server source. It is
not an OpenAPI document: the interface is MCP over Streamable HTTP, and schemas
are published by FastMCP during tool discovery. See the [SRS](../requirements/srs.md)
and [traceability matrix](../traceability.md) for project status.

Endpoint in the local Compose setup: `http://localhost:8000/mcp`.

| Tool | Inputs | Behavior / side effects |
|---|---|---|
| `health_check` | None | Returns a simple server-running message. |
| `find_similar_videos` | `video_url_or_id: str`; `max_results: int = 10` (1–25) | Validates and resolves a public video, searches/ranks a bounded candidate pool, returns seed, queries, links, metadata and reasons. Requires an available quota preflight. Read-only YouTube API access. |
| `find_similar_channels` | `channel_url_handle_or_id: str`; `max_results: int = 10` (1–10) | Resolves a public channel, samples up to five uploads per profile, searches up to three queries and ranks at most ten candidates. Returns links, scores and metadata-match reasons. Requires quota preflight. Read-only. |
| `recommend_videos` | `topic: str` (1–200 nonblank characters); optional `selected_playlist_ids` (up to 3); `include_subscription_uploads: bool = true`; `max_results: int = 10` (1–10) | Uses read-only OAuth to read up to 1,000 liked videos, up to 50 subscriptions, and up to 50 items from each selected playlist. Searches up to 25 topic candidates and can sample five uploads from each of up to five subscribed channels. Excludes liked/saved videos, applies request-time topic/creator/freshness/diversity ranking, and returns short reasons. The inferred profile is not saved; watch history is not used. Requires quota preflight. |
| `summarize_video_metadata` | `video_url_or_id: str` | Returns available video metadata (title, channel, description, category name and ID, publication date and duration) with an explicit metadata-only label. Does not summarize spoken content. Requires quota preflight. Read-only. |
| `analyze_engagement` | `start_date`, `end_date`; optional `selected_playlist_ids`; optional paired `comparison_start_date`, `comparison_end_date` | Reads authorized account data and returns date-bounded engagement statistics. Requires OAuth. |
| `analyze_playlist` | `playlist_id: str` (1–128 letters, numbers, `_` or `-`) | Reads up to 1,000 items across 20 pages. Returns total known duration, duration distribution, channel/category counts, item metadata, and missing-data counts. Descriptive metadata only; request-scoped; read-only OAuth. |
| `analyze_video` | `video_url_or_id: str` | Returns the same descriptive metadata measures for one video, including its available duration and channel/category. Requires quota preflight and read-only OAuth; results are request-scoped. |
| `preview_playlist` | `topic`, `total_duration_minutes`, `playlist_title`, `visibility`; optional `max_video_length_minutes`, `language` | Searches/fetches public metadata and returns a constrained preview. Does not write to the account. |
| `create_playlist_from_preview` | `preview_id: str`; `confirmed_by_user: bool` | Creates a playlist and adds items only when explicit confirmation is true and valid write OAuth/channel access is available. Reports partial item failures. This tool changes the user's YouTube account. |

`create_playlist_from_preview` requires the caller to present the preview and
obtain confirmation for its title, items, and visibility. A boolean supplied by
an untrusted model without an actual user confirmation is not valid consent.

## Planned MCP capabilities

FR-3 recommendations are available through `recommend_videos`, and FR-7
playlist/video analysis is available through `analyze_playlist` and
`analyze_video`. SK-1 still needs its end-to-end workflow check across the
available tools.
