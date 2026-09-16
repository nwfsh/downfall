adr — target/stance detection dropped, project scope changed

status: accepted

context
-------
project needed to classify youtube comments by who they were directed at
(e.g. james charles vs. tati) and whether the comment supported or
criticized that target. this was meant to separate controversy-specific
reaction from general sentiment.

testing done
------------
built a hand-labeled ground truth set of 27 comments from the james
charles/tati controversy (comment, target entity, stance).

tested 4 methods against it:

1. bart zero-shot, entity-only labels (james charles/tati/jeffree/none)
   — ~41% accuracy

2. bart zero-shot, combined stance labels (supports x / criticizes x)
   — ~26% accuracy

3. llm-generated label categories (gemini) fed into bart zero-shot
   — ~41% accuracy, but with polarity-inverted errors (labeled
   "criticizes" on comments that were clearly supportive)

4. bart two-pass — detect entity first, then classify stance toward it
   — ~11% accuracy, worst of all methods

also tested plain sentiment analysis (cardiffnlp/twitter-roberta) alone
as a baseline — insufficient on its own since sentiment doesn't capture
who a comment is about.

failure pattern
----------------
all 4 methods failed on the same kind of comment: sarcasm, mimicry,
pronoun-only reference, indirect judgment. example: "yes sis defend
your mom" reads as mocking on the surface but is actually approving
imitation — supportive, not critical. small/local nlu models
consistently couldn't resolve this kind of tone-through-context, no
matter how the labels were restructured.

considered but not pursued: llm-based classification (rather than
llm-generated labels feeding a smaller model). likely more accurate,
but per-comment llm calls at the volume this project needs weren't
cost-viable.

decision
--------
dropped target/stance detection from the project entirely. no further
label engineering on bart, since the problem was model capability, not
label design.

final thoughts / new scope
---------------------------
moving to a new repo. new angle: report hate rates directed toward the
creator vs. toward other people involved (e.g. james charles filtering
hate aimed at himself but not comments attacking tati, including her
age), broken down by category (race/gender/age, possibly political
topics).

explicitly scoped as reporting stats/rates only — not asserting intent
or mechanism. the data can show a rate difference; it can't show
whether that difference is a deliberate moderation choice, an
algorithm effect, or just audience composition. project name and
framing chosen to reflect this (leaning descriptive, e.g.
"hate-distribution", over anything implying a causal claim like
"selective-filter").

this new direction doesn't require target/stance resolution, so it
avoids the exact failure mode above. carries over bronze ingestion,
airflow orchestration, and existing sentiment/emotion scoring from the
old repo. toxicity/perspective api (identity_attack) integration is
the next real build item, more central now than before.