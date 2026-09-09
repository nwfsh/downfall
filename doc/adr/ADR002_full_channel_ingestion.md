## ADR-002: Full-channel ingestion via uploads-playlist enumeration, in two modes

**Context**

Detecting a downfall requires seeing whether hostility spills over onto a
creator's *old*, previously-published videos after a trigger event — not
just the video that caused the controversy. This means every video a
channel has ever posted needs to be ingestable, not a curated handful.
Separately, the project also wants to catch a *future* decline as it
happens for a creator being actively monitored, not only reconstruct past
ones.

**Decision**

Enumerate a channel's full video catalog via `channels.list` (to get the
channel's auto-generated "uploads" playlist ID) followed by paginated
`playlistItems.list` calls against that playlist — not `search.list` by
channel ID, which is costlier and less complete for this purpose. Every
returned video ID is then run through the existing `ingest_video()`
pipeline (unchanged from prior pivots).

Two ingestion modes:
- **Backfill** — one-time, full-history pull for a creator with a known
  past incident. Reconstructs the whole timeline retroactively, since
  comments already carry a `publishedAt` timestamp — no need to have been
  polling in real time to build the history.
- **Recurring** — daily pull, same shape as the existing Airflow DAG, for
  creators being actively monitored going forward, to catch a future
  decline as it happens rather than only after the fact.

**Consequences**

- Quota cost scales directly with channel size — a channel with hundreds
  of videos, each with its own full comment-thread pull (including the
  existing reply-completeness logic), can burn through a day's quota on
  its own. Channel size should be checked before running a backfill, and
  a large backfill may need to be spread across multiple days.
- The Airflow DAG needs two distinct job shapes going forward: a
  parameterized one-time backfill job (per channel) and the existing
  daily recurring job, rather than one single DAG shape.
- No side-curation step is needed at this stage (see ADR-001) — every
  video in the channel is ingested, not a hand-picked subset.
