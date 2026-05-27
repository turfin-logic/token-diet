# Context Diet Output for mcp-quickstart-python

## README.md
```md

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
The absolute fastest way to build a **Model Context Protocol (MCP)** server in Python. Zero bloated dependencies, async-first, and ready to connect with Claude, Gemini, or any MCP-compatible agent.
The internet is full of complex MCP SDKs that take hours to understand. This repository provides a single-file, lightweight `MCPServer` class that you can drop into any project. It handles stdio communication, JSON parsing, and asynchronous tool routing perfectly.
1. **Clone the repo**
   ```bash
   git clone https://github.com/turfin-logic/mcp-quickstart-python.git
   cd mcp-quickstart-python
   ```
2. **Add your tools in `server.py`**
   ```python
   @app.tool(name="calculate_revenue", description="Calculates startup revenue.")
   async def calculate_revenue(users: int, price: float):
       return {"revenue": users * price}
   ```
3. **Run your MCP server**
   ```bash
   python server.py
   ```
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
Created by [turfin-logic](https://github.com/turfin-logic) - Building the future of agentic AI.
```

## server.py
```py
import asyncio
import json
import sys
from typing import Dict, Any, Callable
class MCPServer:
    def __init__(self, name: str):
        self.name = name
        self.tools: Dict[str, Callable] = {}
        self.running = False
    def tool(self, name: str, description: str):
        def decorator(func):
            self.tools[name] = {'func': func, 'description': description, 'name': name}
            return func
        return decorator
    async def _handle_request(self, req: str):
        try:
            data = json.loads(req)
            action = data.get('action')
            if action == 'list_tools':
                return {'tools': [{'name': k, 'description': v['description']} for k, v in self.tools.items()]}
            if action == 'call_tool':
                tool_name = data.get('tool')
                kwargs = data.get('args', {})
                if tool_name in self.tools:
                    result = await self.tools[tool_name]['func'](**kwargs)
                    return {'status': 'success', 'result': result}
                return {'status': 'error', 'message': f"Tool '{tool_name}' not found."}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    async def serve(self):
        """Starts the stdio JSON-RPC loop."""
        self.running = True
        print(f'[{self.name}] MCP Server started.', file=sys.stderr)
        while self.running:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            response = await self._handle_request(line.strip())
            print(json.dumps(response), flush=True)
if __name__ == '__main__':
    app = MCPServer('QuickstartMCP')
    @app.tool(name='hello_world', description='Returns a simple greeting.')
    async def hello_world(name: str='World'):
        return f'Hello, {name}! This is running via MCP.'
    asyncio.run(app.serve())
```

