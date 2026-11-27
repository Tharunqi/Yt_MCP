# YouTube MCP project

## Scope and status

- [[Tharun]] owns FR-4 Engagement Analysis, FR-5 Playlist Generation and Creation, and FR-7 Playlist/Video Analysis.
- FR-4 is implemented. A read-only live check on 2026-11-26 returned one video for 2026-11-01 through 2026-11-26.
- FR-5 is implemented. A live preview on 2026-11-26 selected 21 videos for 12m 12s, showed 17m 48s remaining, and excluded 29 videos. The user later confirmed a preview and reported that playlist creation succeeded.
- FR-4 and FR-5 choices and diagrams are recorded in [[fr4-fr5-design]].
- FR-4/FR-5 decisions and quota checks are in [[fr4-fr5-design]]. FR-7 implementation and limits are in [[fr7-playlist-analysis]].

## Decisions

- Use read-only access for analysis and previews. Ask for write access only after explicit playlist confirmation.
- Keep the playlist plan within the requested time and show skipped videos and remaining time.
- FR-7 uses a bounded, request-scoped analysis. The read-only live check passed; the policy review remains open.
- FR-4 trends use the available subscription-created and selected-playlist-item-added dates. Like dates are unavailable, so the video publish date is the filter.
- The FR-4 and FR-5 design, accepted rules, and quota checks are in [[fr4-fr5-design]].
- Keep this note linked to [[second-brain-workflow]] and [[brain/tharun/log]]. Requirement IDs: FR-4, FR-5, FR-7.
- GitHub issue and PR links: not available yet. Add them when created.

## Review checkpoint — 2026-11-26

- Worked: FR-4 returned live account data; FR-5 returned a live preview; 26 unit checks passed for the FR-5 commit.
- Did not: the Docker rebuild timed out while downloading a dependency. Playlist creation was not part of this session; it was tested later after the user confirmed the preview.
- Change next: complete the final SRS/SDLC review of FR-4, FR-5, and FR-7. The preview and confirmed creation flow have been checked.

This is a checkpoint, not final Stage 3 or Stage 4 sign-off. See [[brain/tharun/log]] and [[ai-session-2026-11-26-fr4-fr5-live-check]] for the run records.
