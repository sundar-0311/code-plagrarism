"""
embedding_similarity.py

Semantic similarity signal. Every source file is turned into a single
vector (an "embedding") and two files are compared with cosine
similarity. Unlike Jaccard / winnowing (which look for shared token
sequences) and the AST signal (which looks for shared tree shape), an
embedding model has read millions of programs, so it can score two
files as close when they *do the same thing* even if the text and the
structure differ.

Three backends are provided behind the same interface:

  * "codebert"      -- microsoft/codebert-base from HuggingFace. Reads
                        code as plain text -- no awareness of which
                        identifier depends on which.
  * "graphcodebert" -- microsoft/graphcodebert-base. Same idea, but
                        additionally fed a data-flow graph (which
                        identifier's value comes from which other
                        identifier's value; see dfg_extractor.py), so
                        it can tell that two files compute the same
                        thing even when every variable was renamed and
                        every line reordered -- not just that the text
                        looks similar. Needs torch + transformers +
                        tree-sitter, and a one-time ~500 MB download.
  * "tfidf"         -- TF-IDF over code tokens. NOT semantic (it is
                        still a bag-of-tokens method), but it needs no
                        download and runs in a second. Use it to test
                        the pipeline, or as a fallback.

All three expose:   embedder.embed(list_of_source_strings) -> (N, D) array
"""

from __future__ import annotations

import numpy as np

CODEBERT_NAME = "microsoft/codebert-base"
GRAPHCODEBERT_NAME = "microsoft/graphcodebert-base"
MAX_LENGTH = 512  # both models' hard input limit, counted in sub-word tokens


# ---------------------------------------------------------------------
# Cosine similarity
# ---------------------------------------------------------------------
def l2_normalize(matrix: np.ndarray) -> np.ndarray:
    """Scale every row to length 1, so a dot product equals cosine."""
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def cosine_matrix(embeddings: np.ndarray) -> np.ndarray:
    """N x N matrix where entry [i, j] = cosine(embedding_i, embedding_j)."""
    unit = l2_normalize(np.asarray(embeddings, dtype=np.float64))
    return unit @ unit.T


# ---------------------------------------------------------------------
# Backend 1: TF-IDF (cheap, non-semantic fallback)
# ---------------------------------------------------------------------
class TfidfEmbedder:
    name = "tfidf"

    def embed(self, texts: list[str]) -> np.ndarray:
        from sklearn.feature_extraction.text import TfidfVectorizer

        # Identifier/keyword, number, or any single symbol -- works on both
        # raw .py source and the space-separated .tokens style.
        vectorizer = TfidfVectorizer(
            token_pattern=r"[A-Za-z_]\w*|\d+|[^\sA-Za-z_\d]",
            ngram_range=(1, 2),
            lowercase=False,
        )
        return vectorizer.fit_transform(texts).toarray()


# ---------------------------------------------------------------------
# Backend 2: CodeBERT (the real semantic signal)
# ---------------------------------------------------------------------
class CodeBertEmbedder:
    name = "codebert"

    def __init__(self, model_name: str = CODEBERT_NAME, device: str | None = None,
                 tokenizer=None, model=None):
        # Imported here so the TF-IDF backend works without torch installed.
        import torch
        from transformers import AutoModel, AutoTokenizer

        self.torch = torch
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = tokenizer or AutoTokenizer.from_pretrained(model_name)
        model = model or AutoModel.from_pretrained(model_name)
        self.model = model.to(self.device).eval()  # eval(): switch dropout off

    def embed(self, texts: list[str], batch_size: int = 8) -> np.ndarray:
        torch = self.torch

        # Warn if any file will be cut off at 512 sub-word tokens.
        lengths = [len(ids) for ids in self.tokenizer(texts, truncation=False)["input_ids"]]
        too_long = sum(1 for n in lengths if n > MAX_LENGTH)
        if too_long:
            print(f"  WARNING: {too_long} file(s) exceed {MAX_LENGTH} tokens and will be truncated")

        vectors = []
        with torch.no_grad():  # inference only: no gradients, less memory
            for start in range(0, len(texts), batch_size):
                batch = texts[start:start + batch_size]
                enc = self.tokenizer(
                    batch,
                    padding=True,          # pad shorter files in the batch
                    truncation=True,
                    max_length=MAX_LENGTH,
                    return_tensors="pt",
                ).to(self.device)

                # One 768-dim vector per sub-word token: (batch, tokens, 768)
                hidden = self.model(**enc).last_hidden_state

                # Mean-pool over real tokens only (mask out the padding), so
                # each file collapses to a single 768-dim vector.
                mask = enc["attention_mask"].unsqueeze(-1).float()
                pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
                vectors.append(pooled.cpu().numpy())

        return np.vstack(vectors)


