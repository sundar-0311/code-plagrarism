"""
dfg_extractor.py

Data-flow graph extraction for Python source, in the format
GraphCodeBERT (Guo et al., 2021) was trained on: every identifier
token in the code is linked to the earlier token(s) its value comes
from. In `ans = ans * x`, the `ans` on the left comes from the `ans`
and `x` on the right; a later `ans` inside a loop body comes from
*that* assignment, not from the original `ans = 1`. This is the
structural signal plain tokenization throws away -- two files that
rename every variable and reorder every line can still produce an
identical data-flow graph if the underlying computation is the same,
which is exactly the case (renamed identifiers, reformatted code) this
project needs to catch.

Implementation notes
---------------------
This is a Python-only, tree-sitter-based reimplementation of the
approach in the official GraphCodeBERT repo's parser/DFG.py, scoped to
the constructs that actually appear in this dataset (assignments,
augmented assignments, for loops, function definitions, and ordinary
expressions). Anything not explicitly handled falls through to a
generic "recurse into children left-to-right, thread the state dict
through" rule, so the extractor never raises on unfamiliar syntax --
worst case, a construct is treated as pure reads with no def/use edge,
which just means that piece contributes no DFG signal rather than
breaking the run.

Two-pass design (this matters for correctness, not just style):
  Pass 1 (`_collect_tokens`) walks the tree once, strictly in source
    order, and assigns every leaf node a token index. This is the
    same order a subword tokenizer will see when it tokenizes the
    plain source text, which is required later for lining up DFG node
    positions with the model's actual input.
  Pass 2 (`_dfg_walk`) walks the tree again, this time in *semantic*
    order (e.g. for `ans = ans * x`, it looks at the right-hand side
    before the left-hand side, because that's the actual data-flow
    direction) and builds edges by looking up each leaf's index from
    pass 1 -- it never assigns new indices itself.
  Keeping these separate avoids a subtle bug: if index assignment and
  edge-building were the same pass, augmented assignment (`ans *= x`,
  which both reads and writes `ans` from a single source token) would
  either double-count that token or assign indices out of source
  order.
"""

from __future__ import annotations

from tree_sitter import Language, Parser
import tree_sitter_python

_LANGUAGE = Language(tree_sitter_python.language())
_PARSER = Parser(_LANGUAGE)

_ASSIGN_OPS = {"=", "+=", "-=", "*=", "/=", "//=", "%=", "**=", "&=", "|=", "^=", ">>=", "<<="}

# (token_index, var_name, relation, [source_token_indices])
DfgEdge = tuple


# ---------------------------------------------------------------------
# Pass 1: source-order token collection
# ---------------------------------------------------------------------
def _leaf_text(node, code_bytes: bytes) -> str:
    return code_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _collect_tokens(node, code_bytes: bytes, tokens: list, index_to_code: dict) -> None:
    if len(node.children) == 0:
        key = (node.start_byte, node.end_byte)
        if key not in index_to_code:
            index_to_code[key] = len(tokens)
            tokens.append(_leaf_text(node, code_bytes))
        return
    for child in node.children:
        _collect_tokens(child, code_bytes, tokens, index_to_code)


# ---------------------------------------------------------------------
# Pass 2: semantic-order edge building
# ---------------------------------------------------------------------
def _idx(node, index_to_code: dict) -> int:
    return index_to_code[(node.start_byte, node.end_byte)]


def _dfg_generic(node, index_to_code, code_bytes, states):
    """Default rule: recurse into children left to right, threading
    `states` so later children see earlier children's definitions."""
    edges = []
    for child in node.children:
        e, states = _dfg_walk(child, index_to_code, code_bytes, states)
        edges += e
    return edges, states


def _dfg_identifier(node, index_to_code, code_bytes, states):
    name = _leaf_text(node, code_bytes)
    idx = _idx(node, index_to_code)
    if name in states:
        return [(idx, name, "comesFrom", list(states[name]))], states
    # Read of a name with no prior definition in scope (builtin,
    # unresolved import, or first use) -- indexed, but no source edge.
    return [(idx, name, "comesFrom", [])], states


def _dfg_assignment(node, index_to_code, code_bytes, states):
    """`target = value` or `target OP= value`. The value side is
    walked first (semantic order: it may read names already in
    `states`), then every identifier in `target` becomes a fresh
    definition pointing back at the value's source tokens. Augmented
    assignment additionally depends on the name's own prior value,
    since `x += 1` reads `x` before rewriting it -- without double
    counting the token, since pass 1 already gave it one index."""
    children = node.children
    try:
        eq_pos = next(i for i, c in enumerate(children) if c.type in _ASSIGN_OPS)
    except StopIteration:
        return _dfg_generic(node, index_to_code, code_bytes, states)

    left_nodes = children[:eq_pos]
    op_node = children[eq_pos]
    right_nodes = children[eq_pos + 1:]
    is_augmented = op_node.type != "="

    right_edges = []
    for c in right_nodes:
        e, states = _dfg_walk(c, index_to_code, code_bytes, states)
        right_edges += e
    right_sources = [e[0] for e in right_edges]

    def_edges = []
    for c in left_nodes:
        if c.type == "identifier":
            name = _leaf_text(c, code_bytes)
            idx = _idx(c, index_to_code)
            sources = list(right_sources)
            if is_augmented and name in states:
                sources = list(states[name]) + sources
            def_edges.append((idx, name, "computedFrom", sources))
            states = {**states, name: [idx]}
        else:
            # Non-identifier assignment target (subscript like arr[i],
            # attribute like node.next, tuple unpacking...). Walked as
            # a normal read -- imperfect (the container isn't marked
            # as "written"), but safe: no edge is fabricated.
            e, states = _dfg_walk(c, index_to_code, code_bytes, states)
            def_edges += e

    return right_edges + def_edges, states


