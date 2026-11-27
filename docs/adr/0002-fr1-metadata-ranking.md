# ADR-0002: Rank FR-1 candidates with weighted metadata overlap

- **Status:** Accepted for current FR-1 implementation; review if product evidence changes
- **Date:** 2026-11-27
- **Decision owner:** Sid
- **Requirement links:** FR-1.3–FR-1.7
- **Distilled Brain note:** [[brain/sid/resources/youtube-mcp-requirements#FR-1|FR-1 requirements]]
- **Implementation note:** [[brain/sid/projects/youtube-mcp-discovery]]

## Context

YouTube does not expose a supported related-videos endpoint for this workflow.
The application searches a bounded candidate pool and needs explainable ranking
that works without an additional model service.

## Decision

Use application-side weighted Jaccard overlap over available title (45%), tags
(30%), description (20%), and exact category (5%). Return short reasons for
matching metadata. Missing signals contribute zero. Use video ID for deterministic
tie-breaking. Report results as best matches within the bounded pool, not global
similarity.

## Alternatives considered

- TF-IDF/cosine: potentially richer text weighting, but adds feature/vector
  decisions and evaluation needs.
- Embeddings: may improve semantics but adds a model/API dependency, cost, and
  privacy review.
- YouTube related-video endpoint: unavailable/deprecated and therefore not used.

## Consequences

The implementation is deterministic, inspectable, and testable with fixtures.
It may miss semantic similarity not represented in metadata. Weights and
candidate quality need evaluation against a labelled set before claiming quality
targets.
