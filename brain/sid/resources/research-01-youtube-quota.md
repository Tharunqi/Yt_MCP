# Research 01 — YouTube Data API quota

- **Source:** [YouTube Data API quota calculator](https://developers.google.com/youtube/data/determine_quota_cost)
- **Reviewed:** 2026-11-27
- **Requirements:** NFR-QUOTA-01–03, FR-1.4, FR-2.3

## Distilled findings

- API methods draw from quota buckets; `search.list` has its own Search Queries
  bucket, and other methods draw from the standard bucket in the current
  allocation model.
- Every request, including invalid requests, has a quota cost. Additional
  paginated requests cost quota independently.
- Daily quota resets at midnight Pacific Time according to the calculator.
- Google may change quotas/costs; configured local limits are estimates, not
  authoritative live account balances.

## Project implication

Keep estimates configurable, bound candidate pools, preflight before the first
call, record actual attempted calls, and recheck the official calculator before
releasing quota-sensitive changes. See [[brain/sid/resources/youtube-mcp-requirements#Quota model|quota model]] and [[brain/sid/projects/youtube-mcp-discovery]].
