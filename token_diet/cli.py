import argparse
import os
import time
from rich.console import Console
from rich.table import Table

from .parser import load_gitignore, get_files_to_process
from .optimizer import strip_docstrings_and_comments, count_tokens

console = Console()

def main():
    parser = argparse.ArgumentParser(description="Token-Diet: Compress your codebase for LLM Context Windows.")
    parser.add_argument("--path", type=str, default=".", help="Path to the repository to compress")
    parser.add_argument("--output", type=str, default="context.md", help="Output file name")
    args = parser.parse_args()

    repo_path = os.path.abspath(args.path)
    output_path = os.path.abspath(args.output)
    
    console.print(f"[bold blue]Starting Token-Diet on {repo_path}[/bold blue]")
    
    start_time = time.time()
    
    spec = load_gitignore(repo_path)
    files = get_files_to_process(repo_path, spec)
    
    console.print(f"Found [bold green]{len(files)}[/bold green] files to process after applying ignore rules.")
    
    original_tokens = 0
    optimized_tokens = 0
    
    with open(output_path, "w", encoding="utf-8") as out_f:
        out_f.write(f"# Context Diet Output for {os.path.basename(repo_path)}\n\n")
        
        for file_path in files:
            rel_path = os.path.relpath(file_path, repo_path).replace("\\", "/")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                continue # Skip binary files that slipped through
                
            orig_toks = count_tokens(content)
            original_tokens += orig_toks
            
            # Optimize
            opt_content = strip_docstrings_and_comments(content)
            opt_toks = count_tokens(opt_content)
            optimized_tokens += opt_toks
            
            # Write to output
            out_f.write(f"## {rel_path}\n")
            out_f.write(f"```{rel_path.split('.')[-1] if '.' in rel_path else 'text'}\n")
            out_f.write(opt_content)
            if not opt_content.endswith("\n"):
                out_f.write("\n")
            out_f.write("```\n\n")
            
    end_time = time.time()
    
    savings = 0 if original_tokens == 0 else (original_tokens - optimized_tokens) / original_tokens * 100
    
    table = Table(title="Token Savings Summary")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")
    
    table.add_row("Files Processed", str(len(files)))
    table.add_row("Original Tokens", f"{original_tokens:,}")
    table.add_row("Optimized Tokens", f"{optimized_tokens:,}")
    table.add_row("Tokens Saved", f"[bold green]{original_tokens - optimized_tokens:,} ({savings:.1f}%)[/bold green]")
    table.add_row("Execution Time", f"{end_time - start_time:.2f}s")
    
    console.print(table)
    console.print(f"[bold green]Saved compressed context to {output_path}[/bold green]")

if __name__ == "__main__":
    main()
