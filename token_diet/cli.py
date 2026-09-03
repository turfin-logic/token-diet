"""Command-line interface for creating a compact source context file."""

from __future__ import annotations

import argparse
import re
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .optimizer import count_tokens, optimize_source
from .parser import get_files_to_process, load_gitignore, read_text_file

console = Console()
DEFAULT_MAX_FILE_BYTES = 1_000_000


@dataclass(frozen=True)
class ContextSummary:
    """Facts about one generated context file."""

    files_processed: int
    files_skipped: int
    original_tokens: int
    optimized_tokens: int
    elapsed_seconds: float


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def _code_fence(content: str) -> str:
    """Choose a Markdown code fence that cannot be closed by file content."""

    longest_run = max((len(run) for run in re.findall(r"`+", content)), default=0)
    return "`" * max(3, longest_run + 1)


def _language_for(path: Path) -> str:
    return path.suffix.removeprefix(".") or "text"


def _write_context_atomically(output_path: Path, content: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=output_path.parent,
        delete=False,
        prefix=f".{output_path.name}.",
        suffix=".tmp",
    ) as temporary_file:
        temporary_file.write(content)
        temporary_path = Path(temporary_file.name)

    try:
        temporary_path.replace(output_path)
    except OSError:
        temporary_path.unlink(missing_ok=True)
        raise


def generate_context(
    repo_path: str | Path,
    output_path: str | Path,
    *,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
) -> ContextSummary:
    """Generate a context document and return its measured summary.

    The output path is always excluded from the input walk, including when it
    lives inside the analyzed repository. Files are written atomically so an
    interrupted run cannot leave a partial context document behind.
    """

    root = Path(repo_path).resolve()
    if not root.is_dir():
        raise ValueError(f"repository path is not a directory: {root}")
    if max_file_bytes <= 0:
        raise ValueError("max_file_bytes must be greater than zero")

    destination = Path(output_path).resolve()
    spec = load_gitignore(root)
    files = get_files_to_process(root, spec, excluded_paths=[destination])
    start_time = time.perf_counter()
    original_tokens = 0
    optimized_tokens = 0
    files_processed = 0
    files_skipped = 0
    sections = [f"# Context Diet Output for {root.name}\n\n"]

    for file_path in files:
        content = read_text_file(file_path, max_file_bytes)
        if content is None:
            files_skipped += 1
            continue

        optimized_content = optimize_source(content, file_path.suffix)
        original_tokens += count_tokens(content)
        optimized_tokens += count_tokens(optimized_content)
        relative_path = file_path.relative_to(root).as_posix()
        fence = _code_fence(optimized_content)
        sections.extend(
            [
                f"## {relative_path}\n",
                f"{fence}{_language_for(file_path)}\n",
                optimized_content,
                "\n" if not optimized_content.endswith("\n") else "",
                f"{fence}\n\n",
            ]
        )
        files_processed += 1

    _write_context_atomically(destination, "".join(sections))
    return ContextSummary(
        files_processed=files_processed,
        files_skipped=files_skipped,
        original_tokens=original_tokens,
        optimized_tokens=optimized_tokens,
        elapsed_seconds=time.perf_counter() - start_time,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser without causing filesystem side effects."""

    parser = argparse.ArgumentParser(
        description="Create a token-counted context file from a source tree."
    )
    parser.add_argument(
        "--path",
        default=".",
        help="Source directory to analyze (default: current directory)",
    )
    parser.add_argument(
        "--output",
        default="context.md",
        help="Context file to write (default: context.md in the current directory)",
    )
    parser.add_argument(
        "--max-file-bytes",
        type=_positive_int,
        default=DEFAULT_MAX_FILE_BYTES,
        help=f"Skip files larger than this many bytes (default: {DEFAULT_MAX_FILE_BYTES:,})",
    )
    return parser


def _print_summary(summary: ContextSummary, output_path: Path) -> None:
    savings = (
        0
        if summary.original_tokens == 0
        else (summary.original_tokens - summary.optimized_tokens) / summary.original_tokens * 100
    )
    table = Table(title="Token Savings Summary")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")
    table.add_row("Files Processed", str(summary.files_processed))
    table.add_row("Files Skipped", str(summary.files_skipped))
    table.add_row("Original Tokens", f"{summary.original_tokens:,}")
    table.add_row("Optimized Tokens", f"{summary.optimized_tokens:,}")
    table.add_row(
        "Tokens Saved",
        "[bold green]"
        f"{summary.original_tokens - summary.optimized_tokens:,} ({savings:.1f}%)"
        "[/bold green]",
    )
    table.add_row("Execution Time", f"{summary.elapsed_seconds:.2f}s")
    console.print(table)
    console.print(f"[bold green]Saved compressed context to {output_path}[/bold green]")


def main(argv: list[str] | None = None) -> None:
    """Run the command-line interface."""

    args = build_parser().parse_args(argv)
    repo_path = Path(args.path).resolve()
    output_path = Path(args.output).resolve()
    console.print(f"[bold blue]Starting Token-Diet on {repo_path}[/bold blue]")
    try:
        summary = generate_context(repo_path, output_path, max_file_bytes=args.max_file_bytes)
    except (OSError, ValueError) as error:
        raise SystemExit(f"token-diet: {error}") from error
    _print_summary(summary, output_path)


if __name__ == "__main__":
    main()
