"""
Given a creator name, asks Gemini to research their controversies and
output structured entities + stance labels — for use as the label set
in your BART zero-shot script (not for classification itself).

"""

import sys
import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

CREATOR = sys.argv[1] if len(sys.argv) > 1 else "James Charles"

client = genai.Client(api_key=os.environ["API_KEY"])
MODEL = "gemini-3.6-flash"

PROMPT = """
Research the main controversies involving the YouTube creator "{creator}".

For each controversy, identify:
- The creator's name and common aliases used in comments (nicknames, pronouns, age references)
- The other party/parties involved, and their aliases
- A stance label set usable for classifying comments as supporting/criticizing each party

Respond ONLY with valid JSON in this exact structure, no other text:
{{
  "controversies": [
    {{
      "name": "short name of the controversy",
      "description": "one sentence",
      "entities": [
        {{"name": "...", "role": "creator or other_party", "aliases": ["...", "..."]}}
      ],
      "stance_labels": ["supports X", "criticizes X", "supports Y", "criticizes Y", "unrelated"]
    }}
  ]
}}
"""

response = client.models.generate_content(
    model=MODEL,
    contents=PROMPT.format(creator=CREATOR),
    config={"temperature": 0},
)

raw = response.text.strip()
raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

try:
    data = json.loads(raw)
except json.JSONDecodeError:
    print("Could not parse JSON. Raw output:")
    print(raw)
    sys.exit(1)

out_file = f"{CREATOR.replace(' ', '_').lower()}_labels.json"
with open(out_file, "w") as f:
    json.dump(data, f, indent=2)

print(f"Saved to {out_file}")
for c in data["controversies"]:
    print(f"\n{c['name']}: {c['description']}")
    print(f"  Stance labels: {c['stance_labels']}")

# --- Step 2: use those labels to classify comments with BART zero-shot ---
import pandas as pd
from transformers import pipeline

CSV_FILE = sys.argv[2] if len(sys.argv) > 2 else "src/ground_truth.csv"

# flatten all stance labels across all controversies, deduplicated
all_labels = list(dict.fromkeys(
    label
    for controversy in data["controversies"]
    for label in controversy["stance_labels"]
))
print(f"\nUsing {len(all_labels)} stance labels: {all_labels}")

df = pd.read_csv(CSV_FILE)
df.columns = [c.strip() for c in df.columns]
comment_col = "comment" if "comment" in df.columns else "Comments"
comments = df[comment_col].fillna("").tolist()

print("Loading BART zero-shot classifier...")
zsc = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

print(f"Classifying {len(comments)} comments...")
df["bart_stance"] = [
    zsc(c, all_labels, multi_label=False)["labels"][0] for c in comments
]

out_csv = "eval_results_bart.csv"
df.to_csv(out_csv, index=False)
print(f"\nSaved classified results to {out_csv}")