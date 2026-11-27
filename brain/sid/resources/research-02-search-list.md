# Research 02 — YouTube `search.list`

- **Source:** [Search: list reference](https://developers.google.com/youtube/data/reference/rest/v3/search/list)
- **Reviewed:** 2026-11-27
- **Requirements:** FR-1.3–1.4, FR-2.3, FR-3.4

## Distilled findings

- `search.list` retrieves matching video, channel, or playlist search results;
  the result itself is a search result representation, not a persistent resource.
- `type` and `part` should be explicit for predictable application behavior.
- Search results can be incomplete/delayed; they are unsuitable as a global
  enumeration mechanism.
- Recent uploads for a channel should be fetched through its uploads playlist,
  not inferred from search ordering.
- Search calls have their own quota accounting bucket under the current quota
  calculator.

## Project implication

Keep searches bounded, request only the intended resource types, and treat
search as candidate generation before application-side ranking. See [[brain/sid/resources/youtube-mcp-requirements#FR-1|FR-1]] and [[brain/sid/resources/youtube-mcp-requirements#FR-2|FR-2]].
