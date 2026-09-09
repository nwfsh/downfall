## ADR-001: Scope the project around a single creator's downfall/recovery, not topic-level controversy

**Context**

The prior direction (`isthisragebait` v2) measured average toxicity and
emotional intensity across curated videos representing both sides of a
contentious topic (e.g. abortion), with side assigned at video-curation
time. That design was sound and avoided the authenticity-judgment problem
that ended v1, but it had a scope mismatch: "how controversial is this
topic" is a question about the world, and YouTube comments are only a
partial, surface-level window into it — a fuller answer would need
Reddit, news coverage, and other sources this project doesn't have.

A single creator's downfall is different: their YouTube audience's
reaction to them *is* fully contained within their YouTube comment
history. The question's natural boundary matches what the data source can
actually support.

Separately, an adjacent idea was raised and set aside: comparing hate
volume/type between matched pairs of male and female creators (grounded
in real research — Wotanis & McMillan 2014 found a female creator
received far more hostile comments than a male counterpart in a single
pair, but a 5-pair replication with N=6,000 comments did not find women
generally received more negative comments overall; other studies found
effects specific to sexist/appearance-based language rather than volume).

**Decision**

Reframe the project around a single creator's comment-section trajectory
over time: when did hostility spike, how far did it spread, and did it
recover. Drop topic-level, multi-video-curated-by-side analysis entirely.

Explicitly exclude any gender- or demographic-comparative analysis from
this project's scope. Reasons: (1) the underlying research findings are
genuinely mixed and sample-size-dependent — a rigorous version would need
a matched-pairs design across many creators, a significantly larger
project than this one; (2) for a professional portfolio project, this
angle risked reading as advocacy rather than data engineering, which
wasn't the intended framing.

**Consequences**

- Pipeline shifts from a curated, hand-picked video set (topic × side) to
  full-channel ingestion for one creator at a time (see ADR-002).
- No more human-in-the-loop "which side does this video represent"
  curation step — that entire piece of the prior design is dropped.
- If a gender- or demographic-comparative study is wanted later, it should
  be scoped as a separate project with its own matched-pairs design, not
  folded into this one.
