# Software Requirements Specification

- **Product:** YouTube Video Intelligence MCP Server
- **Baseline:** Team SRS dated 7 November 2026, updated to the seven-feature design baseline
- **Status:** Working project baseline; priorities and open decisions require team review.

This SRS consolidates the supplied SRS and workflow constraints. The distilled
feature source is [[brain/sid/resources/youtube-mcp-requirements]]. Detailed
source requirements and stakeholder assignments remain authoritative pending
team review. “Shall” denotes a required behavior; TBD items are not silently
resolved here.

## 1. Purpose and scope

The server exposes YouTube discovery, recommendations, account analytics,
metadata summaries, and playlist workflows through MCP. It owns validation,
bounded API access, deterministic ranking and calculations, quota accounting,
and safe gating of writes. The chatbot host owns conversation, consent
presentation, and the LLM. YouTube Data API v3 is the only YouTube data/action
source.

In scope: FR-1 through FR-7, SK-1 video-to-playlist workflow, OAuth, provider
isolation, and quota preflight. Out of scope: scraping; unofficial APIs or
transcript services; exhaustive/global search; watch history; metadata presented
as spoken-content summary; and persistence of inferred profiles or derived
analytics before policy review.

## 2. Actors and environment

- **Authorised end user:** requests features and grants minimum OAuth scopes
  where private data or writes are needed.
- **Chatbot host/LLM and MCP client:** plan user-facing conversations, discover
  and invoke tools, present previews, and obtain confirmation.
- **MCP server:** validates and executes deterministic application logic.
- **YouTube Data API v3:** supplies public metadata and authorized account data,
  and accepts permitted playlist writes.
- **SQL database:** stores quota records; future user preference and credential
  storage requires separate policy and security decisions.

The local environment uses Python, FastMCP over Streamable HTTP, Docker Compose,
and PostgreSQL 17. The production database topology is TBD.

## 3. Functional requirements

Priorities below follow the supplied SRS. Feature ownership follows the team
assignment in the source SRS. Status is linked to the [traceability matrix](../traceability.md).

### FR-1 — Similar videos (High; Sid)

Given a video URL or ID, validate it, fetch seed metadata, derive up to a bounded
set of queries from available metadata, search a bounded candidate pool, fetch
candidate details, remove seed and duplicates, rank application-side, and
return ranked links and short reasons. Malformed or unavailable seeds produce a
clear error before candidate search. Results describe the searched pool, not a
global guarantee. Ranking choice and weights require an ADR.

Detailed IDs: FR-1.1 identifier validation; FR-1.2 seed metadata; FR-1.3 query
derivation; FR-1.4 bounded candidate search/details; FR-1.5 seed/duplicate
removal; FR-1.6 metadata rank; FR-1.7 links/reasons.

### FR-2 — Similar channels (Medium; Sid)

Resolve a channel URL, handle, or ID; fetch public channel metadata and a bounded
sample of uploads; retrieve a bounded candidate set; derive channel profiles
from description and sampled upload metadata; rank candidates and exclude the
input channel. Do not enumerate all YouTube channels. The current implementation
uses up to ten recent uploads per channel, up to three search queries, and a
total candidate cap of ten. It scores channel-title overlap (10%), description
overlap (45%), upload terms recurring across the sample (30%), and all sampled
upload metadata overlap (15%). These are initial bounded defaults and should be
evaluated against representative examples; see
[ADR-0005](../adr/0005-fr2-channel-profiles.md).

Detailed IDs: FR-2.1 identifier resolution; FR-2.2 metadata and upload sample;
FR-2.3 bounded candidate search; FR-2.4 profile construction; FR-2.5 ranking and
input exclusion.

### FR-3 — Personalised recommendations (Medium; Viraj)

With read-only OAuth, read likes, subscriptions, and user-selected playlist
items; build a request-time preference profile; search topic candidates and
optionally sample subscribed-channel uploads; rank by topic similarity, creator
affinity, freshness, and diversity; exclude already liked/saved videos; explain
each result. No recommendation-feed endpoint or watch history is assumed. The
API returns at most 1,000 liked videos. Do not persist the inferred profile
before policy review.

