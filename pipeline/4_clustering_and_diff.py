"""
4_clustering_and_diff.py

Day 3 (Person A): turns the pairwise composite scores from Day 2 into
group-level results and human-readable evidence.

Two things happen here, both driven by results/composite_results.csv:

1. CLUSTERING
   Build one similarity graph per problem (files = nodes, edges = pairs
   flagged by the composite model). Connected components of that graph
   are "suspicion groups" -- e.g. if A~B and B~C are both flagged, A/B/C
   get reported as one group of three, not two separate pairs, even if
   A~C alone wouldn't have crossed the threshold. Writes results/groups.csv.

2. DIFF VIEWER
   For every flagged pair, render a side-by-side HTML diff
   (difflib.HtmlDiff) with matching lines highlighted, plus the four
   signal scores as context. Writes one HTML file per problem to
   results/diffs/, and an index page linking all of them, sorted by
   composite score (most suspicious first).

Usage:
    python 4_clustering_and_diff.py
    python 4_clustering_and_diff.py --results results/composite_results.csv
"""

from __future__ import annotations

import argparse
import csv
import html
from difflib import HtmlDiff
from pathlib import Path

import networkx as nx
import pandas as pd

SIGNALS = ["jaccard", "winnow", "structural", "embedding"]


def _basename(path: str) -> str:
    return path.replace("\\", "/").split("/")[-1]


# ---------------------------------------------------------------------
# 1. Clustering
# ---------------------------------------------------------------------
def build_groups(df: pd.DataFrame) -> pd.DataFrame:
    """One graph per problem; nodes = files that appear in any pair for
    that problem; edges = pairs the composite model flagged. Connected
    components of that graph are the suspicion groups."""
    rows = []
    for problem, sub in df.groupby("problem_id"):
        g = nx.Graph()
        all_files = set(_basename(f) for f in sub["file_a"]) | set(_basename(f) for f in sub["file_b"])
        g.add_nodes_from(all_files)
        for _, r in sub[sub["flagged"] == 1].iterrows():
            g.add_edge(_basename(r["file_a"]), _basename(r["file_b"]), weight=r["composite"])

        group_id = 0
        for component in nx.connected_components(g):
            if len(component) < 2:
                continue  # singleton, no flagged edges -- not a suspicion group
            group_id += 1
            edges = g.subgraph(component).edges(data=True)
            avg_score = sum(d["weight"] for _, _, d in edges) / max(len(edges), 1)
            rows.append({
                "problem_id": problem,
                "group_id": f"{problem}_{group_id}",
                "size": len(component),
                "files": ";".join(sorted(component)),
                "num_flagged_edges": len(edges),
                "avg_composite": round(avg_score, 4),
            })
    return pd.DataFrame(rows).sort_values(["problem_id", "group_id"]) if rows else pd.DataFrame(
        columns=["problem_id", "group_id", "size", "files", "num_flagged_edges", "avg_composite"]
    )


# ---------------------------------------------------------------------
# 2. Diff viewer
# ---------------------------------------------------------------------
def find_source(problem_id: str, filename: str, dataset_dir: Path) -> Path | None:
    candidate = dataset_dir / problem_id / filename
    return candidate if candidate.exists() else None


def render_pair_diff(row: pd.Series, dataset_dir: Path) -> str | None:
    file_a_name = _basename(row["file_a"])
    file_b_name = _basename(row["file_b"])
    path_a = find_source(row["problem_id"], file_a_name, dataset_dir)
    path_b = find_source(row["problem_id"], file_b_name, dataset_dir)
    if path_a is None or path_b is None:
        return None

    lines_a = path_a.read_text(encoding="utf-8", errors="ignore").splitlines()
    lines_b = path_b.read_text(encoding="utf-8", errors="ignore").splitlines()

    differ = HtmlDiff(wrapcolumn=60)
    diff_table = differ.make_table(
        lines_a, lines_b, fromdesc=file_a_name, todesc=file_b_name, context=False
    )

    signal_row = " ".join(f"<span class='sig'>{s}: {row[s]:.3f}</span>" for s in SIGNALS)
    label = "PLAGIARIZED" if row["label_used"] == 1 else "not plagiarized"
    verdict = "FLAGGED" if row["flagged"] == 1 else "not flagged"

    return f"""
    <section class="pair">
      <h2>{html.escape(row['problem_id'])}: {html.escape(file_a_name)} vs {html.escape(file_b_name)}</h2>
      <p>composite = <b>{row['composite']:.3f}</b> &middot; {verdict} &middot; ground truth: {label}</p>
      <p class="signals">{signal_row}</p>
      {diff_table}
    </section>
    """


