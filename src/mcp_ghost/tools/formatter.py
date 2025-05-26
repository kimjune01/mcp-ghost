# mcp_ghost/tools/formatter.py
"""Tool formatting utilities for different providers."""
from typing import List, Dict, Any, Optional
import json

from .models import ToolInfo, ToolCallResult


def format_tool_for_openai(tool: ToolInfo) -> Dict[str, Any]:
    """Format a tool for OpenAI function calling."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.parameters or {"type": "object", "properties": {}}
        }
    }


def _serialize_for_json(obj):
    """Helper to handle non-serializable objects."""
    if hasattr(obj, '__dict__'):
        return str(obj)
    elif hasattr(obj, '__str__'):
        return str(obj)
    else:
        return repr(obj)


def format_tool_response(response_content: Any) -> str:
    """
    Format tool response content for LLM consumption.
    
    Args:
        response_content: Raw response from tool execution
        
    Returns:
        Formatted string suitable for LLM processing
    """
    # Handle list of dictionaries (likely structured data like SQL results)
    if isinstance(response_content, list) and response_content and isinstance(response_content[0], dict):
        # Treat as text records only if every item has type == "text"
        if all(isinstance(item, dict) and item.get("type") == "text" for item in response_content):
            return "\n".join(item.get("text", "") for item in response_content)
        # This could be data records (like SQL results)
        try:
            return json.dumps(response_content, indent=2, default=_serialize_for_json, ensure_ascii=False)
        except Exception:
            return str(response_content)
    elif isinstance(response_content, dict):
        # Single dictionary - return as JSON
        try:
            return json.dumps(response_content, indent=2, default=_serialize_for_json, ensure_ascii=False)
        except Exception:
            return str(response_content)
    else:
        # Default case - convert to string
        return str(response_content)


def format_tool_call_result(result: ToolCallResult) -> str:
    """Format tool call result for LLM consumption."""
    if result.success:
        return format_tool_response(result.result)
    else:
        return f"Error: {result.error or 'Unknown error'}"


def format_tools_for_provider(tools: List[ToolInfo], provider: str) -> List[Dict[str, Any]]:
    """Format tools for specific provider."""
    provider = provider.lower()
    
    if provider == "openai":
        return [format_tool_for_openai(tool) for tool in tools]
    elif provider in ["anthropic", "gemini"]:
        # Both use similar OpenAI-style format
        return [format_tool_for_openai(tool) for tool in tools]
    else:
        # Default to OpenAI format
        return [format_tool_for_openai(tool) for tool in tools]