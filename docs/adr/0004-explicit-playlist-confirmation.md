# ADR-0004: Require an explicit preview confirmation before playlist writes

- **Status:** Accepted product safety rule
- **Date:** 2026-11-27
- **Decision owner:** Project team
- **Requirement links:** FR-5.5–FR-5.9, SK-1.4–SK-1.5, NFR-UX-01, NFR-SEC-04
- **Distilled Brain note:** [[brain/tharun/resources/second-brain-workflow]]

## Context

Playlist creation changes a user's account. A conversational model or untrusted
video metadata must not initiate or alter that write without informed user
consent.

## Decision

Show the title, selected videos, durations, total duration, and visibility in a
preview. Require an explicit confirmation signal before creating the playlist or
adding videos. The application enforces the confirmation and reports partial
write results accurately.

## Consequences

The user can review the exact intended change and decline without a write.
Workflow skills and hosts must preserve the preview/confirmation sequence. The
server remains the enforcement boundary even if a host skill is unavailable.