Detailed IDs: FR-3.1 account connection; FR-3.2 authorized data retrieval;
FR-3.3 request-time profile; FR-3.4 bounded candidate acquisition; FR-3.5
multi-signal ranking; FR-3.6 exclusion; FR-3.7 explanations.

### FR-4 — Engagement analysis (Medium; Tharun)

Accept an inclusive analysis period and optional comparison period; retrieve
likes, subscriptions, selected playlist items, and video metadata; report top
channels/categories, duration statistics/distribution, weekly trends, and the
same metrics for the comparison period. Read at most 1,000 likes, 1,000
subscriptions, 1,000 items per playlist, and five selected playlists, with a
maximum of 20 pages per source. Filter likes by video publish date because
YouTube does not provide like dates. Use the API calendar dates for subscription
creation and playlist-item addition. Count a video once in video totals if it
appears in more than one source; count each playlist item in playlist trends.
Show sources, date ranges, limits, and missing data. Describe liked/saved
content, not actual watch time.

Detailed IDs: FR-4.1 period inputs; FR-4.2 bounded source retrieval; FR-4.3
top-channel and category grouping; FR-4.4 duration statistics; FR-4.5 weekly
time trends; FR-4.6 like-for-like comparison; FR-4.7 source/range and limit
explanations.

### FR-5 — Playlist generation and creation (High; Tharun)

Parse topic, total duration, maximum video length, language, title, and
visibility; search one relevance-ordered page of up to 50 candidates and fetch
their metadata; remove unavailable, duplicate, or constraint-breaking items.
Keep candidate order, allow an exact duration fit, and continue after items that
do not fit. Skip unknown duration and, when requested, unknown or different
language. Accept `private`, `unlisted`, or `public` visibility. Preview title,
item title, channel, duration, link, reason, total duration, and privacy setting.
Obtain explicit confirmation before playlist creation or item insertion. Verify
OAuth and channel availability before write; accurately report full or partial
outcomes. Reserve quota before each API workflow and account for 50 quota units
for playlist creation and each inserted item.

Detailed IDs: FR-5.1 request parsing; FR-5.2 candidate filtering; FR-5.3 planning;
FR-5.4 unknown metadata; FR-5.5 preview; FR-5.6 explicit confirmation; FR-5.7
authorization/channel checks; FR-5.8 missing-channel handling; FR-5.9 partial
write reporting. Exact-fit, candidate order, and visibility are settled as
described above and in [[brain/tharun/projects/fr4-fr5-design]].

### FR-6 — Metadata-based video summary (Medium; Viraj)

Return available title, channel, description, category, publication date, and
duration. Label the result as metadata-based and never imply it summarizes
spoken content. Transcript/content summarization is deferred pending eligible
source and policy decisions.

Detailed IDs: FR-6.1 available metadata; FR-6.2 metadata-only label; FR-6.3 no
claim about spoken content.

### FR-7 — Playlist/video analysis (Medium; Tharun)

Fetch playlist items and video metadata and return total duration, duration
distribution, channel/category counts, and item-level metadata summaries. Label
results descriptive and metadata-based. Review API policy before storing or
expanding derived analytics.

Detailed IDs: FR-7.1 retrieval; FR-7.2 total duration; FR-7.3 distribution;
FR-7.4 channel/category counts; FR-7.5 item summaries; FR-7.6 descriptive label.
The implementation provides one tool for a playlist ID and one for a video ID
or supported video URL. Playlist reads are capped at 1,000 items across 20
pages; repeated videos count as separate playlist items. Both tools return the
available duration, duration distribution, channel/category counts, and item
metadata. Missing metadata is marked and totals use known durations only.
Results remain request-scoped and are not stored. A YouTube API policy review
is still required before release or any storage/expansion of analytics.

### SK-1 — Video-to-playlist workflow (High)

