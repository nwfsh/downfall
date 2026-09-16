# ADR: blindspot MVP scoping — LLM usage, model testing strategy, and category narrowing

## Status
Accepted

## Context

### LLM usage
Original project scope specified Perspective API / Detoxify only, with no LLM required for the hate/identity-attack classification pipeline. Revisited given real credit/token limits, and given the pivot toward category-level classification with an overt/covert/benevolent taxonomy, which surfaces edge cases (subtle stereotyping, ambiguous category boundaries) that a fixed rules-based or single-model approach can't always resolve on its own.

### Model testing strategy
Considered building a custom fine-tuned RoBERTa classifier for category + mode (hostile/covert/benevolent/control/critique) discrimination detection from the outset. This carried real over-scoping risk: the prior pivot (stance/target detection) was attempted and dropped after four different methods failed, largely from tackling a harder problem than the classification task needed. To avoid repeating that failure mode, evaluated whether existing off-the-shelf classifiers could do the job first, before committing to a fine-tune.

Two architecture questions came up during this evaluation:

1. **Staged (detect-then-classify) vs. single-pass classification.** Tested binary and severity-gated models (`cardiffnlp/twitter-roberta-base-hate-latest`, `Hate-speech-CNERG/bert-base-uncased-hatexplain`) as a potential first-stage filter ahead of a category classifier. Found that these gating models filtered out benevolent content before it could ever reach a categorization stage — a binary hate/not-hate gate scored a clear benevolent-sexism statement at 0.996 "not hate," meaning a staged pipeline would structurally guarantee the exact content this project cares about never gets classified at all.

2. **GUS-Net (token-level span classifier for generalizations/unfairness/stereotypes) as a complementary tool.** Confirmed GUS-Net performs no hate or category classification — it flags biased spans within a sentence but doesn't identify which discrimination category or whether something is "hate" at all. Using it would mean stacking a second model and a second training/eval pipeline on top of a category classifier, for a problem that later testing showed was more likely a training-data coverage gap than something span-level detection would fix.

### Category narrowing
Tested `cardiffnlp/twitter-roberta-base-hate-multiclass-latest` (7-class: sexism/racism/disability/sexual_orientation/religion/other/not_hate) — the best performer from the above evaluation — against an 85-statement hand-labeled test set (35 tagged examples across 6 categories x 5 modes, 50 control/neutral statements):

- Control accuracy: ~98% (42/43), near-zero false positives on neutral and identity-mentioning-but-neutral text
- Hostile accuracy: 40% (4/10)
- Benevolent accuracy: 33% (2/6)
- Covert accuracy: 33% (2/6)
- **Disability: 0/5**, including a miss on the most severe statement in the test set (eugenics-adjacent content)
- Mental health: 1 test case, misclassified into an unrelated category (religion)
- Sexism: strongest category — caught most hostile and 2/3 benevolent examples
- Race: caught overt hostile cleanly, missed covert and benevolent
- One false positive: an egalitarian control statement ("Women are as capable as men") flagged as sexism

Chaining multiple general-purpose models (binary detector + multiclass classifier + span detector) did not converge on a working solution for the full category set — added pipeline complexity without resolving the underlying gap in disability and mental-health coverage.

## Decision

1. **LLM usage**: allowed in the pipeline, but reserved for minimal, targeted calls — edge-case adjudication and generating/validating hand-written taxonomy examples — not bulk scoring across the dataset. Perspective/Detoxify (or an eventual fine-tuned classifier) remains the primary mechanism for scoring comments at volume.
2. **Testing strategy**: validate off-the-shelf classifiers against a hand-built, labeled test set before deciding whether a fine-tune is justified, rather than building custom from the outset.
3. **Architecture**: reject staged detect-then-classify in favor of a single-pass multiclass model that outputs category labels (including a "not hate" option) in one call. Defer GUS-Net integration — documented as a viable future enhancement, not adopted now.
4. **Scope**: narrow the MVP to **racism and sexism only**. Source a dedicated, specialized model per category rather than relying on one general-purpose multiclass model or a multi-model chained pipeline. These are the most extensively researched categories in existing hate speech literature, and were the categories where the tested general-purpose classifier actually performed adequately.

## Consequences

**Gained:**
- Avoided repeating the stance-detection over-engineering failure
- Predictable, low LLM cost, with LLM use unlocked for the one place it's actually useful right now (taxonomy example generation/validation)
- A finishable MVP path — classify → store → dashboard — on categories where underlying model performance is usable
- Evidence-based rather than assumption-based decision about what to fine-tune, if anything

**Deferred, not abandoned:**
- GUS-Net span-level detection remains unintegrated; revisit if/when a benevolent/covert detection gap is confirmed to be an architecture problem rather than a data-coverage one
- Disability, mental health, religion, sexual orientation, criminal status, nationality — moved to backlog, logged with the specific evidence for why each was cut
- The disability finding (0/5, including the eugenics-severity miss) is itself a notable result worth keeping for later writeup, independent of whether it gets fixed

**Requires:**
- Manual review of any LLM-generated content (example sentences, edge-case labels) rather than trusting it directly

**Open question carried forward:**
- Whether the gold-layer schema should be designed to accommodate re-adding categories later without a redesign, or whether that's deferred until a category is actually re-added