# ---------------------------------------------------------------------
# Backend 3: GraphCodeBERT (semantic signal + data-flow structure)
# ---------------------------------------------------------------------
# How much of the 512-token budget goes to actual code vs. to DFG
# nodes. 1 (CLS) + CODE_LENGTH + 1 (SEP) + DFG_LENGTH = 512 exactly.
CODE_LENGTH = 400
DFG_LENGTH = 110


def _build_graphcodebert_input(tokenizer, code_tokens: list[str], dfg_edges: list[tuple]):
    """Turns one file's (code_tokens, dfg_edges) -- see dfg_extractor.py
    -- into the combined input GraphCodeBERT expects: sub-word code
    tokens followed by one placeholder slot per retained DFG node,
    plus the position ids and the pairwise attention mask that
    actually encodes the graph structure.

    Returns (input_ids, position_idx, attn_mask, pooling_mask, kept_edge_count):
      input_ids     -- token ids, length = code_region_len + n_dfg_nodes
      position_idx  -- sequential for CLS/code/SEP, constant 0 for every
                        DFG node (they have no sequential meaning --
                        only the attention mask's graph edges matter)
      attn_mask     -- (L, L) bool matrix: True where position i may
                        attend to position j
      pooling_mask  -- (L,) bool, True over code sub-word positions
                        only (excludes CLS/SEP/DFG slots) -- this is
                        what embed() mean-pools over
    """
    # 1. Sub-word tokenize each code token individually, remembering
    #    which sub-word slice each landed in (so a DFG node can point
    #    back at the right span).
    subtoken_lists = [tokenizer.tokenize(t) or [tokenizer.unk_token] for t in code_tokens]
    ori2cur_pos = {}
    cur = 0
    for i, sub in enumerate(subtoken_lists):
        ori2cur_pos[i] = (cur, cur + len(sub))
        cur += len(sub)
    code_subtokens = [s for sub in subtoken_lists for s in sub][:CODE_LENGTH]
    valid_code_len = len(code_subtokens)

    # 2. Keep only DFG edges whose own token, and whose source tokens,
    #    still fall inside the retained (possibly truncated) code
    #    region -- a truncated-away token can't be pointed at.
    kept_edges = []
    for idx, name, rel, sources in dfg_edges:
        start, _ = ori2cur_pos.get(idx, (None, None))
        if start is None or start >= valid_code_len:
            continue
        kept_sources = [s for s in sources
                         if ori2cur_pos.get(s, (None,))[0] is not None
                         and ori2cur_pos[s][0] < valid_code_len]
        kept_edges.append((idx, name, rel, kept_sources))
    kept_edges = kept_edges[:DFG_LENGTH]
    node_pos_of_token = {e[0]: slot for slot, e in enumerate(kept_edges)}

    # 3. Assemble input ids: [CLS] code_subtokens [SEP] dfg_placeholders.
    #    Each DFG node is ONE slot (not one per sub-word) -- its content
    #    comes entirely from the attention mask linking it back to real
    #    code tokens, so it gets a neutral placeholder id (unk).
    input_ids = (
        [tokenizer.cls_token_id]
        + tokenizer.convert_tokens_to_ids(code_subtokens)
        + [tokenizer.sep_token_id]
        + [tokenizer.unk_token_id] * len(kept_edges)
    )

    code_region_len = 1 + valid_code_len + 1  # CLS + code + SEP
    position_idx = list(range(code_region_len)) + [0] * len(kept_edges)

    total_len = code_region_len + len(kept_edges)
    attn = np.zeros((total_len, total_len), dtype=bool)
    attn[:code_region_len, :code_region_len] = True  # code block: full bidirectional

    dfg_start = code_region_len
    for slot, (idx, name, rel, sources) in enumerate(kept_edges):
        node_pos = dfg_start + slot
        attn[node_pos, node_pos] = True
        start, end = ori2cur_pos[idx]
        start, end = start + 1, end + 1  # +1 to account for CLS at position 0
        attn[node_pos, start:end] = True   # node <-> the code span it represents
        attn[start:end, node_pos] = True
        for s in sources:
            if s in node_pos_of_token:      # node <-> the node(s) it's computed from
                other = dfg_start + node_pos_of_token[s]
                attn[node_pos, other] = True
                attn[other, node_pos] = True

    pooling_mask = np.zeros(total_len, dtype=bool)
    pooling_mask[1:1 + valid_code_len] = True  # code sub-words only

    return input_ids, position_idx, attn, pooling_mask