Guide the assistant through FR-6 metadata summary, FR-1 similar-video discovery,
FR-5 constrained preview, clear preview of items/visibility, explicit user
confirmation, confirmed playlist creation, and FR-7 playlist analysis. Skills
guide host workflow and never replace server-side validation, deterministic
logic, API calls, or consent enforcement. Host/client support must be verified.

Subrequirements: SK-1.1 metadata summary; SK-1.2 similar videos; SK-1.3
constrained proposal; SK-1.4 preview and confirmation; SK-1.5 confirmed writes;
SK-1.6 final analysis.

## 4. Non-functional and cross-cutting requirements

- **NFR-QUOTA-01:** Track per-request quota and remaining budget.
- **NFR-QUOTA-02:** Reject over-budget work before the first API call.
- **NFR-QUOTA-03:** Reserve and settle quota atomically under concurrent requests.
- **NFR-SEC-01:** Use Google OAuth for private data/writes; minimum scopes; never
  collect passwords.
- **NFR-SEC-02:** Protect OAuth tokens at rest; separate credentials from
  preferences; never commit or log secrets.
- **NFR-SEC-03:** Validate tool parameters and external identifiers.
- **NFR-SEC-04:** Treat metadata as untrusted data, not instructions or consent.
- **NFR-PRIV-01:** Keep inferred profiles and derived analytics request-scoped
  until storage policy and user controls are approved.
- **NFR-COMP-01:** Official YouTube Data API v3 only; no scraping, unofficial
  APIs/transcripts, or quota evasion.
- **NFR-COMP-02:** Support reauthorisation after OAuth expiry.
- **NFR-COMP-03:** Complete a current YouTube API Services policy review of
  derived rankings/analytics, privacy disclosures, storage, retention, deletion,
  and consent before release; unresolved policy concerns block release.
- **NFR-OPS-01:** Provide repeatable Docker application/database setup.
- **NFR-OPS-02:** Keep secrets and real personal data out of logs/fixtures.
- **NFR-REL-01:** Report partial playlist-write outcomes accurately.
- **NFR-REL-02:** Handle quota, rate-limit, auth, channel, unavailable/private/
  deleted resource, and missing-metadata errors.
- **NFR-MAINT-01:** Isolate YouTube API calls behind a provider interface.
- **NFR-TEST-01:** Maintain unit, integration, negative, and MCP-interface E2E
  coverage.
- **NFR-TEST-02:** CI uses mocks/fixtures and does not depend on live YouTube.
- **NFR-TEST-03:** Add regression coverage for significant defects.
- **NFR-UX-01:** Preview playlist content/title/visibility and require explicit
  confirmation before any write.
- **NFR-PERF-01 / NFR-AVAIL-01:** Numeric response-time and availability targets
  are TBD.

## 5. Verification, acceptance, and governance

- **TQ-1:** Unit coverage for functions, features, tools, scoring, parsing, and
  planner constraints.
- **TQ-2:** Integration coverage across provider and feature components.
- **TQ-3:** E2E through MCP for FR-1–FR-7.
- **TQ-4:** Negative cases for malformed IDs, unavailable/private resources,
  missing metadata, quota, auth expiry, channel errors, and rate limits.
- **TQ-5:** CI uses mocks/fixtures, not live API.
- **TQ-6:** Verify quota preflight rejects before API access.
- **TQ-7:** Evaluate skills before each stage submission; record results.
- **TQ-8:** Maintain regression coverage as the system changes.
- **SEC-T:** Check minimum scopes, token safety, secret absence, input validation,
  metadata isolation, and fixtures/log privacy.
- **CI-T:** Build, lint, and automated tests run for PRs targeting `main`.
- **REV-T:** All changes use reviewed PRs; direct `main` commits are prohibited.

Acceptance criteria and current tests are in [traceability](../traceability.md)
and [testing records](../testing/).

## 6. Open decisions

Production SQL topology; migrations/schema versioning; OAuth app/redirect/token
encryption; FR-1/FR-2 ranking quality evaluation; FR-6 eligible content source;
FR-7 data retention; final MCP schemas/resources; skill host distribution;
performance/availability targets; retention/deletion controls; and priority
confirmation. These are tracked in the [development plan](../development-plan.md).
