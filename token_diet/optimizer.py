import ast
import re

def strip_docstrings_and_comments(source_code: str) -> str:
    """Removes docstrings and comments from Python code using AST and regex."""
    try:
        # For Python files, use AST to reliably remove docstrings
        tree = ast.parse(source_code)
        
        # A simple NodeTransformer to remove docstrings
        class DocstringRemover(ast.NodeTransformer):
            def visit_FunctionDef(self, node):
                self.generic_visit(node)
                if ast.get_docstring(node):
                    node.body = node.body[1:] if len(node.body) > 1 else [ast.Pass()]
                return node
                
            def visit_ClassDef(self, node):
                self.generic_visit(node)
                if ast.get_docstring(node):
                    node.body = node.body[1:] if len(node.body) > 1 else [ast.Pass()]
                return node
                
            def visit_Module(self, node):
                self.generic_visit(node)
                if ast.get_docstring(node):
                    node.body = node.body[1:] if len(node.body) > 1 else [ast.Pass()]
                return node

        tree = DocstringRemover().visit(tree)
        # Using ast.unparse requires Python 3.9+
        clean_code = ast.unparse(tree)
        
        # Fallback regex for remaining # comments
        clean_code = re.sub(r'(?m)^\s*#.*$', '', clean_code)
        # Remove empty lines
        clean_code = re.sub(r'\n\s*\n', '\n', clean_code)
        return clean_code
        
    except SyntaxError:
        # If it's not valid Python (or JS/TS etc), just do basic regex compression
        clean_code = re.sub(r'(?m)^\s*//.*$', '', source_code)  # JS comments
        clean_code = re.sub(r'/\*[\s\S]*?\*/', '', clean_code) # Block comments
        clean_code = re.sub(r'(?m)^\s*#.*$', '', clean_code)   # Python/Bash comments
        clean_code = re.sub(r'\n\s*\n', '\n', clean_code)
        return clean_code

def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """Counts tokens using tiktoken (used by OpenAI models)."""
    try:
        import tiktoken
        encoding = tiktoken.get_encoding(model)
        return len(encoding.encode(text))
    except ImportError:
        return len(text) // 4  # Rough fallback
