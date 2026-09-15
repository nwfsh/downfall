project halt :
classification of hate/sentiment directed towards a youtube creator, or towards stories or other subjects, was too difficult to identify due to sarcasm, jokes, 
and just too much context needed to tell who a comment is actually about

methods tried:
bart zero-shot, entity-only labels (james charles/tati/jeffree/none) — ~41% accuracy
bart zero-shot, combined stance labels (supports/criticizes x) — ~26%
llm-generated label categories fed into bart — ~41%, but flipped polarity on several (said "criticizes" when it was actually "supports")
bart two-pass (find entity first, then stance) — ~11%, worst one

tested against a hand-labeled 27-comment ground truth set from the james charles/tati drama

unfortunate to not be able to proceed with this project further 
