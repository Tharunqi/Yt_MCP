# Defect and Regression Log

This log separates confirmed product defects from environment blockers and
unverified design risks. Each confirmed product defect should get a regression
test before it is closed. Link a GitHub Issue when one is created; no issue IDs
are invented.

| Ref | Type | Observation | Status / evidence | Follow-up |
|---|---|---|---|---|
| ENV-001 | Environment blocker | Live provider test host could not resolve `youtube.googleapis.com`; no API response was received. | Blocked on 2026-11-27; not a product defect diagnosis. | Re-run from network-enabled developer machine and record safe result. |
| ENV-002 | Environment blocker | Docker Compose could not connect to the local Docker daemon (`docker.sock` absent), so app/database startup and MCP fetch could not run. | Blocked on 2026-11-27; no containers were started. | Start Docker Desktop, then follow the local-check skill. |
| VAL-001 | Local tooling gap | `.venv` did not contain the `build` package, so local `python -m build` could not start. | CI dev dependency now includes `build`; no local build result yet. | Install dev extras and run build locally; confirm CI build. |
| RISK-001 | Verification risk | SQLAlchemy ledger unit tests use SQLite; PostgreSQL concurrency/locking has not been exercised. | Open; described in ADR-0003. | Add PostgreSQL integration test before deployment reliance. |
| GAP-001 | Coverage gap | FR-3, FR-6 and FR-7 have no feature tests identified in this checkout. | Open per traceability matrix. | Add unit, integration, negative, and MCP E2E tests with each feature. |
| GAP-002 | Release-readiness gap | Full SK-1 flow and local Docker/MCP smoke have not been executed; FR-6/FR-7 are incomplete. | Open; skill evaluation is not E2E evidence. | Finish features and record end-to-end demo evidence. |

No confirmed new product defect was found in the checks run for this change set.
