"""Safe, conservative source transformations used by the CLI."""

from __future__ import annotations

import ast


class _DocstringRemover(ast.NodeTransformer):
    """Remove Python docstrings while preserving executable statements."""

    @staticmethod
    def _without_docstring(node: ast.AST) -> ast.AST:
        body = getattr(node, "body", None)
        if not isinstance(body, list) or not body:
            return node

        first_statement = body[0]
        is_docstring = (
            isinstance(first_statement, ast.Expr)
            and isinstance(first_statement.value, ast.Constant)
            and isinstance(first_statement.value.value, str)
        )
        if is_docstring:
            node.body = body[1:] or [ast.Pass()]  # type: ignore[attr-defined]
        return node

    def visit_Module(self, node: ast.Module) -> ast.AST:
        self.generic_visit(node)
        return self._without_docstring(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        self.generic_visit(node)
        return self._without_docstring(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        self.generic_visit(node)
        return self._without_docstring(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        self.generic_visit(node)
        return self._without_docstring(node)


def strip_docstrings_and_comments(source_code: str) -> str:
    """Return valid Python source without comments or docstrings.

    ``ast.unparse`` intentionally formats the parsed program. It is used only
    for Python files; non-Python text is left unchanged by the caller so that
    comment-looking text inside strings or templates is never altered.
    """

    tree = ast.parse(source_code)
    cleaned_tree = _DocstringRemover().visit(tree)
    ast.fix_missing_locations(cleaned_tree)
    return ast.unparse(cleaned_tree)


def optimize_source(source_code: str, suffix: str) -> str:
    """Optimize Python conservatively and preserve every other file verbatim."""

    if suffix.lower() not in {".py", ".pyi", ".pyw"}:
        return source_code

    try:
        return strip_docstrings_and_comments(source_code)
    except SyntaxError:
        # A broken Python source file can still be useful context. Keeping it
        # intact is safer than applying regular expressions to arbitrary text.
        return source_code


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """Count tokens with tiktoken, falling back to a documented approximation."""

    try:
        import tiktoken

        encoding = tiktoken.get_encoding(model)
        return len(encoding.encode(text))
    except (ImportError, ValueError):
        # The approximation avoids making a missing optional encoder fatal.
        return max(1, len(text) // 4) if text else 0
