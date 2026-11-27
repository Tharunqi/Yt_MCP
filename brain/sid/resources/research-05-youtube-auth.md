# Research 05 — YouTube API keys and OAuth

- **Source:** [Implement authorization](https://developers.google.com/youtube/data/guides/authentication)
- **Reviewed:** 2026-11-27
- **Requirements:** FR-3.1–3.2, FR-4.2, FR-5.6–5.7, NFR-SEC-01–02

## Distilled findings

- API keys identify a project and are appropriate for public-data requests where
  allowed.
- OAuth 2.0 is required for writes and private user data.
- OAuth scopes define access; request the narrowest scopes needed for the
  functionality currently implemented.
- The application must not collect Google passwords.

## Project implication

Keep public metadata access and account authorization paths separate. Request
playlist-write permission only at the confirmed write boundary. See
[[brain/sid/resources/youtube-mcp-requirements#Shared implementation constraints|shared constraints]] and [[brain/tharun/resources/second-brain-workflow]].
