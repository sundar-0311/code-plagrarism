"""
embedding_similarity.py

Semantic similarity signal. Every source file is turned into a single
vector (an "embedding") and two files are compared with cosine
similarity. Unlike Jaccard / winnowing (which look for shared token
sequences) and the AST signal (which looks for shared tree shape), an
embedding model has read millions of programs, so it can score two
files as close when they *do the same thing* even if the text and the
structure differ.

Two backends are provided behind the same interface:

  * "codebert" -- microsoft/codebert-base from HuggingFace (the real
                  semantic signal; needs torch + transformers and a
                  one-time ~500 MB model download).
  * "tfidf"    -- TF-IDF over code tokens. NOT semantic (it is still
                  a bag-of-tokens method), but it needs no download and
                  runs in a second. Use it to test the pipeline, or as
                  the fallback if CodeBERT is too slow on your machine.

Both expose:   embedder.embed(list_of_source_strings) -> (N, D) array
"""

from __future__ import annotations

import numpy as np

CODEBERT_NAME = "microsoft/codebert-base"
MAX_LENGTH = 512  # CodeBERT's hard input limit, counted in sub-word tokens


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
# Factory
# ---------------------------------------------------------------------
def make_embedder(backend: str):
    if backend == "codebert":
        return CodeBertEmbedder()
    if backend == "tfidf":
        return TfidfEmbedder()
    raise ValueError(f"Unknown backend '{backend}' (use 'codebert' or 'tfidf')")


if __name__ == "__main__":
    # Tiny smoke test with the TF-IDF backend (no downloads needed).
    demo = [
        "def f(a, b):\n    return a + b\n",
        "def g(x, y):\n    return x + y\n",
        "for i in range(10):\n    print(i)\n",
    ]
    sim = cosine_matrix(TfidfEmbedder().embed(demo))
    print(np.round(sim, 3))