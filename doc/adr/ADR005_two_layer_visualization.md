## ADR-005: Visualize hate and support as two overlaid, semi-transparent time series, not a single intensity line

**Context**

A single toxicity-over-time line can't distinguish two very different
things that can both look like "a spike": a controversy that increases
hostility alone, versus a controversy that increases total engagement on
both sides at once — defenders showing up in greater numbers alongside
critics. These have different implications for what actually happened to
a creator's audience, and collapsing them into one line loses that
distinction entirely.

**Decision**

Render two semi-transparent, overlaid area series per creator: red for
hate/toxicity volume over time, green for support/"love" volume over
time, with a vertical marker at each detected change point (from
ADR-003). Where both series rise together, the controversy increased
total attention rather than only hostility; where only red rises, it did
not.

**Consequences**

- This requires a defined "love"/support signal, which is not yet
  finalized — open decision between reusing the `joy` dimension from the
  existing emotion classifier (cheap, approximate) or building a
  dedicated support-language marker (density of phrases like "so proud,"
  "don't listen to the haters" — same keyword-density approach as earlier
  `learning_language_ratio` work, more accurate, more effort). This ADR
  does not resolve that choice.
- The visualization is descriptive, not diagnostic on its own — it shows
  *that* both curves moved together or didn't, not *why*; the "why" comes
  from ADR-004's term-frequency extraction at the same change point.
