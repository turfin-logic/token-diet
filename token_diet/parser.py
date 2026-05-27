import os
import pathspec

DEFAULT_IGNORES = [
    ".git", ".svn", ".hg",
    "node_modules", "venv", ".venv", "env",
    "__pycache__", ".pytest_cache", ".mypy_cache",
    "build", "dist",
    "*.lock", "package-lock.json", "yarn.lock", "poetry.lock", "Pipfile.lock",
    "*.jpg", "*.jpeg", "*.png", "*.gif", "*.svg", "*.ico", "*.webp",
    "*.mp3", "*.mp4", "*.wav", "*.avi", "*.mkv",
    "*.pdf", "*.doc", "*.docx", "*.xls", "*.xlsx",
    "*.pyc", "*.pyo", "*.pyd",
    "*.so", "*.dylib", "*.dll", "*.exe", "*.bin",
    ".DS_Store", "Thumbs.db"
]

def load_gitignore(repo_path: str) -> pathspec.PathSpec:
    """Loads .gitignore patterns into a PathSpec."""
    patterns = list(DEFAULT_IGNORES)
    gitignore_path = os.path.join(repo_path, ".gitignore")
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            patterns.extend(f.readlines())
    return pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, patterns)

def get_files_to_process(repo_path: str, spec: pathspec.PathSpec) -> list[str]:
    """Returns a list of absolute file paths to process, respecting ignore rules."""
    files_to_process = []
    
    for root, dirs, files in os.walk(repo_path):
        # We need to compute relative path to match against gitignore
        rel_root = os.path.relpath(root, repo_path)
        if rel_root == ".":
            rel_root = ""
            
        # Filter directories in-place to avoid traversing ignored dirs
        dirs[:] = [d for d in dirs if not spec.match_file(os.path.join(rel_root, d) + "/")]
        
        for file in files:
            rel_file = os.path.join(rel_root, file).replace("\\", "/")
            if not spec.match_file(rel_file):
                files_to_process.append(os.path.join(root, file))
                
    return files_to_process
