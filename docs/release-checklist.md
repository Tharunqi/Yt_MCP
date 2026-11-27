# Demo and Release Checklist

Release work is not complete until the required evidence is attached to a
reviewed PR. Do not create a release tag before the team approves the release.

## Product demo

- [ ] Use a clean test account/data set; do not show keys, tokens, or private
  account data.
- [ ] Demonstrate read-only health and discovery calls.
- [ ] Demonstrate FR-3/FR-4 authorization and data-source explanations where
  applicable.
- [ ] Demonstrate playlist preview, refusal/no-write path, explicit confirmation,
  and accurate partial-failure reporting.
- [ ] Demonstrate metadata-only FR-6 label and FR-7 descriptive analysis.
- [ ] Run the SK-1 flow through MCP and record the result in the PR and Brain log.
- [ ] Record a live brain-query answer with supporting note links.
- [ ] Trace one requirement from distilled note to ADR, issue, PR, code, and test.

## Release gate

- [ ] All FR-1–FR-7 and SK-1 acceptance evidence is complete.
- [ ] All tests, Ruff, build, secret scan, skill validation, and Brain validation
  pass in CI.
- [ ] PostgreSQL quota concurrency, OAuth scope/token handling, privacy, and
  playlist confirmation have review evidence.
- [ ] YouTube API Services policy review covers the app's derived ranking and
  analytics, data storage/retention/deletion, and user disclosures. Treat any
  unresolved policy concern as a release blocker.
- [ ] Stage reviews and TQ-7 skill evaluation are recorded.
- [ ] All code and Brain changes are reviewed through PRs; no direct `main`
  changes.
- [ ] Update [CHANGELOG](../CHANGELOG.md), obtain team approval, then create an
  annotated version tag.

## Current release status

**Not ready.** FR-3, FR-6, FR-7, and a complete SK-1 E2E remain incomplete.
FR-2 is implemented, but its ranking quality still needs evaluation. The latest
live test attempt was network-blocked; production/deployment decisions and team
review are outstanding.
