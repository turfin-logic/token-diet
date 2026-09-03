"""Filesystem selection and safe text reading for Token Diet."""

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path

import pathspec

# These patterns reduce the chance of accidentally placing credentials or
# generated/binary material in a context file. They are defense in depth, not
# a substitute for reviewing generated output before sharing it.
DEFAULT_IGNORES = (
    ".git/",
    ".svn/",
    ".hg/",
    "node_modules/",
    "venv/",
    ".venv/",
    "env/",
    "__pycache__/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    "build/",
    "dist/",
    ".uv-cache/",
    "*.lock",
    "package-lock.json",
    "yarn.lock",
    "poetry.lock",
    "Pipfile.lock",
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    "secret.*",
    "secrets.*",
    "service-account*.json",
    "*.jpg",
    "*.jpeg",
    "*.png",
    "*.gif",
    "*.svg",
    "*.ico",
    "*.webp",
    "*.mp3",
    "*.mp4",
    "*.wav",
    "*.avi",
    "*.mkv",
    "*.pdf",
    "*.doc",
    "*.docx",
    "*.xls",
    "*.xlsx",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.so",
    "*.dylib",
    "*.dll",
    "*.exe",
    "*.bin",
    ".DS_Store",
    "Thumbs.db",
)


def load_gitignore(repo_path: str | Path) -> pathspec.GitIgnoreSpec:
    """Combine .gitignore rules with non-overridable built-in exclusions."""

    root = Path(repo_path)
    patterns: list[str] = []
    gitignore_path = root / ".gitignore"
    if gitignore_path.is_file():
        patterns.extend(gitignore_path.read_text(encoding="utf-8").splitlines())
    # Keep safety exclusions last so an accidental `!.env` in a repository's
    # .gitignore cannot make credentials part of an exported context file.
    patterns.extend(DEFAULT_IGNORES)
    return pathspec.GitIgnoreSpec.from_lines(patterns)


def get_files_to_process(
    repo_path: str | Path,
    spec: pathspec.GitIgnoreSpec,
    *,
    excluded_paths: Iterable[str | Path] = (),
) -> list[Path]:
    """Return sorted regular files that are not ignored or explicitly excluded."""

    root = Path(repo_path).resolve()
    excluded = {Path(path).resolve() for path in excluded_paths}
    files_to_process: list[Path] = []

    for directory, directories, filenames in os.walk(root):
        directory_path = Path(directory)
        relative_root = directory_path.relative_to(root)
        prefix = "" if relative_root == Path(".") else f"{relative_root.as_posix()}/"

        directories[:] = sorted(
            directory_name
            for directory_name in directories
            if not spec.match_file(f"{prefix}{directory_name}/")
        )

        for filename in sorted(filenames):
            file_path = directory_path / filename
            relative_file = f"{prefix}{filename}"
            if (
                file_path.is_file()
                and not file_path.is_symlink()
                and file_path.resolve() not in excluded
                and not spec.match_file(relative_file)
            ):
                files_to_process.append(file_path)

    return files_to_process


def read_text_file(file_path: Path, max_file_bytes: int) -> str | None:
    """Read a bounded UTF-8 text file, returning ``None`` for skipped files."""

    try:
        if file_path.stat().st_size > max_file_bytes:
            return None
        content = file_path.read_bytes()
    except OSError:
        return None

    if b"\x00" in content:
        return None

    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return None
