"""
tokenizer.py

Converts a flat token list into overlapping n-grams (windows of n
consecutive tokens). N-grams are more distinctive than single tokens
and are the shared input for both token_similarity.py and winnowing.py.
"""


def get_ngrams(tokens: list[str], n: int = 5) -> list[tuple[str, ...]]:
    """Returns overlapping n-grams from a token list.

    Example: tokens=['a','b','c','d'], n=2
    -> [('a','b'), ('b','c'), ('c','d')]

    If there are fewer than n tokens, returns a single n-gram covering
    everything (so very short files still produce at least one n-gram
    instead of an empty list).
    """
    if len(tokens) < n:
        return [tuple(tokens)] if tokens else []
    return [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


if __name__ == "__main__":
    # Quick manual test with a small fake token list.
    sample_tokens = ["def", "VAR1", "(", "VAR2", ")", ":", "return", "VAR2"]
    ngrams = get_ngrams(sample_tokens, n=3)
    print(f"Input: {sample_tokens}")
    print(f"Number of 3-grams: {len(ngrams)}")
    for g in ngrams:
        print(" ", g)