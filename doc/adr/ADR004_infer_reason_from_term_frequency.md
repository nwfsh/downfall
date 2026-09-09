## ADR-004: Infer the reason for a downfall or recovery from comment term-frequency, applied per change point

**Context**

Knowing *why* a creator's comment section turned hostile, or later
recovered, matters for the project to be useful — but YouTube's API
returns only comments and metadata, no external news context. This is a
different kind of problem than the manufactured-vs-earned emotion
question that ended `isthisragebait` v1: that required judging whether a
reaction was *authentic*, which text doesn't support. Identifying *what
topic* people are discussing during a given window is a standard,
well-established NLP task — it requires no authenticity judgment, only
detecting which terms/phrases are unusually frequent compared to a
baseline.

**Decision**

At each change point detected in ADR-003, automatically extract candidate
reason terms by comparing comment text in the window immediately
following the change point against a baseline window immediately
preceding it, using term-frequency comparison (TF-IDF or n-gram frequency
delta) to surface newly over-represented terms/phrases. The same method
runs in reverse at a recovery change point — comparing the recovery
window against the peak-hostility window — to surface what's newly
frequent there instead (e.g. "apologized," "old news").

Topic modeling (LDA/BERTopic) was considered and set aside as a possible
future enhancement rather than the default — term-frequency comparison is
lighter-weight, more explainable, and keeps this project's positioning as
data engineering with an applied inference layer rather than a heavier
ML-engineering build.

A human still reviews the extracted candidate terms to write the final
one-line "reason" — a lightweight confirmation step, not manual research
from scratch.

**Consequences**

- The precise claim this supports: "here's what commenters were
  collectively saying caused the spike/recovery" — the audience's own
  account, not a verified external fact. If comments are dominated by a
  rumor or misinterpretation, that's what gets surfaced, consistent with
  this project's overall scope of measuring audience discourse rather
  than adjudicating truth.
- Sometimes no coherent reason will surface at all — e.g. a recovery
  driven by attention simply fading rather than any specific reconciling
  moment. This is a legitimate, reportable result, not a pipeline
  failure.
- "Forgiven" is an informal framing only, not the literal claim this
  signal supports. Pipeline output should be phrased as "hostile
  discourse de-escalated" or similar — the measured signal is
  de-escalation of hostility, not a moral judgment that an audience
  genuinely forgave someone.
- Because this runs per change point rather than once globally, a creator
  with multiple controversies gets a separate, independently-derived
  reason for each — avoiding a blended or misattributed explanation
  across their whole history.
