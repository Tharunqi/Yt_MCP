# Team Collaboration

Ongoing responsibility for keeping the shared YouTube MCP project easy to review and safe to integrate.

- Work on a personal branch from the latest `main`; submit changes through a PR targeting `main`.
- Keep commits focused and review the staged diff before committing.
- Coordinate changes to shared modules, project configuration, Docker files, and CI.
- Keep each person's notes authored and maintained by that teammate; preserve attribution in Git history.
- Keep secrets and local workspace settings out of tracked files.
- Keep `brain/log.md` aligned with actual Git history: one entry per commit, with any prepared pending entry clearly identified and no invented commit IDs.
- The FR-1 SQLAlchemy ledger uses the existing PostgreSQL service; schema migrations are deferred and missing tables are created from model metadata. Verify PostgreSQL locking before relying on cross-instance quota coordination.

References: [[Team]], [[youtube-mcp-requirements]], and [[second-brain-conventions]]. The repository setup and branch guidance is distilled from the team development guide.
