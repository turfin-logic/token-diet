# Token-Diet 🥬

> A hyper-optimized codebase summarizer built specifically for LLM context windows.

LLMs have limited context windows and charge by the token. When passing your repository to Claude or GPT, you waste thousands of tokens on boilerplate, whitespaces, comments, large lockfiles, and meaningless data.

`token-diet` compresses your entire repository into a highly optimized, minified `context.md` file. It uses Python's AST (Abstract Syntax Tree) to strip comments and docstrings intelligently, and respects your `.gitignore` to skip large junk files.

## Features
- **Semantic Minification:** Removes comments, docstrings, and empty lines automatically using AST.
- **Smart Ignore:** Automatically respects `.gitignore` and ignores `node_modules`, `venv`, `.git`, `.lock` files, and media.
- **Token Counter:** Estimates the token count of the final output file before sending it to OpenAI/Anthropic.

## Installation

You can install it directly from the source using `uv` or `pip`:

```bash
uv add token-diet
```

## Usage

Simply point it at your repository directory:

```bash
python -m token_diet.cli --path /path/to/your/repo --output compressed_context.md
```

### Example Output:

```
Starting Token-Diet on /path/to/repo
Found 45 files to process after applying ignore rules.

     Token Savings Summary
+------------------------------+
| Metric           | Value     |
|------------------+-----------|
| Files Processed  | 45        |
| Original Tokens  | 145,230   |
| Optimized Tokens | 87,450    |
| Tokens Saved     | 57,780 (39.8%) |
| Execution Time   | 0.42s     |
+------------------------------+
Saved compressed context to compressed_context.md 🎉
```

## Why?
Reducing your token footprint by 40% means:
1. Faster API responses.
2. 40% cheaper API costs.
3. Less LLM hallucination because you removed the noise.

---
Built with ❤️ for the AI Engineering community.
