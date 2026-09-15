"""
Runs your ground_truth.csv through 3 methods and saves results for comparison.
Run this on your OWN machine (needs internet access to huggingface.co).

Setup:
    pip install transformers torch pandas

Usage:
    python run_eval.py ground_truth.csv
"""

import sys
import pandas as pd
from transformers import pipeline

INPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else "ground_truth.csv"

# --- Load and clean columns (matches your export's messy headers) ---
df = pd.read_csv(INPUT_FILE)
df.columns = [c.strip() for c in df.columns]
df = df.rename(columns={
    "Comments": "comment",
    "Target_Entity": "target_entity",
    "target stance": "stance",
})

comments = df["comment"].tolist()

# --- Method 1: plain sentiment (baseline) ---
print("Running sentiment-only baseline...")
sentiment = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment-latest"
)
df["sentiment_only"] = [sentiment(c)[0]["label"] for c in comments]

# --- Method 2: BART zero-shot, entity-only labels ---
print("Running BART zero-shot (entity-only)...")
zsc = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
entity_labels = ["James Charles", "Tati", "Jeffree", "unrelated"]

df["bart_entity_only"] = [
    zsc(c, entity_labels, multi_label=True)["labels"][0] for c in comments
]

# --- Method 3: BART zero-shot, stance labels ---
print("Running BART zero-shot (stance labels)...")
stance_labels = [
    "supports James Charles", "criticizes James Charles",
    "supports Tati", "criticizes Tati",
    "supports Jeffree", "criticizes Jeffree",
    "unrelated",
]

df["bart_stance"] = [
    zsc(c, stance_labels, multi_label=True)["labels"][0] for c in comments
]

# --- Save ---
out_file = "eval_results.csv"
df.to_csv(out_file, index=False)
print(f"\nSaved to {out_file}")
print("\nNow add a 'correct' column (Y/N) for each method by comparing to your original stance column.")