def _dfg_for(node, index_to_code, code_bytes, states):
    """`for <left> in <right>: <body>`. `<right>` is evaluated first
    (normal reads); `<left>` is a fresh definition sourced from
    `<right>`; `<body>` (and any trailing `else:` clause) is then
    walked with the loop variable visible."""
    children = node.children
    try:
        in_pos = next(i for i, c in enumerate(children) if c.type == "in")
        colon_pos = next(i for i in range(in_pos + 1, len(children)) if children[i].type == ":")
    except StopIteration:
        return _dfg_generic(node, index_to_code, code_bytes, states)

    left_nodes = children[1:in_pos]
    right_nodes = children[in_pos + 1:colon_pos]
    rest = children[colon_pos:]

    right_edges = []
    for c in right_nodes:
        e, states = _dfg_walk(c, index_to_code, code_bytes, states)
        right_edges += e
    right_sources = [e[0] for e in right_edges]

    def_edges = []
    for c in left_nodes:
        if c.type == "identifier":
            name = _leaf_text(c, code_bytes)
            idx = _idx(c, index_to_code)
            def_edges.append((idx, name, "comesFrom", right_sources))
            states = {**states, name: [idx]}
        else:
            # Tuple-unpacking loop var, e.g. `for i, x in enumerate(...)`.
            e, states = _dfg_walk(c, index_to_code, code_bytes, states)
            def_edges += e

    rest_edges = []
    for c in rest:
        e, states = _dfg_walk(c, index_to_code, code_bytes, states)
        rest_edges += e

    return right_edges + def_edges + rest_edges, states


def _dfg_function_definition(node, index_to_code, code_bytes, states):
    """Parameters are fresh definitions with no earlier source (the
    caller's actual argument values aren't visible to us); the body is
    walked with them in scope."""
    edges = []
    for child in node.children:
        if child.type == "parameters":
            for p in child.children:
                if p.type == "identifier":
                    name = _leaf_text(p, code_bytes)
                    idx = _idx(p, index_to_code)
                    edges.append((idx, name, "comesFrom", []))
                    states = {**states, name: [idx]}
                else:
                    # default_parameter, typed_parameter, *args, **kwargs...
                    e, states = _dfg_walk(p, index_to_code, code_bytes, states)
                    edges += e
        else:
            e, states = _dfg_walk(child, index_to_code, code_bytes, states)
            edges += e
    return edges, states


_HANDLERS = {
    "assignment": _dfg_assignment,
    "augmented_assignment": _dfg_assignment,
    "for_statement": _dfg_for,
    "function_definition": _dfg_function_definition,
}


def _dfg_walk(node, index_to_code, code_bytes, states):
    if len(node.children) == 0:
        if node.type == "identifier":
            return _dfg_identifier(node, index_to_code, code_bytes, states)
        return [], states  # non-identifier leaf: already indexed in pass 1
    handler = _HANDLERS.get(node.type, _dfg_generic)
    return handler(node, index_to_code, code_bytes, states)


# ---------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------
def extract_dataflow(code: str) -> tuple[list[str], list[DfgEdge]]:
    """Parses `code` (one Python source file's text) and returns:

      code_tokens -- every leaf token (identifiers, literals,
                     operators, keywords, punctuation), in source
                     order. This is the token sequence
                     GraphCodeBertEmbedder feeds to the model as the
                     "code" half of its input.

      dfg_edges   -- one tuple per identifier token:
                     (token_index, var_name, relation, [source_indices])
                     `relation` is "comesFrom" (read, loop variable, or
                     function parameter) or "computedFrom" (assignment
                     target). `source_indices` index into `code_tokens`.

    Never raises: if parsing or graph-building hits something
    unanticipated, falls back to a plain whitespace/symbol split with
    no edges, so one malformed file can't take down a batch run.
    """
    try:
        code_bytes = code.encode("utf-8")
        tree = _PARSER.parse(code_bytes)
        tokens: list[str] = []
        index_to_code: dict = {}
        _collect_tokens(tree.root_node, code_bytes, tokens, index_to_code)
        edges, _ = _dfg_walk(tree.root_node, index_to_code, code_bytes, {})
        return tokens, edges
    except Exception:
        import re
        return re.findall(r"[A-Za-z_]\w*|\d+(?:\.\d+)?|[^\sA-Za-z_\d]", code), []


if __name__ == "__main__":
    sample = (
        "def factorial(num):\n"
        "    ans = 1\n"
        "    for x in range(1, num + 1):\n"
        "        ans = ans * x\n"
        "    return ans\n"
    )
    toks, dfg = extract_dataflow(sample)
    print(f"{len(toks)} code tokens: {toks}\n")
    for idx, name, rel, src in dfg:
        print(f"  [{idx:>2}] {name!r:<10} {rel:<13} from {[toks[i] for i in src]}")