DIFF_CSS = """
<style>
  body { font-family: -apple-system, Arial, sans-serif; margin: 2rem; background: #fafafa; color: #222; }
  h1 { margin-bottom: 0.2rem; }
  .pair { background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 1rem 1.5rem; margin-bottom: 2rem; }
  .signals { font-size: 0.85rem; color: #555; }
  .sig { display: inline-block; margin-right: 1rem; background: #eef; padding: 2px 6px; border-radius: 4px; }
  table.diff { font-family: Consolas, monospace; font-size: 0.8rem; border-collapse: collapse; width: 100%; }
  table.diff td { padding: 1px 4px; }
  .diff_header { background: #f0f0f0; }
  td.diff_header { text-align: right; color: #888; }
  .diff_next { background: #f0f0f0; }
  .diff_add { background: #d4f7d4; }
  .diff_chg { background: #fff3b8; }
  .diff_sub { background: #fdd; }
  a { color: #06c; }
</style>
"""


def write_problem_diff_page(problem_id: str, sub: pd.DataFrame, dataset_dir: Path, out_dir: Path) -> Path | None:
    sub = sub.sort_values("composite", ascending=False)
    sections = []
    for _, row in sub.iterrows():
        rendered = render_pair_diff(row, dataset_dir)
        if rendered:
            sections.append(rendered)
    if not sections:
        return None

    page = f"<html><head><meta charset='utf-8'><title>{html.escape(problem_id)} diffs</title>{DIFF_CSS}</head>" \
           f"<body><h1>{html.escape(problem_id)}</h1><p><a href='index.html'>&larr; back to index</a></p>" \
           + "".join(sections) + "</body></html>"

    out_path = out_dir / f"{problem_id}.html"
    out_path.write_text(page, encoding="utf-8")
    return out_path


def write_index(flagged: pd.DataFrame, out_dir: Path) -> None:
    flagged = flagged.sort_values("composite", ascending=False)
    rows = "".join(
        f"<tr><td>{r['composite']:.3f}</td><td>{html.escape(r['problem_id'])}</td>"
        f"<td>{html.escape(_basename(r['file_a']))}</td><td>{html.escape(_basename(r['file_b']))}</td>"
        f"<td><a href='{html.escape(r['problem_id'])}.html'>view diff</a></td></tr>"
        for _, r in flagged.iterrows()
    )
    page = f"""<html><head><meta charset='utf-8'><title>Flagged pairs</title>{DIFF_CSS}
    <style>table {{ border-collapse: collapse; width: 100%; background: #fff; }}
    td, th {{ border: 1px solid #ddd; padding: 6px 10px; text-align: left; }}</style>
    </head><body>
    <h1>Flagged pairs ({len(flagged)})</h1>
    <table><tr><th>composite</th><th>problem</th><th>file A</th><th>file B</th><th></th></tr>
    {rows}</table></body></html>"""
    (out_dir / "index.html").write_text(page, encoding="utf-8")


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results/composite_results.csv")
    ap.add_argument("--dataset-dir", default="dataset")
    ap.add_argument("--out-dir", default="results")
    args = ap.parse_args()

    df = pd.read_csv(args.results)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- clustering ---
    groups = build_groups(df)
    groups.to_csv(out_dir / "groups.csv", index=False)
    print(f"{len(df)} pairs -> {int(df['flagged'].sum())} flagged edges -> {len(groups)} suspicion groups")
    if len(groups):
        print(groups.to_string(index=False))
    print(f"\nWrote {out_dir / 'groups.csv'}")

    # --- diff viewer ---
    diffs_dir = out_dir / "diffs"
    diffs_dir.mkdir(parents=True, exist_ok=True)
    flagged = df[df["flagged"] == 1].copy()
    dataset_dir = Path(args.dataset_dir)

    written = []
    for problem_id, sub in flagged.groupby("problem_id"):
        path = write_problem_diff_page(problem_id, sub, dataset_dir, diffs_dir)
        if path:
            written.append(problem_id)
    write_index(flagged, diffs_dir)
    print(f"Wrote diff pages for {len(written)} problems + index to {diffs_dir}/")


if __name__ == "__main__":
    main()
