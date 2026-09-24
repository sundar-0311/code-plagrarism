"""
app.py

Day 3 (Partner): Streamlit dashboard for the plagiarism detector.

Two ways to use it (pick a mode in the sidebar):

  Live scan   Upload any set of .py files. The app preprocesses them,
              computes jaccard + winnowing + AST-structural similarity
              for every pair, and (optionally) CodeBERT embeddings
              (needs torch + transformers; downloads the model the
              first time -- CodeBERT, not GraphCodeBERT: it measurably
              outperforms GraphCodeBERT on this dataset, see
              similarity_engine/composite.py's docstring), then blends
              whichever signals were computed using the weights already
              tuned in results/composite_model.json (Day 2). If
              embeddings are switched off, it falls back to a plain
              average of the other three signals, using the threshold
              tuned specifically for that case -- see
              composite.composite_score(), which both code paths below
              now go through so the two modes can never disagree with
              each other about how a pair is scored. This is the
              "upload a folder, get flagged results" flow from the plan.

  Saved run   Loads the dataset's precomputed results/composite_results.csv
              and results/groups.csv (from 4_clustering_and_diff.py) so
              you can browse the full labeled 120-pair run without
              re-scoring anything.

Either way you get: a similarity heatmap, a sortable flagged-pairs/groups
table, a click-to-diff view, and a cluster graph of suspicion groups.

Run from the repo root:
    streamlit run app.py
"""

from __future__ import annotations

import importlib.util
import sys
from difflib import HtmlDiff
from itertools import combinations
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).parent
SIM_ENGINE = ROOT / "similarity_engine"
sys.path.insert(0, str(SIM_ENGINE))

from tokenizer import get_ngrams  # noqa: E402
from token_similarity import jaccard_similarity  # noqa: E402
from winnowing import fingerprint_similarity  # noqa: E402
from composite import load_model, composite_score, verdict_label  # noqa: E402


