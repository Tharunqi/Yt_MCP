# FR-7 playlist analysis

Date: 2026-11-28
Owner: Tharun
Requirements: FR-7.1–FR-7.6, NFR-QUOTA-01–03, NFR-PRIV-01

## What it does

The `analyze_playlist` tool checks one playlist ID, reserves quota, and reads
playlist items and video metadata through the current YouTube provider. It reads
up to 1,000 items across 20 pages. It returns total known duration, duration
ranges, channel/category counts, and an item summary with links.

Each playlist position counts as an item, including repeated videos. Video
metadata is requested once per unique video ID. Missing videos and durations are
reported. The total uses available durations only and `duration_complete` tells
when information is missing.

The result is descriptive and metadata-based. It does not claim to measure
views, watch time, likes, or viewer behavior. Results are not saved. A YouTube
API policy review is still needed before release or any later storage/expansion.

## Checks

Focused tests: 13 passed. Full suite: 100 passed, 5 live checks skipped.
Ruff, docs/Brain validation, and `git diff --check` passed. The local `python -m build` command was unavailable because `build` is missing
from the host environment. The Docker image rebuilt and packaged the current
code successfully. The live check initially found the old app image;
rebuilding it exposed the tool, and the read-only MCP check then passed. The
playlist result is not saved in project notes.

## Data flow

```mermaid
flowchart LR
    Host[MCP client] -->|playlist ID| Tool[analyze_playlist]
    Tool --> Validate[Validate ID]
    Validate --> Quota[Reserve worst-case quota]
    Quota --> Provider[YouTube data provider]
    Provider --> API[YouTube Data API]
    API --> Analysis[Count items and summarize metadata]
    Analysis --> Result[Return descriptive result]
    Analysis -. request-scoped only .-> Memory[Temporary request memory]
```

## Simple class view

```mermaid
classDiagram
    class PlaylistAnalysisTool {
      +analyze_playlist(playlist_id)
    }
    class PlaylistAnalysis {
      +validate_playlist_id(id)
      +analyze_playlist(id, provider)
    }
    class YouTubeDataProvider {
      +list_playlist_items(id)
      +get_videos(ids)
      +get_category_names(ids)
    }
    PlaylistAnalysisTool --> PlaylistAnalysis
    PlaylistAnalysis --> YouTubeDataProvider
```

## UML sequence

```mermaid
sequenceDiagram
    actor User
    participant Host as MCP client
    participant Tool as analyze_playlist
    participant Quota as Quota ledger
    participant Provider as YouTube data provider
    participant API as YouTube Data API
    User->>Host: Request playlist analysis
    Host->>Tool: playlist ID
    Tool->>Tool: Validate ID
    Tool->>Quota: Reserve 41 standard units
    Tool->>Provider: Read bounded playlist
    Provider->>API: Playlist items, video details, category names
    API-->>Provider: Metadata
    Provider-->>Tool: Playlist and video records
    Tool->>Tool: Count items and summarize known fields
    Tool-->>Host: Descriptive, request-scoped result
```

## ER diagram

FR-7 adds no saved analytics records, so there are no new ER entities for this
feature. The project ER diagram remains the quota usage/reservation model in
[[fr4-fr5-design]].

## Next

- Tomorrow: complete the final SRS/SDLC review of FR-4, FR-5, and FR-7.
- Keep analytics request-scoped until the team completes the API policy review.
- Add an issue and PR link when the team creates them; neither ID is available yet.
