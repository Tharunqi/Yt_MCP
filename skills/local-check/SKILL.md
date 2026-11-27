---
name: local-check
description: Build, test, run, and smoke-check the YouTube MCP service locally.
---

# Local check

Use this workflow before requesting review. See the distilled project and safety
constraints in [[brain/sid/resources/youtube-mcp-requirements]] and the repository
conventions in [[brain/sid/resources/second-brain-conventions]].

## Checks

Run from the repository root. If the virtual environment does not exist, create
it with `python3 -m venv .venv`; then activate it with `source .venv/bin/activate`.
Report each result as **passed**, **failed**, **skipped**, or **blocked**. Do not
describe a blocked network check as a pass.

1. Install the project and development tools: `python -m pip install -e ".[dev]"`.
2. Build distributions: `python -m build`.
3. Check formatting and lint: `ruff check src tests scripts`.
4. Run automated tests: `pytest -p no:cacheprovider tests`.
5. Start the local PostgreSQL and MCP services: `docker compose up --build -d`.
   Check service health with `docker compose ps` and logs with
   `docker compose logs --tail=100 app db`.
6. Open the MCP server at `http://localhost:8000/mcp` in an MCP client such as
   MCP Inspector. Call `health_check`, then use the read-only
   `find_similar_videos` tool with a public video URL and
   `find_similar_channels` with a public channel URL or handle. Do not call
   `create_playlist_from_preview` during this smoke check.
7. Stop services with `docker compose down` when finished. Preserve database
   state unless the user asks to remove it; do not use `-v` by default.

The live YouTube request requires `YOUTUBE_API_KEY` in the ignored local `.env`.
Never print, paste, or record the key. If external network access is unavailable,
mark the read-only fetch as blocked and include the safe error category only.

After a significant run, add the date, command, outcome, what worked, what did
not, and the next action to your own `brain/<contributor>/log.md` as described by
[[brain/sid/resources/second-brain-conventions]]. Do not author another member's
review note.
