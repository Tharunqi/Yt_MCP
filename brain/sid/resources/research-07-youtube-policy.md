# Research 07 — YouTube API data policy

- **Source:** [YouTube API Services Developer Policies](https://developers.google.com/youtube/terms/developer-policies)
- **Reviewed:** 2026-11-27
- **Requirements:** NFR-COMP-01, NFR-PRIV-01, NFR-OPS-02, SEC-T

## Distilled findings

- Authorized-data clients must transparently describe collection, use, sharing,
  protection, and deletion of user data.
- Users must have a deletion path for stored API data, and revoked/invalid
  authorization requires deleting associated stored data within the policy
  period.
- The policies constrain deriving new metrics from API data; derived analytics
  and retention require careful policy review before product use.
- Do not request scopes for future/unbuilt functionality; consent must be
  informed and user-controlled.

## Project implication

This is a **release blocker for compliance review**, not a legal determination:
the team must review whether the proposed ranking and analytics use is permitted
and define privacy/deletion controls before persistence or release. See
[[brain/sid/resources/youtube-mcp-requirements]] and [[docs/requirements/srs]].
