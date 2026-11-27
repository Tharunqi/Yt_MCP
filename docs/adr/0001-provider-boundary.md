# ADR-0001: Isolate YouTube API calls behind provider adapters

- **Status:** Accepted
- **Date:** 2026-11-27
- **Decision owners:** Project team; implementation contribution by Sid and Tharun
- **Requirement links:** NFR-MAINT-01, NFR-COMP-01
- **Distilled Brain note:** [[brain/sid/resources/youtube-mcp-requirements]]

## Context

Feature logic needs stable metadata and domain errors without depending on
Google API client request objects. Tests should run without credentials or live
YouTube availability.

## Decision

Route YouTube Data API calls through provider methods in
`src/youtube_mcp/providers/youtube.py`. Feature modules consume provider
behavior and typed metadata. Tests substitute fakes/mocks. Use only the official
YouTube Data API v3.

## Consequences

Feature code can be tested independently and API details have one boundary.
Provider interfaces need coordinated changes when shared features add API
operations. The current module contains two provider classes for distinct
existing use cases; consolidating or formalizing protocols remains open.

## Evidence

Current consumers include discovery, engagement, and playlist modules. Provider
unit tests use fakes. See [architecture](../architecture/architecture.md) and
[traceability](../traceability.md).
