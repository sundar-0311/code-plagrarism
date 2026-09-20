"""
composite.py

Combines the four similarity signals into ONE weighted score, tunes the
weights and the decision threshold on the labelled pairs, and reports
honest metrics.

Signals (one CSV each, all keyed by problem + file names):
    jaccard, winnow   <- results/similarity_results.csv   (your Day 1)
    structural        <- pairs_scored.csv                 (Person A, Day 2)
    embedding         <- results/embedding_<backend>.csv  (your Day 2)

Run from the repo root:
    python similarity_engine/composite.py --embedding-csv results/embedding_codebert.csv

What it does, in order:
  1. Merge the four signals into one table (one row per pair).
  2. Build "family" labels from variant_of.csv (see note below).
  3. Print how good each signal is on its own (ROC-AUC).
  4. Tune weights + threshold with leave-one-problem-out cross-validation,
     so every score reported comes from a problem the tuner never saw.
  5. Fit the final model on all pairs, save it to results/composite_model.json,
     and write per-pair scores to results/composite_results.csv.

NOTE ON LABELS. pairs.csv marks a pair "plagiarized" when EITHER file is
numbered 4-6. But files 4-6 are copies of one specific original (usually
file 1), so e.g. file 2 vs file 4 is two genuinely different solutions
that the original rule still labels as plagiarized. "family" labels fix
that: a pair is plagiarized only if both files descend from the same
original (variant_of.csv). Use --labels original to see the old behaviour.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score

ALL_SIGNALS = ["jaccard", "winnow", "structural", "embedding"]


# ---------------------------------------------------------------------
# 1. Loading and merging
# ---------------------------------------------------------------------
def _basename(path_series: pd.Series) -> pd.Series:
    return path_series.str.replace("\\", "/", regex=False).str.split("/").str[-1]


def _key(df: pd.DataFrame) -> pd.Series:
    """problem|a_file|b_file -- identical no matter which folder the CSV
    pointed at (dataset/, dataset_preprocessed/, backslashes or slashes)."""
    return df["problem_id"].astype(str) + "|" + _basename(df["file_a"]) + "|" + _basename(df["file_b"])


def load_signals(similarity_csv, structural_csv, embedding_csv) -> pd.DataFrame:
    base = pd.read_csv(similarity_csv)
    base["key"] = _key(base)

    structural = pd.read_csv(structural_csv)
    structural["key"] = _key(structural)
    structural = structural[["key", "structural"]]  # ignore Person A's own jaccard/combined

    embedding = pd.read_csv(embedding_csv)
    embedding["key"] = _key(embedding)
    embedding = embedding[["key", "embedding"]]

    df = base.merge(structural, on="key", how="inner").merge(embedding, on="key", how="inner")
    if len(df) != len(base):
        raise SystemExit(f"Merge lost rows: {len(base)} pairs in similarity CSV, {len(df)} after merge. "
                         "Check that all three CSVs cover the same pairs.")
    return df


def family_labels(df: pd.DataFrame, variants_csv) -> np.ndarray:
    v = pd.read_csv(variants_csv)
    family = {(r.problem_id, int(r.file_num)): int(r.family) for r in v.itertuples()}

    def number(name: str) -> int:
        return int(re.match(r"(\d+)", name).group(1))

    a = _basename(df["file_a"]).map(number)
    b = _basename(df["file_b"]).map(number)
    return np.array([
        int(family[(p, na)] == family[(p, nb)])
        for p, na, nb in zip(df["problem_id"], a, b)
    ])


# ---------------------------------------------------------------------
# 2. The model: normalise -> weighted sum -> threshold
# ---------------------------------------------------------------------
def fit_minmax(X):
    return X.min(axis=0), X.max(axis=0)


def apply_minmax(X, lo, hi):
    span = np.where(hi - lo == 0, 1.0, hi - lo)
    return np.clip((X - lo) / span, 0.0, 1.0)


def simplex_grid(n: int, step: float):
    """All weight vectors of length n, multiples of `step`, summing to 1."""
    k = round(1 / step)

    def rec(n_left, total):
        if n_left == 1:
            yield (total,)
            return
        for i in range(total + 1):
            for rest in rec(n_left - 1, total - i):
                yield (i,) + rest

    for combo in rec(n, k):
        yield np.array(combo) / k


def search_weights(Xn, y, step):
    """Pick the weights whose composite ranks plagiarized pairs above the
    rest best (ROC-AUC). The tiny sum-of-squares penalty only breaks ties,
    preferring balanced weights over 'all weight on one signal'."""
    best_obj, best_w = -np.inf, None
    for w in simplex_grid(Xn.shape[1], step):
        obj = roc_auc_score(y, Xn @ w) - 1e-3 * float((w ** 2).sum())
        if obj > best_obj:
            best_obj, best_w = obj, w
    return best_w


def best_threshold(scores, y):
    """Threshold with the highest F1, placed in the gap just below the
    lowest score it flags (more robust than sitting exactly on a point)."""
    candidates = np.unique(scores)
    best_f1, best_i = -1.0, 0
    for i, t in enumerate(candidates):
        pred = scores >= t
        tp = int((pred & (y == 1)).sum())
        fp = int((pred & (y == 0)).sum())
        fn = int((~pred & (y == 1)).sum())
        f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
        if f1 > best_f1 + 1e-12:
            best_f1, best_i = f1, i
    lower = candidates[best_i - 1] if best_i > 0 else candidates[best_i]
    return float((candidates[best_i] + lower) / 2)


def fit(X, y, step):
    lo, hi = fit_minmax(X)
    Xn = apply_minmax(X, lo, hi)
    w = search_weights(Xn, y, step)
    t = best_threshold(Xn @ w, y)
    return {"lo": lo, "hi": hi, "w": w, "t": t}


def score(model, X):
    return apply_minmax(X, model["lo"], model["hi"]) @ model["w"]


# ---------------------------------------------------------------------
# 3. Leave-one-problem-out cross-validation
# ---------------------------------------------------------------------
def lopo(df, signals, y, step):
    """For each problem: tune on the other 7, score this one. Returns the
    held-out composite scores and predictions for every pair."""
    X = df[signals].to_numpy(dtype=float)
    scores = np.zeros(len(df))
    preds = np.zeros(len(df), dtype=bool)
    for problem in df["problem_id"].unique():
        test = (df["problem_id"] == problem).to_numpy()
        model = fit(X[~test], y[~test], step)
        s = score(model, X[test])
        scores[test] = s
        preds[test] = s >= model["t"]
    return scores, preds


def metrics(y, preds, scores):
    p, r, f1, _ = precision_recall_fscore_support(y, preds, average="binary", zero_division=0)
    return {"precision": p, "recall": r, "f1": f1,
            "accuracy": accuracy_score(y, preds), "auc": roc_auc_score(y, scores)}


def print_table(title, rows):
    print(f"\n{title}")
    print(f"  {'configuration':<28}{'precision':>10}{'recall':>9}{'F1':>8}{'accuracy':>10}{'AUC':>8}")
    for name, m in rows:
        print(f"  {name:<28}{m['precision']:>10.3f}{m['recall']:>9.3f}{m['f1']:>8.3f}"
              f"{m['accuracy']:>10.3f}{m['auc']:>8.3f}")


# ---------------------------------------------------------------------
# 4. Reusable scoring for the dashboard (Day 3)
# ---------------------------------------------------------------------
def load_model(path="results/composite_model.json"):
    m = json.loads(Path(path).read_text())
    return {"signals": m["signals"], "lo": np.array(m["lo"]), "hi": np.array(m["hi"]),
            "w": np.array(m["weights"]), "t": m["threshold"]}


def composite_score(model, signal_values: dict) -> tuple[float, bool]:
    """signal_values = {'jaccard': .., 'winnow': .., 'structural': .., 'embedding': ..}
    Returns (composite score in [0,1], flagged?)."""
    x = np.array([[signal_values[s] for s in model["signals"]]], dtype=float)
    s = float(score(model, x)[0])
    return s, s >= model["t"]


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--similarity-csv", default="results/similarity_results.csv")
    ap.add_argument("--structural-csv", default="pairs_scored.csv")
    ap.add_argument("--embedding-csv", default="results/embedding_codebert.csv")
    ap.add_argument("--variants", default="variant_of.csv")
    ap.add_argument("--labels", choices=["family", "original"], default="family")
    ap.add_argument("--step", type=float, default=0.1, help="weight grid step (default 0.1)")
    ap.add_argument("--out-dir", default="results")
    args = ap.parse_args()

    df = load_signals(args.similarity_csv, args.structural_csv, args.embedding_csv)
    y_original = df["is_plagiarized"].to_numpy().astype(int)
    y_family = family_labels(df, args.variants)
    y = y_family if args.labels == "family" else y_original

    print(f"{len(df)} pairs merged. Labels used for tuning: '{args.labels}'")
    print(f"  original labels : {y_original.sum()} plagiarized / {(y_original == 0).sum()} not")
    print(f"  family labels   : {y_family.sum()} plagiarized / {(y_family == 0).sum()} not "
          f"({int((y_original != y_family).sum())} pairs change label)")

    # --- how good is each signal alone? (threshold-free ranking quality)
    print("\nSingle-signal ROC-AUC  (0.5 = coin flip, 1.0 = perfect ranking)")
    print(f"  {'signal':<12}{'original labels':>17}{'family labels':>16}")
    for s in ALL_SIGNALS:
        print(f"  {s:<12}{roc_auc_score(y_original, df[s]):>17.3f}{roc_auc_score(y_family, df[s]):>16.3f}")

    # --- cross-validated comparison
    rows = []
    for s in ALL_SIGNALS:
        sc, pr = lopo(df, [s], y, args.step)
        rows.append((f"{s} alone", metrics(y, pr, sc)))
    no_emb = [s for s in ALL_SIGNALS if s != "embedding"]
    sc, pr = lopo(df, no_emb, y, args.step)
    rows.append(("composite WITHOUT embedding", metrics(y, pr, sc)))
    scores_all, preds_all = lopo(df, ALL_SIGNALS, y, args.step)
    rows.append(("composite (all 4 signals)", metrics(y, preds_all, scores_all)))
    print_table("Leave-one-problem-out results (each problem scored by a model that never saw it)", rows)

    # --- final model on all data
    model = fit(df[ALL_SIGNALS].to_numpy(dtype=float), y, args.step)
    print("\nFinal model (fit on all pairs)")
    for s, w, lo, hi in zip(ALL_SIGNALS, model["w"], model["lo"], model["hi"]):
        print(f"  {s:<12} weight={w:.2f}   (raw range used for scaling: {lo:.3f} .. {hi:.3f})")
    print(f"  threshold = {model['t']:.3f}  (composite >= threshold -> flagged)")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "composite_model.json").write_text(json.dumps({
        "signals": ALL_SIGNALS,
        "lo": model["lo"].tolist(), "hi": model["hi"].tolist(),
        "weights": model["w"].tolist(), "threshold": model["t"],
        "labels": args.labels,
        "lopo_composite": metrics(y, preds_all, scores_all),
    }, indent=2))

    final_scores = score(model, df[ALL_SIGNALS].to_numpy(dtype=float))
    out = df.drop(columns=["key"]).copy()
    out["label_used"] = y
    out["composite"] = np.round(final_scores, 4)
    out["flagged"] = (final_scores >= model["t"]).astype(int)
    out.to_csv(out_dir / "composite_results.csv", index=False)
    print(f"\nWrote {out_dir / 'composite_model.json'} and {out_dir / 'composite_results.csv'}")

    # --- error analysis (final model, so this is training-set behaviour)
    wrong = out[out["flagged"] != out["label_used"]].copy()
    wrong["file_a"] = _basename(wrong["file_a"])
    wrong["file_b"] = _basename(wrong["file_b"])
    wrong = wrong.assign(gap=(wrong["composite"] - model["t"]).abs()).sort_values("gap", ascending=False)
    print(f"\n{len(wrong)} misclassified pairs (largest miss first, max 10 shown):")
    print(wrong[["problem_id", "file_a", "file_b", "label_used", "composite"] + ALL_SIGNALS]
          .head(10).to_string(index=False))


if __name__ == "__main__":
    main()