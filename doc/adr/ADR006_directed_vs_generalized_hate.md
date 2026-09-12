## ADR-006: Run change-point detection on directed hate specifically, not raw toxicity volume

**Context**

A creator whose content is *about* enraging subject matter (news
commentary, reaction content, covering real injustice) can show the same
aggregate toxicity/anger signature as a creator who has personally become
the target of backlash — high toxicity, anger-dominant emotion — even
though the first case involves no downfall at all. Raw toxicity/emotion
volume, as used in ADR-003, cannot distinguish these: it measures how
angry a comment section is, not *at whom*.

This is a recognized distinction in hate-speech research: **directed**
hate speech (aimed at a specific individual) vs. **generalized** hate
speech (aimed at a topic, group, or third party). A commonly used, low-
cost method for isolating directed hate speech (per "Hate Lingo," a
target-based linguistic analysis of hate speech) filters for comments
that combine an explicit mention of the specific target with second-
person pronouns ("you," "your," "u," "ur") — as opposed to third-person
references, which more often indicate the comment is about someone or
something discussed in the video rather than the creator themself.

**Decision**

Before running change-point detection (ADR-003), filter comments to a
"directed" subset: comments containing second-person address markers
("you," "your," etc.) in a hostile/toxic context, optionally combined with
an explicit creator name/handle mention where available. Run change-point
detection on this directed-toxicity volume, not on raw whole-comment-
section toxicity. Generalized hostility about a video's subject matter is
excluded from the spike-detection signal, though it may still be worth
tracking separately as a distinct metric (how angry is the audience about
the topic vs. about the creator).

**Consequences**

- This is a lightweight heuristic (pronoun + mention pattern matching),
  not a trained classifier — consistent with this project's existing
  preference for explainable, lower-effort methods (see ADR-004's choice
  of term-frequency over topic modeling).
- The heuristic is imperfect: second-person address doesn't always mean
  the creator is the target (e.g. a reply addressing another commenter,
  not the creator), and some directed hostility may not use second-person
  pronouns at all (e.g. repeated use of the creator's name in third
  person: "she's disgusting" said about the creator, not a video subject).
  This should be validated against a small labeled sample before being
  trusted, same calibration discipline as ADR-003.
- ADR-003 and ADR-004 both need to be read as operating on this directed
  subset, not raw comment volume — this ADR effectively amends the input
  to both, not just adds a new step.