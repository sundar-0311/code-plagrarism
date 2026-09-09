"""
Normalizes Python source files for plagiarism comparison:
  1. Strips comments and docstrings
  2. Normalizes whitespace
  3. Renames identifiers (variables, function names, args) to VAR1, VAR2...
     in first-seen order, so renamed-variable variants collapse to the
     same canonical form. Keywords, builtins, and imported/dotted names
     are left untouched so the code stays parseable-in-spirit.

Usage:
    python preprocess.py <input_dir> <output_dir>

    <input_dir>  : root folder containing .py files (searched recursively)
    <output_dir> : where normalized copies are written, mirroring the
                   input folder structure. A .tokens file (space-joined
                   token stream) is written alongside each .py file for
                   fast similarity comparison later.
"""

import ast
import builtins
import io
import keyword
import sys
import tokenize
from pathlib import Path

BUILTIN_NAMES = set(dir(builtins))
KEYWORDS = set(keyword.kwlist)


class IdentifierCanonicalizer(ast.NodeTransformer):
    """Renames user-defined names (functions, variables, args) to VAR1, VAR2...
    in first-seen order. Skips builtins, keywords, dunder names, and
    attribute/module references (e.g. `math.sqrt` keeps `math`)."""

    def __init__(self):
        self.mapping = {}
        self.counter = 0

    def _canonical(self, name):
        if name in BUILTIN_NAMES or name in KEYWORDS or name.startswith("__"):
            return name
        if name not in self.mapping:
            self.counter += 1
            self.mapping[name] = f"VAR{self.counter}"
        return self.mapping[name]

    def visit_Name(self, node):
        node.id = self._canonical(node.id)
        return node

    def visit_FunctionDef(self, node):
        node.name = self._canonical(node.name)
        self.generic_visit(node)
        return node

    def visit_arg(self, node):
        node.arg = self._canonical(node.arg)
        return node


def strip_comments_and_docstrings(source: str) -> str:
    """Removes comments and standalone/docstring string literals via the
    tokenizer + AST, then reconstructs cleaned source."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        # If it doesn't parse, fall back to comment-only stripping.
        return _strip_comments_only(source)

    for node in ast.walk(tree):
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)
        ):
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            ):
                node.body = node.body[1:] or [ast.Pass()]

    return ast.unparse(tree)


def _strip_comments_only(source: str) -> str:
    out = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for tok_type, tok_string, *_ in tokens:
            if tok_type != tokenize.COMMENT:
                out.append(tok_string)
    except tokenize.TokenizeError:
        return source
    return " ".join(out)


def canonicalize_identifiers(source: str) -> str:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source
    canon = IdentifierCanonicalizer()
    new_tree = canon.visit(tree)
    ast.fix_missing_locations(new_tree)
    return ast.unparse(new_tree)


def normalize_whitespace(source: str) -> str:
    lines = [line.strip() for line in source.splitlines() if line.strip()]
    return "\n".join(lines)


def tokenize_source(source: str) -> list[str]:
    """Returns a flat list of meaningful tokens (ignoring whitespace,
    comments, and encoding markers) for sequence-based comparison."""
    tokens = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(source).readline):
            tok_type, tok_string = tok.type, tok.string
            if tok_type in (
                tokenize.NEWLINE,
                tokenize.NL,
                tokenize.INDENT,
                tokenize.DEDENT,
                tokenize.COMMENT,
                tokenize.ENCODING,
                tokenize.ENDMARKER,
            ):
                continue
            if tok_string.strip() == "":
                continue
            tokens.append(tok_string)
    except tokenize.TokenizeError:
        pass
    return tokens


def process_file(path: Path) -> tuple[str, list[str]]:
    source = path.read_text(encoding="utf-8", errors="ignore")
    no_comments = strip_comments_and_docstrings(source)
    canonical = canonicalize_identifiers(no_comments)
    normalized = normalize_whitespace(canonical)
    tokens = tokenize_source(normalized)
    return normalized, tokens


def main():
    if len(sys.argv) != 3:
        print("Usage: python preprocess.py <input_dir> <output_dir>")
        sys.exit(1)

    input_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])

    py_files = sorted(input_dir.rglob("*.py"))
    if not py_files:
        print(f"No .py files found under {input_dir}")
        sys.exit(1)

    count = 0
    for path in py_files:
        rel = path.relative_to(input_dir)
        out_path = output_dir / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            normalized, tokens = process_file(path)
        except Exception as e:
            print(f"  [skip] {rel} -> error: {e}")
            continue

        out_path.write_text(normalized, encoding="utf-8")
        tokens_path = out_path.with_suffix(".tokens")
        tokens_path.write_text(" ".join(tokens), encoding="utf-8")
        count += 1
        print(f"  [ok] {rel}")

    print(f"\nProcessed {count}/{len(py_files)} files. Output in: {output_dir}")


if __name__ == "__main__":
    main()