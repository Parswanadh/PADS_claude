"""
Dialogue-act classifier: predicts shallow-serve vs. deep-reasoning-need from
a partial user utterance. Per the SKILL/PRD, this must be trained on existing
labeled corpora (Switchboard-DAMSL / MultiWOZ), never collected from scratch.

This script is fully runnable and hardware-agnostic (verified in sandbox on
synthetic placeholder data -- structurally identical to what a real
Switchboard-DAMSL-derived dataset would look like: short utterance -> binary
label). Swap `load_synthetic_data()` for a real corpus loader before trusting
any reported classifier accuracy.

Kept deliberately lightweight (TF-IDF + logistic regression) so it is CPU-cheap
enough to run alongside the turn-taking predictor and the LLM inference process
on the Latitude 5490 without contending for the same cores/RAM the reasoning
model needs -- this is a design constraint, not just a convenience choice.
"""
import argparse
import json

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib


SHALLOW = 0   # greeting / backchannel / simple factual -> stay at shallow exit
DEEP = 1      # analytical / coding / planning -> trigger deep reasoning


def load_synthetic_data():
    """
    Placeholder data with the SAME SHAPE as a real Switchboard-DAMSL-derived
    dataset would have: (partial_utterance_text, label). Replace with a real
    corpus loader -- see load_real_corpus() below for the expected interface.
    """
    examples = [
        ("hey how's it going", SHALLOW),
        ("thanks a lot", SHALLOW),
        ("okay sounds good", SHALLOW),
        ("uh-huh right", SHALLOW),
        ("what time is it", SHALLOW),
        ("good morning", SHALLOW),
        ("yeah I hear you", SHALLOW),
        ("that makes sense", SHALLOW),
        ("can you write a function that sorts a list", DEEP),
        ("explain why my code is throwing this error", DEEP),
        ("help me plan a three step project timeline", DEEP),
        ("what's the time complexity of this algorithm", DEEP),
        ("walk me through the proof of this theorem", DEEP),
        ("debug this recursive function for me", DEEP),
        ("compare these two architectural approaches", DEEP),
        ("design a database schema for this app", DEEP),
    ] * 8  # replicate for a slightly larger toy training set
    texts = [t for t, _ in examples]
    labels = [l for _, l in examples]
    return texts, labels


def load_real_corpus(path):
    """
    Expected interface for a real corpus loader: a JSONL file where each line
    is {"text": "<partial utterance>", "label": 0 or 1}, pre-mapped from
    Switchboard-DAMSL dialogue-act tags (e.g. greeting/backchannel/statement-
    non-opinion -> SHALLOW; action-directive/open-question requiring
    multi-step reasoning -> DEEP) or from MultiWOZ intent categories.
    REQUIRES the actual labeled corpus file -- not available in this sandbox.
    """
    texts, labels = [], []
    with open(path) as f:
        for line in f:
            row = json.loads(line)
            texts.append(row["text"])
            labels.append(row["label"])
    return texts, labels


def train_and_evaluate(texts, labels, out_path="dialogue_act_model.joblib"):
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.25, random_state=42, stratify=labels
    )

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    clf = LogisticRegression(max_iter=1000)
    clf.fit(X_train_vec, y_train)

    preds = clf.predict(X_test_vec)
    acc = accuracy_score(y_test, preds)
    report = classification_report(y_test, preds, target_names=["shallow", "deep"])

    print(f"Test accuracy: {acc:.3f}\n")
    print(report)

    joblib.dump({"vectorizer": vectorizer, "classifier": clf}, out_path)
    print(f"Saved model bundle to {out_path}")
    return acc


def predict_deep_need_prob(model_bundle, partial_utterance: str) -> float:
    """Returns P(deep reasoning needed) for one partial utterance -- this is
    the signal the TriggerPolicy (src/trigger_policy/policy.py) consumes."""
    vec = model_bundle["vectorizer"].transform([partial_utterance])
    return float(model_bundle["classifier"].predict_proba(vec)[0][DEEP])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", help="Path to a real JSONL corpus (Switchboard-DAMSL/MultiWOZ derived)")
    parser.add_argument("--out", default="dialogue_act_model.joblib")
    args = parser.parse_args()

    if args.corpus:
        texts, labels = load_real_corpus(args.corpus)
        print(f"Loaded {len(texts)} real labeled examples from {args.corpus}")
    else:
        print("[DEMO MODE] No --corpus given -- training on synthetic placeholder")
        print("data. Replace with a real Switchboard-DAMSL/MultiWOZ derived corpus")
        print("before this classifier's accuracy is reportable.\n")
        texts, labels = load_synthetic_data()

    train_and_evaluate(texts, labels, out_path=args.out)
