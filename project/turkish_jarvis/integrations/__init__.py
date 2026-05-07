"""Integrations package for Turkish Jarvis.

This package contains third-party service integrations:
- MCP Client (Model Context Protocol)
- Home Assistant
- Browser Automation
"""

__version__ = "2.0.0"

__all__ = [
    "MCPClient",
    "HomeAssistantClient",
    "BrowserClient",
]

try:
    from .mcp_client import MCPClient
except ImportError:  # pragma: no cover
    MCPClient = None  # type: ignore[misc, assignment]

try:
    from .home_assistant import HomeAssistantClient
except ImportError:  # pragma: no cover
    HomeAssistantClient = None  # type: ignore[misc, assignment]

try:
    from .browser import BrowserClient
except ImportError:  # pragma: no cover
    BrowserClient = None  # type: ignore[misc, assignment]