class GraphCodeBertEmbedder:
    name = "graphcodebert"

    def __init__(self, model_name: str = GRAPHCODEBERT_NAME, device: str | None = None,
                 tokenizer=None, model=None):
        import torch
        from transformers import AutoModel, AutoTokenizer
        from dfg_extractor import extract_dataflow

        self.torch = torch
        self.extract_dataflow = extract_dataflow
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = tokenizer or AutoTokenizer.from_pretrained(model_name)
        model = model or AutoModel.from_pretrained(model_name)
        self.model = model.to(self.device).eval()

    def embed(self, texts: list[str], batch_size: int = 8) -> np.ndarray:
        torch = self.torch

        # Build the (input_ids, position_idx, attn, pooling_mask) tuple
        # for every file up front, so batching just has to pad them to
        # a common length.
        built = []
        for text in texts:
            code_tokens, dfg_edges = self.extract_dataflow(text)
            built.append(_build_graphcodebert_input(self.tokenizer, code_tokens, dfg_edges))

        vectors = []
        with torch.no_grad():
            for start in range(0, len(built), batch_size):
                batch = built[start:start + batch_size]
                max_len = max(len(b[0]) for b in batch)

                ids = torch.full((len(batch), max_len), self.tokenizer.pad_token_id, dtype=torch.long)
                pos = torch.zeros((len(batch), max_len), dtype=torch.long)
                attn = torch.zeros((len(batch), max_len, max_len), dtype=torch.bool)
                pool = torch.zeros((len(batch), max_len), dtype=torch.bool)

                for i, (input_ids, position_idx, attn_mask, pooling_mask) in enumerate(batch):
                    L = len(input_ids)
                    ids[i, :L] = torch.tensor(input_ids, dtype=torch.long)
                    pos[i, :L] = torch.tensor(position_idx, dtype=torch.long)
                    attn[i, :L, :L] = torch.tensor(attn_mask, dtype=torch.bool)
                    pool[i, :L] = torch.tensor(pooling_mask, dtype=torch.bool)

                ids, pos, attn, pool = (t.to(self.device) for t in (ids, pos, attn, pool))

                # 3-D attention_mask is the documented way to hand a
                # model.transformers custom pairwise mask instead of
                # the usual 2-D padding mask -- it's expanded internally
                # to (batch, 1, L, L) and applied per attention head.
                hidden = self.model(input_ids=ids, attention_mask=attn, position_ids=pos).last_hidden_state

                mask = pool.unsqueeze(-1).float()
                pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
                vectors.append(pooled.cpu().numpy())

        return np.vstack(vectors)


# ---------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------
def make_embedder(backend: str):
    if backend == "codebert":
        return CodeBertEmbedder()
    if backend == "graphcodebert":
        return GraphCodeBertEmbedder()
    if backend == "tfidf":
        return TfidfEmbedder()
    raise ValueError(f"Unknown backend '{backend}' (use 'codebert', 'graphcodebert', or 'tfidf')")


if __name__ == "__main__":
    # Tiny smoke test with the TF-IDF backend (no downloads needed).
    demo = [
        "def f(a, b):\n    return a + b\n",
        "def g(x, y):\n    return x + y\n",
        "for i in range(10):\n    print(i)\n",
    ]
    sim = cosine_matrix(TfidfEmbedder().embed(demo))
    print(np.round(sim, 3))