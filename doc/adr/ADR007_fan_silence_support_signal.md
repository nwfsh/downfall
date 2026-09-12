## ADR-010: Track support withdrawal ("fan silence") as a third time-series signal alongside directed hate

**Context**

The existing pipeline detects downfalls via directed hate volume (ADR-006)
and identity-hate ratio shifts (Signal 3, the core interaction). Both
are active-hostility signals — they detect when people are saying
negative things at the creator. Neither detects passive withdrawal: a
creator whose core fanbase goes quiet (support comments dropping off)
while hate stays flat is experiencing a real downfall that the current
signals miss entirely. "Fans going silent" is a meaningfully different
phenomenon from "haters showing up" — they can occur independently, and
distinguishing them changes what a result actually means.

Four distinct patterns become distinguishable with a support signal:

| Hate | Support | Meaning |
|---|---|---|
| ↑ | ↓ | Classic cancellation — hostility rising, fans withdrawing |
| ↑ | ↑ | Controversy driving both sides — polarizing, not cancelled |
| flat | ↓ | Fans drifting away quietly — slow burnout, no spike event |
| ↓ | ↓ | Creator becoming irrelevant — full audience withdrawal |

Without a support signal, patterns 3 and 4 are invisible to the pipeline.

**Decision**

Add support volume as a third time series, tracked alongside directed
hate volume. Measure support as a *proportion of total engagement* (not
raw volume), since total comment volume fluctuates with algorithm reach
and is not a stable denominator — a support drop from 40% to 5% of
total comments is the signal, not raw support comment count.

For the support signal itself: use the `joy` dimension from the existing
`j-hartmann/emotion-english-distilroberta-base` emotion classifier,
already planned for the Silver layer. This is an approximation — "joy"
in a comment isn't identical to "defending or supporting this creator"
— but it is cheap, consistent with the existing stack, and avoids
introducing a new dependency. A dedicated support-language keyword
marker (density of phrases like "so proud," "don't listen to the
haters," "we still support you") was considered as a more accurate
alternative and remains a possible future enhancement, not the default.
The choice between these was explicitly deferred in OPEN_QUESTIONS.md —
this ADR resolves it in favor of the joy-classifier approach.

This also resolves the ADR-005 visualization's open question about the
"love" signal definition: the green area series in the two-layer
hate/support chart uses the joy-dimension proportion as its input.

**Consequences**

- The `joy` dimension is an imperfect proxy for fan support — a comment
  expressing joy about the video's topic (e.g. "so happy for the person
  in this story!") would score high on joy without being support for the
  creator. This is an accepted approximation at this stage; the signal
  is most reliable when read at the aggregate/trend level rather than
  per-comment.
- Change-point detection (ADR-003) should be run independently on the
  support-proportion time series, not only on the hate time series —
  a change point in support without a corresponding hate change point
  is itself a meaningful finding (fans quietly leaving without active
  hostility increasing).
- Three time series now need to be produced in the Gold layer:
  directed-hate proportion, identity-hate ratio (Signal 3), and
  support proportion. All three share the same change-point detection
  method and term-frequency reason-inference step (ADR-004) at their
  respective detected change points.
- The two open decisions in OPEN_QUESTIONS.md are now both resolved
  by this ADR (love signal definition) and by the Perspective API
  shutdown (subscriber-data axis dropped — comment-based signals only).
  OPEN_QUESTIONS.md can be retired.
