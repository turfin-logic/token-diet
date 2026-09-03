from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from token_diet.cli import generate_context
from token_diet.parser import get_files_to_process, load_gitignore, read_text_file


class ParserTests(unittest.TestCase):
    def test_sensitive_and_gitignored_files_are_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / ".gitignore").write_text(
                "ignored/\ncustom.secret\n!.env\n",
                encoding="utf-8",
            )
            (root / "src").mkdir()
            (root / "src" / "main.py").write_text("print('ok')\n", encoding="utf-8")
            (root / ".env").write_text("API_KEY=not-for-context\n", encoding="utf-8")
            (root / ".env.local").write_text("LOCAL_KEY=not-for-context\n", encoding="utf-8")
            (root / "server.pem").write_text("certificate", encoding="utf-8")
            (root / "ignored").mkdir()
            (root / "ignored" / "skip.py").write_text("print('skip')\n", encoding="utf-8")
            (root / "custom.secret").write_text("skip", encoding="utf-8")

            files = get_files_to_process(root, load_gitignore(root))
            relative_files = {file_path.relative_to(root).as_posix() for file_path in files}

            self.assertIn("src/main.py", relative_files)
            self.assertNotIn(".env", relative_files)
            self.assertNotIn(".env.local", relative_files)
            self.assertNotIn("server.pem", relative_files)
            self.assertNotIn("ignored/skip.py", relative_files)
            self.assertNotIn("custom.secret", relative_files)

    def test_binary_and_oversized_files_are_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            binary_file = root / "binary.txt"
            binary_file.write_bytes(b"valid-prefix\x00invalid")
            oversized_file = root / "large.txt"
            oversized_file.write_text("too large", encoding="utf-8")

            self.assertIsNone(read_text_file(binary_file, max_file_bytes=100))
            self.assertIsNone(read_text_file(oversized_file, max_file_bytes=4))


class ContextGenerationTests(unittest.TestCase):
    def test_output_excludes_itself_and_sensitive_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            output_path = root / "context.md"
            (root / "app.py").write_text(
                '"""Application documentation."""\n# comment\nmessage = "```"\n',
                encoding="utf-8",
            )
            (root / "notes.txt").write_text("literal // do not remove\n", encoding="utf-8")
            (root / ".env").write_text("API_KEY=not-for-context\n", encoding="utf-8")
            output_path.write_text("old generated output", encoding="utf-8")

            summary = generate_context(root, output_path)
            output = output_path.read_text(encoding="utf-8")

            self.assertEqual(summary.files_processed, 2)
            self.assertNotIn("Application documentation", output)
            self.assertNotIn("# comment", output)
            self.assertIn("literal // do not remove", output)
            self.assertNotIn("API_KEY=not-for-context", output)
            self.assertNotIn("## context.md", output)
            self.assertIn("````py", output)

    def test_maximum_file_size_is_reported_as_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            output_path = root / "context.md"
            (root / "large.txt").write_text("x" * 20, encoding="utf-8")

            summary = generate_context(root, output_path, max_file_bytes=10)

            self.assertEqual(summary.files_processed, 0)
            self.assertEqual(summary.files_skipped, 1)


if __name__ == "__main__":
    unittest.main()
