# Token Diet

Token Diet creates one Markdown context file from a source tree and reports
the token count before and after conservative Python cleanup. It is intended
for preparing code context for review or an LLM prompt; it never sends files to
an API.

## What it does

- walks a directory deterministically and respects its `.gitignore`;
- excludes common generated, binary, dependency, credential, and key files by
  default;
- removes Python comments and docstrings through the Python AST, while leaving
  non-Python files unchanged;
- skips non-UTF-8, NUL-containing, unreadable, and oversized files;
- excludes the output file from the walk, even if it lives inside the source
  directory; and
- writes the resulting context file atomically.

## Install

This project requires Python 3.11 or later.

```bash
git clone https://github.com/turfin-logic/token-diet.git
cd token-diet
python -m pip install .
```

For development with [uv](https://docs.astral.sh/uv/):

```bash
uv sync --extra dev
```

## Use

```bash
token-diet --path ./my-project --output ./context.md
```

The same command is available without installation from a checkout:

```bash
python -m token_diet --path ./my-project --output ./context.md
```

Files larger than 1 MB are skipped by default. Increase or lower that cap when
needed:

```bash
token-diet --path ./my-project --output ./context.md --max-file-bytes 250000
```

The command prints processed/skipped file counts plus token totals. The output
is a context artifact, not a replacement for the original source tree.

## Safety boundaries

Token Diet excludes `.env` files, common private-key and certificate suffixes,
common credential filenames, dependency folders, lockfiles, and the patterns
in the target repository's `.gitignore`; symbolic links are also skipped.
Built-in exclusions cannot be unignored by a repository rule. This is defense
in depth, not a guarantee that every secret in arbitrary source code will be
found. Review the generated file before sharing it with any person or service.

Only Python files are transformed. Their output is reformatted by
`ast.unparse`; non-Python content is kept verbatim so comment-looking text in
templates and strings is not accidentally changed.

## Development checks

```bash
uv run python -m unittest discover -s tests -v
uv run python -m mypy token_diet
uv run ruff check .
```

The test suite covers file selection, sensitive-file exclusions, output
self-exclusion, bounded file handling, safe code fences, and Python-only
optimization.
