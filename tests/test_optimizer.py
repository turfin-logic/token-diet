from __future__ import annotations

import unittest

from token_diet.optimizer import optimize_source, strip_docstrings_and_comments


class OptimizerTests(unittest.TestCase):
    def test_python_docstrings_and_comments_are_removed_from_valid_source(self) -> None:
        source = '''"""Module documentation."""
# module comment
class Example:
    """Class documentation."""

    async def run(self) -> str:
        """Method documentation."""
        # implementation detail
        return "value # retained in a string"
'''

        optimized = strip_docstrings_and_comments(source)

        self.assertNotIn("Module documentation", optimized)
        self.assertNotIn("Class documentation", optimized)
        self.assertNotIn("Method documentation", optimized)
        self.assertIn("value # retained in a string", optimized)
        compile(optimized, "optimized.py", "exec")

    def test_non_python_files_are_preserved_verbatim(self) -> None:
        source = "const endpoint = 'https://example.test//keep';\n/* keep this */\n"

        self.assertEqual(optimize_source(source, ".ts"), source)

    def test_invalid_python_is_preserved_instead_of_regex_rewritten(self) -> None:
        source = "const endpoint = 'https://example.test//keep';\n"

        self.assertEqual(optimize_source(source, ".py"), source)


if __name__ == "__main__":
    unittest.main()
