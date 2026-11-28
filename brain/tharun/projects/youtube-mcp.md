# YouTube MCP project

## Scope and status

- [[Tharun]] owns FR-4 Engagement Analysis, FR-5 Playlist Generation and Creation, and FR-7 Playlist/Video Analysis.
- FR-4 is implemented; its read-only live check passed.
- FR-5 is implemented; the live preview passed, and the owner confirmed a playlist was created after approval.
- FR-4 and FR-5 choices and diagrams are recorded in [[fr4-fr5-design]].
- FR-4/FR-5 decisions and quota checks are in [[fr4-fr5-design]]. FR-7 playlist/video tools, limits, diagrams, and checks are in [[fr7-playlist-analysis]].

## Decisions

- Use read-only access for analysis and previews. Ask for write access only after explicit playlist confirmation.
- Keep the playlist plan within the requested time and show skipped videos and remaining time.
- FR-7 has bounded playlist/video analysis. Playlist and single-video live checks passed; the policy review remains open.
- FR-4 trends use the available subscription-created and selected-playlist-item-added dates. Like dates are unavailable, so the video publish date is the filter.
- The FR-4 and FR-5 design, accepted rules, and quota checks are in [[fr4-fr5-design]].
- Keep this note linked to [[second-brain-workflow]] and [[brain/tharun/log]]. Requirement IDs: FR-4, FR-5, FR-7.
- FR-7 GitHub issue: [#9](https://github.com/Tharunqi/Yt_MCP/issues/9). Add the PR link after opening it.

## Review checkpoint — 2026-11-26

- Worked: FR-4 live read and FR-5 preview passed; playlist creation was checked later after confirmation.
- Did not: the Docker rebuild timed out while downloading a dependency. Playlist creation was not part of this session; it was tested later after the user confirmed the preview.
- Change next: complete the final SRS/SDLC review of FR-4, FR-5, and FR-7. The preview and confirmed creation flow have been checked.

This is a checkpoint, not final Stage 3 or Stage 4 sign-off. See [[brain/tharun/log]] and [[ai-session-2026-11-26-fr4-fr5-live-check]] for the run records.
