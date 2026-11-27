# ADR-0005: Rank bounded channel profiles from sampled uploads

- **Status:** Accepted as revised FR-2 implementation defaults; quality evaluation pending
- **Date:** 2026-11-27
- **Decision owner:** Sid
- **Requirement links:** FR-2.1–FR-2.5, NFR-QUOTA-01–03
- **Distilled Brain note:** [[brain/sid/resources/youtube-mcp-requirements#FR-2|FR-2 requirements]]

## Context

The YouTube Data API has no supported related-channel endpoint. FR-2 needs to
form channel profiles from public metadata and bounded recent uploads without
attempting to enumerate YouTube channels or spending unbounded quota.

## Decision

- Resolve the supplied channel URL, handle, or ID and sample up to ten recent
  uploads. FR-2 operates on this channel profile; a video URL is not its input.
- Build searches from the channel description and terms recurring across the
  sampled uploads. Fall back to upload terms when the profile is sparse. Remove
  the seed's own name/handle as phrases, rather than maintaining a list of
  channel-specific brand terms. Keep the total candidate cap at ten.
- Sample up to ten recent uploads from each candidate.
- Score channel-title overlap at 10%, description overlap at 45%, terms that
  recur across sampled uploads at 30%, and all sampled-upload
  title/description/tag overlap at 15%, using deterministic Jaccard token
  overlap. Recurrence is a generic channel-level signal; it does not assume a
  specific content category or format.
- Exclude the input channel and duplicate IDs; sort ties by channel ID.
- Estimate and reserve a conservative quota amount before the first API call;
  settle against actual attempted API requests.

## Alternatives considered

- Search only by channel title: inexpensive, but weak for channels whose name
  does not describe their topics.
- Use only channel descriptions: misses channels with sparse descriptions.
- Search videos and infer channel similarity: can overrepresent one upload and
  needs a separate candidate-to-channel aggregation rule.
- Embeddings: adds model cost, service dependency, evaluation, and data-policy
  review requirements.

## Consequences

The result is bounded, deterministic, explainable, and testable with fixtures.
It is not a global similarity guarantee, and lexical overlap cannot infer
semantic relationships that are absent from metadata. Sparse descriptions or
uploads can reduce accuracy. The sample/candidate defaults and weights need
evaluation on representative examples before setting quality targets. YouTube
policy review must clear derived similarity scoring before release.
