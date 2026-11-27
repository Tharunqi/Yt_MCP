# YouTube Video Intelligence MCP Server

A Python MCP server for bounded YouTube video/channel discovery, account
engagement analysis, and user-confirmed playlist creation. The current codebase
implements FR-1, FR-2, FR-4, and the implemented portions of FR-5; see the [requirements](docs/requirements/srs.md)
and [traceability matrix](docs/traceability.md) for the project-wide status.

## Local development

1. Install Python 3.12+, Docker Desktop, and Docker Compose.
2. Create a local `.env` from `.env.example`; set a YouTube API key for public
   discovery/live tests and use private OAuth files only when account features
   are needed. Compose passes the key from local `.env` to the app container.
   Never commit `.env` or OAuth files.
3. Create/activate the virtual environment and install developer tools:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -e ".[dev]"
   ```

4. Build and check locally:

   ```bash
   python -m build
   ruff check src tests scripts
   python scripts/validate_repository_docs.py
   pytest -p no:cacheprovider tests
   ```

5. For the PostgreSQL-backed MCP server, use `docker compose up --build -d`.
   Connect an MCP client to `http://localhost:8000/mcp`; see the [local-check
   skill](skills/local-check/SKILL.md) for a read-only smoke workflow.

Live provider checks are opt-in and make real, low-cost public API requests:

```bash
RUN_YOUTUBE_LIVE_TESTS=1 pytest -v tests/live/test_youtube_provider_live.py
```

## Documentation

- [Software requirements specification](docs/requirements/srs.md)
- [Architecture and data model](docs/architecture/architecture.md)
- [MCP tool reference](docs/api/mcp-tools.md)
- [ADRs](docs/adr/)
- [Development plan](docs/development-plan.md)
- [Traceability](docs/traceability.md)
- [Testing and skill evaluations](docs/testing/)
- [Release checklist](docs/release-checklist.md)
