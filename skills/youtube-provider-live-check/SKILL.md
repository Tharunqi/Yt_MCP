---
name: youtube-provider-live-check
description: Run opt-in smoke tests against public YouTube Data API metadata.
---

# YouTube provider live check

This skill covers read-only provider and MCP discovery smoke checks for FR-1 and
FR-2. See the distilled API constraints in
[[brain/sid/resources/youtube-mcp-requirements]] and the stage review practices
in [[brain/sid/resources/second-brain-conventions]].

## Run

1. Confirm `.env` contains `YOUTUBE_API_KEY`; never display or copy its value.
2. From the repository root run:

   ```bash
   RUN_YOUTUBE_LIVE_TESTS=1 pytest -m live -s -v tests/live/test_youtube_provider_live.py
   ```

3. Set `YOUTUBE_LIVE_VIDEO_ID` to choose a public seed video. The discovery test
   invokes both read-only MCP tools and prints their bounded candidate results.
   It uses an in-memory quota ledger, so Docker/PostgreSQL is not required. It
   does not create or modify YouTube content.
4. Report each test as passed, failed, skipped, or blocked. Live requests use
   YouTube API quota; an empty channel result fails the discovery smoke test.
5. Record the date and a safe outcome summary in your own contributor log. Never
   include request URLs, credentials, or raw exception details that may contain
   the API key.

## Recorded run

- 2026-11-27: the live MCP test for `8vRhCUPB6Jk` first returned no similar
  channels. After changing FR-2 to use concise topic queries instead of full
  branded tag strings, it returned ten similar videos and nine similar
  channels. See [[brain/sid/log]] for the review.
  See [[brain/sid/log]] for the run record.
