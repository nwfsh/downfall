**downfall**

*A data engineering project tracking when a YouTube creator's audience
reaction turns sharply negative, how far it spreads, and whether it
recovers — measured entirely from comment-section data over time.*

# 1. The Question

When a creator has a public downfall, three things are usually asked
informally, but rarely measured: when did it actually start, how far did
the backlash spread beyond the triggering video, and did it ever let up?
This project answers those from data:

- At what point in time did hate/toxicity in a creator's comment sections
  measurably spike, relative to their own baseline?
- Did the spike spill over onto *old* videos (new hostile comments arriving
  on unrelated, previously-published content after the trigger date)?
- Did negative *and* positive engagement both rise together (a
  controversy drawing more total attention, both defenders and critics),
  or just negative?
- Did the comment-level hate/toxicity signal recover toward baseline after
  the spike, and if so, how long did that take?

# 2. Origin — Third pivot from `isthisragebait`

This project has changed shape twice before landing here:

1. **middleground** — a YouTube debate-polarization tracker, abandoned
   partly due to noisy debate-format comments and partly because it needed
   to infer *which side* an ambiguous comment favored — a hard,
   circularity-prone problem.
2. **isthisragebait (v1)** — tried to classify comment sections as
   "ragebait" vs. "genuinely educational" using a manufactured-vs-earned
   emotion framing. Dropped because that authenticity distinction isn't
   reliably detectable from text alone — confirmed against research on
   emotional-authenticity detection in facial/vocal expression (a richer-
   signal domain than text, where this is still an open, actively-studied
   problem).
3. **isthisragebait (v2), topic-controversy tracker** — pivoted to
   measuring average toxicity/emotional intensity across curated videos on
   both sides of a contentious topic (side assigned by curation, not
   inferred). Sound and buildable, but scoped away from in favor of this
   project because YouTube comments alone are a partial, surface-level
   view of how a *topic* is really being discussed (compared to Reddit,
   news, etc.) — a mismatch between the question's scope and what the
   data source can actually support.
4. **downfall (current)** — reframed around a single creator instead of a
   topic. This question's natural boundary matches YouTube's data
   boundary: a creator's YouTube-audience reaction *is* fully contained in
   their YouTube comment history, so there's no cross-platform gap to
   worry about.

# 3. Scope Boundaries

This project measures **aggregate comment-section behavior over time for
one creator** — volume, toxicity, and emotion trends. It does not attempt
to judge whether a creator's downfall was deserved, whether their
apology/response was genuine, or make any claim about the underlying
controversy's merits. Those would require the same authenticity/legitimacy
judgment that sank `isthisragebait` v1, and this project deliberately
avoids it.

**"The reason" for a spike is identified manually**, not automated —
YouTube's API returns comments and metadata, not news context. Confirming
what actually happened around a detected spike date is a human research
step, same as curated video-side assignment was in the topic-controversy
version.

**No gender or cross-creator comparative claims.** Earlier discussion
considered a matched-pairs gender-comparison design (do women creators
face disproportionate backlash) — grounded in real, mixed academic
findings (Wotanis & McMillan 2014 found this in a single pair; a 5-pair
replication did not; other studies found the opposite or found effects
specific to sexist language rather than volume). That angle is explicitly
out of scope here — this project is a single-creator timeline tool, not a
comparative study.

# 4. Architecture — Bronze / Silver / Gold (extends middleground/isthisragebait)

| **Layer** | **Contents** | **Notes** |
| --- | --- | --- |
| Bronze | Raw comment + video metadata, **full-channel**, not curated subset | Two ingestion modes: **backfill** (one-time, full history, for a creator with a known past incident) and **recurring** (daily, for creators being monitored going forward — reuses the existing Airflow DAG shape) |
| Silver | Comments scored for toxicity (Perspective API) and emotion, indexed by comment `publishedAt` (not video publish date) — this is what makes spillover-to-old-videos detection possible | Toxicity/emotion scoring not yet wired in (same status as prior pivots) |
| Gold | Per-creator time series: rolling toxicity/hate volume, rolling support/"love" volume, change-point flags, recovery status | Not started |

# 5. Signals

- **Hate/toxicity volume over time** — rolling average of `avg_toxicity`, primary signal for detecting the spike
- **Support/"love" volume over time** — **open decision**: either reuse the `joy` dimension from the existing emotion classifier (cheap, approximate), or build a dedicated support-language marker (density of phrases like "so proud," "don't listen to the haters" — same keyword-density approach as earlier `learning_language_ratio` work, more accurate, more effort)
- **Change-point detection** — statistical detection of where the rolling toxicity average shifts, marking the likely start of a downfall
- **Spillover** — new hostile comments arriving on old, previously-published videos after the detected trigger date
- **Recovery** — does the rolling toxicity average return toward its pre-spike baseline, and how long does it take

**Explicitly not measured:** subscriber count over time. YouTube's public
Data API only returns a channel's *current* subscriber count — there is
no historical time series available for a channel you don't own.
**Open decision:** either integrate a third-party estimator (e.g. Social
Blade — ToS/API terms unverified) for a subscriber-based recovery signal,
or drop that axis and define "recovery" using comment-based toxicity
trends only.

# 6. Visualization

