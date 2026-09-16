import sys
import pandas as pd
import tweetnlp

CSV_FILE = sys.argv[1] if len(sys.argv) > 1 else "blindspot_test_examples.csv"

model = tweetnlp.Classifier("cardiffnlp/twitter-roberta-base-hate-multiclass-latest")

df = pd.read_csv(CSV_FILE, engine="python")
df.columns = [c.strip() for c in df.columns]
comment_col = "comment" if "comment" in df.columns else df.columns[0]
comments = df[comment_col].fillna("").tolist()

print(f"Classifying {len(comments)} comments...")
results = model.predict(comments, return_probability=True)
print("Sample result:", results[0])

THRESHOLD = 0.05
HATE_CATEGORIES = {"sexism", "racism", "disability", "sexual_orientation", "religion", "other"}

def apply_threshold(result):
    probs = result["probability"]
    best_hate_cat = max(HATE_CATEGORIES, key=lambda c: probs.get(c, 0))
    if probs.get(best_hate_cat, 0) >= THRESHOLD:
        return best_hate_cat
    return "not_hate"

df["hate_label"] = [apply_threshold(r) for r in results]

out_file = CSV_FILE.replace(".csv", "_results.csv")
df.to_csv(out_file, index=False)
print(f"Saved to {out_file}")
print(df[[comment_col, "hate_label"]].to_string())
