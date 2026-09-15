"""
Two-pass zero-shot classification:
  Pass 1: which entity is this comment about? (James Charles / Tati / Jeffree / none)
  Pass 2: for each entity found, is the comment supportive or critical of them?

Run on your own machine (needs huggingface.co access).
"""

import sys
import pandas as pd
from transformers import pipeline

INPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else "ground_truth.csv"
ENTITY_THRESHOLD = 0.1  # only count an entity as "detected" above this score

ENTITIES = ["James Charles", "Tati", "Jeffree"]

df = pd.read_csv(INPUT_FILE)
df.columns = [c.strip() for c in df.columns]
df = df.rename(columns={
    "Comments": "comment",
    "Target_Entity": "target_entity",
    "target stance": "stance",
})

zsc = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

def detect_entities(comment):
    result = zsc(comment, ENTITIES + ["none"], multi_label=True)
    detected = [
        label for label, score in zip(result["labels"], result["scores"])
        if label != "none" and score >= ENTITY_THRESHOLD
    ]
    return detected if detected else ["none"]

def detect_stance(comment, entity):
    labels = [f"supports {entity}", f"criticizes {entity}", "neutral"]
    result = zsc(comment, labels, multi_label=False)
    return result["labels"][0]

targets = []
stances = []

for comment in df["comment"]:
    entities = detect_entities(comment)
    if entities == ["none"]:
        targets.append("none")
        stances.append("neutral")
        continue

    per_entity_stances = []
    for entity in entities:
        stance = detect_stance(comment, entity)
        per_entity_stances.append(stance)

    targets.append(", ".join(entities))
    stances.append(" | ".join(per_entity_stances))

df["bart_twopass_target"] = targets
df["bart_twopass_stance"] = stances

out_file = "eval_results_twopass.csv"
df.to_csv(out_file, index=False)
print(f"Saved to {out_file}")