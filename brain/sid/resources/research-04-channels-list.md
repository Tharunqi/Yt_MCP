# Research 04 — YouTube `channels.list`

- **Source:** [Channels: list reference](https://developers.google.com/youtube/data/reference/rest/v3/channels/list)
- **Reviewed:** 2026-11-27
- **Requirements:** FR-2.1–2.2, FR-3.2, FR-5.7

## Distilled findings

- `channels.list` can resolve channels using ID, handle, or legacy username
  filters and requests selected resource parts.
- A channel resource's `contentDetails` contains the uploads playlist ID.
- `mine=true` and private account details require authorization; public lookup
  may use an API key where permitted.
- Current quota cost is one standard unit per call.

## Project implication

Use handle/ID resolution for FR-2 and the uploads playlist for bounded recent
uploads. Keep public lookup separate from account-scoped operations. See
[[brain/sid/resources/youtube-mcp-requirements#FR-2|FR-2]].
