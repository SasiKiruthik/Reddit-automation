import browser_use
import playwright
from mcp.server.mcpserver import MCPServer

print("Browser Use:", getattr(browser_use, "__version__", "installed"))
print("Playwright:", getattr(playwright, "__version__", "installed"))
print("MCPServer: OK")
