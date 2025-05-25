"""
MCP-Ghost: Intelligent MCP tool orchestration library

Provides Claude Desktop-level tool orchestration capabilities for MCP servers.
"""

from .core import mcp_ghost, MCPGhostConfig, MCPGhostResult

__version__ = "0.1.0"
__all__ = ["mcp_ghost", "MCPGhostConfig", "MCPGhostResult"]