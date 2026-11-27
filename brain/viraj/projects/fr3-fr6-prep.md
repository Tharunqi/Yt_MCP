\# FR-3 and FR-6 implementation prep



Source: `YouTube\_MCP\_SRS\_Super-dev.pdf`, repository README, source tree, provider/auth code, and traceability notes reviewed on 2026-11-27.



Requirements: FR-3, FR-6.



\## Scope



\- \*\*FR-3:\*\* Recommend videos using the authorized user's likes, subscriptions, and selected playlists. Build the preference profile for the current request, rank with topic similarity, creator affinity, freshness, and diversity, exclude videos already liked or saved, and explain each recommendation.

\- \*\*FR-6:\*\* Return available title, channel, description, category, publication date, and duration. Label the result as metadata-based; do not claim it summarizes spoken content.



\## Repository findings



\- The README reports FR-1, FR-2, FR-4, and implemented portions of FR-5 as current functionality.

\- `src/youtube\_mcp/recommendations/` and `src/youtube\_mcp/summarization/` currently contain only `\_\_init\_\_.py`.

\- `tests/unit/recommendations/` and `tests/unit/summarization/` contain only placeholders. The traceability table says no feature tests are identified.

\- The MCP server registers tools that call feature logic through a provider and quota preflight.

\- The authorized provider has methods for likes, subscriptions, playlist items by playlist ID, video search, and video details. Confirm how selected playlist IDs will be supplied before implementing FR-3.

\- YouTube credential loading defaults to read-only access and checks granted scopes.



\## Constraints to carry into implementation



\- Use the official YouTube Data API through the provider boundary.

\- Keep inferred profiles request-scoped; do not persist them.

\- Account for the API limit of up to 1,000 liked videos.

\- Use mocked or recorded data for automated checks. Never put credentials, tokens, or real personal data in notes or fixtures.



\## Session review



\- \*\*Worked:\*\* Updated `main`, returned to `feature/viraj-fr3-fr6`, and confirmed the feature branch is clean. Mapped the feature modules, server pattern, provider methods, auth setup, and test locations.

\- \*\*Still to confirm:\*\* How users select playlists and provide those playlist IDs to FR-3.

\- \*\*Next:\*\* Check the existing data models and MCP/API documentation before settling the FR-3 and FR-6 interfaces.



Related notes: \[\[brain/tharun/resources/second-brain-workflow]], \[\[docs/requirements/srs]], \[\[docs/traceability]].



No issue or PR IDs were available during this review.