def _load_module(filename: str):
    """1_preprocess.py etc. can't be `import`-ed (leading digit), so load
    them by file path instead."""
    path = ROOT / filename
    spec = importlib.util.spec_from_file_location(filename[:-3], path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


preprocess_mod = _load_module("1_preprocess.py")
structural_mod = _load_module("3_structural_similarity.py")

st.set_page_config(page_title="Plagiarism Detector", layout="wide")
st.title("Programming Assignment Similarity Detector")


# ---------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------
def basename(p: str) -> str:
    return str(p).replace("\\", "/").split("/")[-1]


def build_group_table(files: list[str], score_matrix: np.ndarray, threshold: float) -> pd.DataFrame:
    """Connected components of the thresholded similarity graph -> suspicion groups."""
    g = nx.Graph()
    g.add_nodes_from(files)
    for i, j in combinations(range(len(files)), 2):
        if score_matrix[i, j] >= threshold:
            g.add_edge(files[i], files[j], weight=score_matrix[i, j])

    rows = []
    for k, comp in enumerate(nx.connected_components(g), start=1):
        if len(comp) < 2:
            continue
        edges = list(g.subgraph(comp).edges(data=True))
        rows.append({
            "group_id": f"group_{k}",
            "size": len(comp),
            "files": ", ".join(sorted(comp)),
            "num_flagged_edges": len(edges),
            "avg_score": round(sum(d["weight"] for _, _, d in edges) / max(len(edges), 1), 4),
        })
    return pd.DataFrame(rows)


def plot_heatmap(files: list[str], matrix: np.ndarray, title: str):
    fig = go.Figure(data=go.Heatmap(
        z=matrix, x=files, y=files, colorscale="Reds", zmin=0, zmax=1,
        colorbar=dict(title="score"),
    ))
    fig.update_layout(title=title, height=500, xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)


def plot_cluster_graph(files: list[str], score_matrix: np.ndarray, threshold: float):
    g = nx.Graph()
    g.add_nodes_from(files)
    for i, j in combinations(range(len(files)), 2):
        if score_matrix[i, j] >= threshold:
            g.add_edge(files[i], files[j], weight=score_matrix[i, j])

    if g.number_of_edges() == 0:
        st.info("No edges above the current threshold — nothing to cluster yet.")
        return

    pos = nx.spring_layout(g, seed=42, k=0.9)
    edge_x, edge_y = [], []
    for a, b in g.edges():
        edge_x += [pos[a][0], pos[b][0], None]
        edge_y += [pos[a][1], pos[b][1], None]
    edge_trace = go.Scatter(x=edge_x, y=edge_y, mode="lines",
                             line=dict(width=1.5, color="#bbb"), hoverinfo="none")

    node_x = [pos[n][0] for n in g.nodes()]
    node_y = [pos[n][1] for n in g.nodes()]
    degrees = [g.degree(n) for n in g.nodes()]
    node_trace = go.Scatter(
        x=node_x, y=node_y, mode="markers+text", text=list(g.nodes()),
        textposition="top center",
        marker=dict(size=[14 + 4 * d for d in degrees], color=degrees,
                    colorscale="Oranges", showscale=False, line=dict(width=1, color="#333")),
        hoverinfo="text",
    )
    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(showlegend=False, height=500, margin=dict(l=10, r=10, t=10, b=10),
                       xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True)


DIFF_CSS = """
<style>
  table.diff { font-family: Consolas, monospace; font-size: 0.8rem; border-collapse: collapse; width: 100%; }
  table.diff td { padding: 1px 4px; }
  .diff_header { background: #f0f0f0; } td.diff_header { text-align: right; color: #888; }
  .diff_next { background: #f0f0f0; } .diff_add { background: #d4f7d4; }
  .diff_chg { background: #fff3b8; } .diff_sub { background: #fdd; }
</style>
"""


def show_diff(label_a: str, text_a: str, label_b: str, text_b: str):
    table = HtmlDiff(wrapcolumn=60).make_table(
        text_a.splitlines(), text_b.splitlines(), fromdesc=label_a, todesc=label_b, context=False
    )
    import streamlit.components.v1 as components
    components.html(DIFF_CSS + table, height=500, scrolling=True)


def flagged_pair_picker(pairs_df: pd.DataFrame, key: str):
    """Sortable table + a selectbox to drive the diff view (works on any
    Streamlit version; row-click selection isn't relied on)."""
    st.dataframe(
        pairs_df.sort_values("score", ascending=False).reset_index(drop=True),
        use_container_width=True, height=300,
    )
    options = [f"{r.file_a}  vs  {r.file_b}  (score={r.score:.3f})"
               for r in pairs_df.sort_values("score", ascending=False).itertuples()]
    if not options:
        return None
    choice = st.selectbox("Pick a pair to view the diff", options, key=key)
    idx = options.index(choice)
    return pairs_df.sort_values("score", ascending=False).reset_index(drop=True).iloc[idx]


# ---------------------------------------------------------------------
# Mode 1: Live scan of uploaded files
# ---------------------------------------------------------------------
def live_scan_mode():
    st.subheader("Upload files to scan")
    uploads = st.file_uploader("Python files (.py) — select several at once", type=["py"],
                                accept_multiple_files=True)
    use_embeddings = st.checkbox(
        "Also compute CodeBERT embeddings (slower — needs torch + "
        "transformers, downloads ~500MB the first time)", value=False,
    )
    threshold_override = st.slider("Flagging threshold override (composite score)", 0.0, 1.0, -1.0, 0.01,
                                    help="Leave at -1 to use the trained model's own threshold.")

    if not uploads or len(uploads) < 2:
        st.info("Upload at least two .py files to compare.")
        return

    names = [u.name for u in uploads]
    raw_sources = {u.name: u.getvalue().decode("utf-8", errors="ignore") for u in uploads}

    # Preprocess: strip comments/docstrings, canonicalize identifiers, tokenize.
    normalized, tokens = {}, {}
    for name, source in raw_sources.items():
        try:
            no_comments = preprocess_mod.strip_comments_and_docstrings(source)
            canonical = preprocess_mod.canonicalize_identifiers(no_comments)
            norm = preprocess_mod.normalize_whitespace(canonical)
            normalized[name] = norm
            tokens[name] = preprocess_mod.tokenize_source(norm)
        except Exception as e:
            st.warning(f"Skipping {name}: couldn't preprocess ({e})")
    names = [n for n in names if n in normalized]
    if len(names) < 2:
        st.error("Fewer than two files parsed successfully — nothing to compare.")
        return

    model = load_model(str(ROOT / "results" / "composite_model.json"))

    embedder = None
    embeddings = None
    if use_embeddings:
        with st.spinner("Loading CodeBERT and embedding files (first run downloads the model)…"):
            from embedding_similarity import make_embedder, cosine_matrix
            embedder = make_embedder("codebert")
            embeddings = cosine_matrix(embedder.embed([raw_sources[n] for n in names]))

    n = len(names)
    score_matrix = np.zeros((n, n))
    pair_rows = []
    with st.spinner("Scoring all pairs…"):
        for i, j in combinations(range(n), 2):
            a, b = names[i], names[j]
            jac = jaccard_similarity(tokens[a], tokens[b])
            win = fingerprint_similarity(tokens[a], tokens[b])
            struct = structural_mod.structural_similarity(
                _TextAsPath(raw_sources[a]), _TextAsPath(raw_sources[b])
            ) or 0.0

            # Always go through composite_score() -- with an "embedding"
            # value it applies the fitted 4-signal weighted model; without
            # one it falls back to composite.py's own plain average of
            # jaccard/winnow/structural and that fallback's own
            # separately-tuned threshold (model["no_embedding"]). Scoring
            # this by hand here (as an earlier version of this file did,
            # re-normalizing the 4-signal weights over 3 signals) gives a
            # DIFFERENT number than composite.py's own no-embedding
            # metrics were computed against -- routing both cases through
            # the same function is what keeps "flagged" meaning the same
            # thing everywhere in the project.
            signal_values = {"jaccard": jac, "winnow": win, "structural": struct}
            if embeddings is not None:
                signal_values["embedding"] = float(embeddings[i, j])
            sc, flagged = composite_score(model, signal_values)

            score_matrix[i, j] = score_matrix[j, i] = sc
            pair_rows.append({
                "file_a": a, "file_b": b, "score": round(sc, 4), "flagged": bool(flagged),
                "jaccard": round(jac, 4), "winnow": round(win, 4), "structural": round(struct, 4),
                "embedding": round(signal_values.get("embedding", float("nan")), 4) if embeddings is not None else None,
            })
    np.fill_diagonal(score_matrix, 1.0)
    pairs_df = pd.DataFrame(pair_rows)

    # The model's OWN default threshold depends on which mode we're in --
    # the full model's threshold only makes sense for 4-signal scores, the
    # no_embedding threshold only for the 3-signal average. Pick the one
    # that actually matches what was just computed above.
    default_threshold = model["t"] if embeddings is not None else model["no_embedding"]["threshold"]
    threshold = default_threshold if threshold_override < 0 else threshold_override
    pairs_df["flagged"] = pairs_df["score"] >= threshold
    pairs_df["verdict"] = pairs_df["flagged"].map({True: verdict_label(True), False: verdict_label(False)})

    st.caption(f"Using threshold = {threshold:.3f}"
               + ("" if threshold_override < 0 else " (overridden — trained model default is "
                                                      f"{default_threshold:.3f})"))

    tab_heat, tab_flags, tab_diff, tab_graph = st.tabs(
        ["Similarity heatmap", "Flagged pairs", "Diff viewer", "Cluster graph"]
    )
    with tab_heat:
        plot_heatmap(names, score_matrix, "Pairwise composite similarity")
    with tab_flags:
        flagged_df = pairs_df[pairs_df["flagged"]].copy()
        st.write(f"**{len(flagged_df)} of {len(pairs_df)} pairs flagged** "
                 f"({(pairs_df['verdict'] == verdict_label(True)).sum()} PLAGIARIZED, "
                 f"{(pairs_df['verdict'] == verdict_label(False)).sum()} NOT PLAGIARIZED)")
        display_cols = ["file_a", "file_b", "verdict", "score", "jaccard", "winnow", "structural", "embedding"]
        st.dataframe(pairs_df.sort_values("score", ascending=False)[display_cols],
                     use_container_width=True, height=300)
        groups = build_group_table(names, score_matrix, threshold)
        st.write("**Suspicion groups (connected components of flagged pairs)**")
        st.dataframe(groups, use_container_width=True) if len(groups) else st.info("No groups yet.")
    with tab_diff:
        row = flagged_pair_picker(pairs_df, key="live_pair_picker")
        if row is not None:
            show_diff(row.file_a, raw_sources[row.file_a], row.file_b, raw_sources[row.file_b])
    with tab_graph:
        plot_cluster_graph(names, score_matrix, threshold)


class _TextAsPath:
    """Lets structural_similarity() (which expects a Path) work on an
    in-memory string without touching disk."""
    def __init__(self, text: str):
        self._text = text

    def read_text(self, encoding="utf-8", errors="ignore"):
        return self._text


# ---------------------------------------------------------------------
# Mode 2: Browse the precomputed dataset run
# ---------------------------------------------------------------------
def saved_run_mode():
    results_path = ROOT / "results" / "composite_results.csv"
    if not results_path.exists():
        st.error("results/composite_results.csv not found — run similarity_engine/composite.py first.")
        return
    df = pd.read_csv(results_path)
    df["file_a"] = df["file_a"].map(basename)
    df["file_b"] = df["file_b"].map(basename)

    problems = sorted(df["problem_id"].unique())
    problem = st.selectbox("Problem", problems)
    sub = df[df["problem_id"] == problem].reset_index(drop=True)

    files = sorted(set(sub["file_a"]) | set(sub["file_b"]))
    idx = {f: i for i, f in enumerate(files)}
    n = len(files)
    matrix = np.eye(n)
    for _, r in sub.iterrows():
        matrix[idx[r["file_a"]], idx[r["file_b"]]] = r["composite"]
        matrix[idx[r["file_b"]], idx[r["file_a"]]] = r["composite"]

    threshold = float(json_threshold())
    if "verdict" not in sub.columns:
        # Stale results/composite_results.csv from an older composite.py
        # that didn't write this column yet -- derive it from "flagged"
        # instead of crashing. Re-run composite.py to get it for real.
        sub = sub.copy()
        sub["verdict"] = sub["flagged"].map({1: verdict_label(True), 0: verdict_label(False)})
        st.warning("results/composite_results.csv has no 'verdict' column (it's from an older "
                   "composite.py run) -- showing a verdict derived from 'flagged' instead. "
                   "Re-run `python similarity_engine/composite.py` to regenerate it properly.")
    pairs_df = sub.rename(columns={"composite": "score"})[["file_a", "file_b", "score", "flagged", "verdict"]]

    tab_heat, tab_flags, tab_diff, tab_graph = st.tabs(
        ["Similarity heatmap", "Flagged pairs", "Diff viewer", "Cluster graph"]
    )
    with tab_heat:
        plot_heatmap(files, matrix, f"{problem}: composite similarity")
    with tab_flags:
        flagged_df = pairs_df[pairs_df["flagged"] == 1]
        st.write(f"**{len(flagged_df)} of {len(pairs_df)} pairs flagged** in {problem} "
                 f"({(pairs_df['verdict'] == verdict_label(True)).sum()} PLAGIARIZED, "
                 f"{(pairs_df['verdict'] == verdict_label(False)).sum()} NOT PLAGIARIZED)")
        st.dataframe(pairs_df.sort_values("score", ascending=False), use_container_width=True, height=300)
        groups_path = ROOT / "results" / "groups.csv"
        if groups_path.exists():
            groups = pd.read_csv(groups_path)
            st.write("**Suspicion groups**")
            st.dataframe(groups[groups["problem_id"] == problem], use_container_width=True)
    with tab_diff:
        row = flagged_pair_picker(pairs_df, key="saved_pair_picker")
        if row is not None:
            path_a = ROOT / "dataset" / problem / row.file_a
            path_b = ROOT / "dataset" / problem / row.file_b
            if path_a.exists() and path_b.exists():
                show_diff(row.file_a, path_a.read_text(errors="ignore"),
                           row.file_b, path_b.read_text(errors="ignore"))
            else:
                st.warning("Source files not found under dataset/ — can't render the diff.")
    with tab_graph:
        plot_cluster_graph(files, matrix, threshold)


def json_threshold() -> float:
    model = load_model(str(ROOT / "results" / "composite_model.json"))
    return model["t"]


# ---------------------------------------------------------------------
# Sidebar / entry point
# ---------------------------------------------------------------------
mode = st.sidebar.radio("Mode", ["Saved run (labeled dataset)", "Live scan (upload files)"])
st.sidebar.caption(
    "Saved run browses the precomputed results from the labeled dataset. "
    "Live scan lets you drag in any .py files and scores them on the spot."
)

if mode.startswith("Saved"):
    saved_run_mode()
else:
    live_scan_mode()