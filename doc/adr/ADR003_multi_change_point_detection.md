## ADR-003: Detect downfall/recovery via multi-change-point detection (PELT), not a fixed toxicity threshold

**Context**

No creator has zero hate comments — small, routine negative comments are
normal background noise for any public creator, not evidence of a
downfall. A fixed toxicity threshold would either flag routine noise as a
"controversy" (set too low) or miss real downfalls for creators whose
baseline is already elevated (set too high, or too low for a normally
calm creator). Separately, a creator can have multiple, separate
controversies across their history — a single global before/after split
can't distinguish which controversy caused which later spillover, and
risks misattributing old-video hate to the wrong trigger entirely.

**Decision**

Use PELT (Pruned Exact Linear Time; Killick et al., 2012) for change-point
detection, run per-creator against their own comment-toxicity time
series. PELT detects the optimal *number and location* of change points
simultaneously, via a penalized cost function — it does not assume a
single split, so a creator with multiple controversies produces multiple
detected regimes rather than being forced into one binary comparison.

The resulting timeline is segmented into regimes bounded by the detected
change points. Any comment — including a spillover comment on an old,
previously-published video — is attributed to whichever regime its
`publishedAt` timestamp falls into, not to a single global split. Each
detected change point is treated independently downstream (see ADR-004).

Recovery is detected the same way, in reverse: a later change point where
an elevated regime shifts back down and stays there.

**Consequences**

- The penalty parameter is a critical tuning input, not a default to
  leave alone. Simulation research on PELT found an average of 19 false
  change points detected across series with zero real change points when
  the penalty was set too loosely — this must be tuned per-creator
  against their own baseline noise before results are trustworthy.
- Before trusting output on an unknown creator, the detector should be
  calibrated against a small set of known cases — a creator with a
  well-documented single controversy, and a creator with none — the same
  discipline as composite-score calibration in this project's earlier
  pivots.
- This adds a real dependency (a change-point detection library, e.g.
  Python's `ruptures`, which implements PELT) to the Gold-layer
  processing step, beyond PySpark aggregation alone.