A two-layer, semi-transparent area chart per creator: red for hate/
toxicity volume, green for support/love volume, both over time, with a
vertical marker at the detected trigger date. Purpose: distinguish a
downfall that increases *only* hostility from one that increases *total*
engagement on both sides at once (defenders and critics both showing up
in higher numbers).

# 7. Known Limitations

- "The reason" behind a detected spike is inferred automatically as
  candidate terms (term-frequency comparison against a baseline window),
  with a human reviewing the candidates to write the final one-line
  reason — not fully automated, and not manual research from scratch
  either. See downfall ADR-004.
- Change-point detection identifies *when* a shift happened, not *why* —
  correlation with a nearby video's publish date is not the same as
  confirmed causation.
- No claim is made about whether backlash was deserved, proportionate, or
  based on accurate information — this project measures reaction, not
  legitimacy.
- Subscriber-based recovery tracking is either unavailable or dependent on
  an unverified third-party source (open decision, see §5).
- "Love"/support signal definition is not yet finalized (open decision,
  see §5).
- **Scale limitation: full-channel backfill is impractical for the
  largest creators under YouTube's default API quota (10,000 units/day).**
  Comment-pull cost scales with comment volume per video, not just video
  count — a single high-comment video can cost hundreds of quota units on
  its own. A full backfill on a creator with thousands of videos (e.g.
  PewDiePie) would realistically take weeks under the default quota, not
  days, absent a quota increase from Google (which has its own review
  process and isn't guaranteed). This pipeline, as designed, is better
  suited to small-to-mid creators than platform-scale ones for full
  historical backfill. For calibration against known cases specifically,
  this is worked around by bounding ingestion to a window around the
  known event date rather than pulling full channel history — see the
  calibration test set (§8) and ADR-002.
- **Comment data is incomplete by construction, and backfill sees a more
  incomplete version than real-time monitoring does.** YouTube's own
  moderation removes or hides some hate speech/spam before it's visible
  via the API; commenters can delete their own comments; creators/
  moderators can delete comments on their own videos. A creator going
  through a downfall has an obvious incentive to clean up the most
  hostile comments on their own channel over time. This means backfill
  ingestion of a known past event — which is what the entire calibration
  test set (§8) relies on — is measuring a survivor-biased, smoothed-over
  version of what actually happened; the true historical peak was likely
  higher than what change-point detection will find years later.
  Recurring/real-time monitoring mode is less affected by this, since it
  captures comments closer to when they're posted. This isn't fixable —
  it's an inherent property of retroactive data collection on a
  moderated, editable platform — but it should be treated as expected
  signal attenuation on calibration results, not a sign the detector is
  underperforming.

# 8. Calibration Test Set

Picked before running the pipeline, based on outside knowledge of what
actually happened — not picked afterward to match whatever the pipeline
outputs (see downfall ADR-007's consequence on this). Ingestion for these
six is bounded to a window around each known event date, not full-channel
backfill (see §7's scale limitation).

- **James Charles** — multiple controversies, one creator (2019, 2021, 2024)
- **PewDiePie** — known downfall (2017), subscriber/view metrics
  unaffected — the case for why comment-based signals beat subscriber-based ones
- **Trisha Paytas** — controversial-by-design, no single clean cancellation
- **Ryan Higa** — vanilla, expected near-zero directed hate (needs a
  dedicated check before fully trusting this categorization)
- **Stephanie Soo** — single-event downfall (2019 Nikocado Avocado dispute,
  second video shifted backlash onto her) and apparent recovery —
  mechanism of recovery (specific reconciling event vs. attention fading)
  intentionally left for the pipeline to discover, not assumed
- **Logan Paul** — single-event downfall (Jan 2018 Aokigahara video),
  well-documented recovery mechanism (a specific suicide-prevention video
  + donation, not just faded attention) — the strongest test case for
  ADR-004's reason-inference method specifically. Note: involves an
  actual death, a different order of severity than the other cases —
  handle with corresponding care in any write-up or visualization.

Two categories from the original design (a clean "known downfall, never
recovered" case) are not yet filled — worth adding before treating the
calibration set as complete.

# 9. Build Order

1. Wire up Perspective API toxicity scoring in the Silver layer
2. Confirm emotion scoring runs on real comment data
3. Design and implement bounded-window Bronze ingestion for the
   calibration set (§8); full-channel backfill mode separately for real
   future use on smaller creators (see §7's scale limitation)
4. Build Gold-layer rolling averages + multi-change-point detection
   (directed-hate signal specifically, per ADR-006/007)
5. Build spillover detection (old-video comments post-trigger-date)
6. Build term-frequency reason inference (ADR-004)
7. Resolve the "love" signal definition and subscriber-data decision
8. Build the two-layer visualization
9. Run the full pipeline against the calibration set and validate against
   known outcomes
10. Extend to recurring/daily ingestion for future-decline monitoring on
    an unknown creator

# 10. Tech Stack

| **Layer** | **Tool** |
| --- | --- |
| Ingestion | YouTube Data API |
| Orchestration | Airflow (Docker Compose) — backfill + recurring DAGs |
| Processing | PySpark |
| Emotion | `j-hartmann/emotion-english-distilroberta-base` |
| Toxicity | Perspective API |
| Change-point detection | TBD (e.g. `ruptures` or rolling-window threshold) |
| Storage / Warehouse | BigQuery (free tier) |
| Transformation | dbt — window functions for rolling averages, change-point flags |