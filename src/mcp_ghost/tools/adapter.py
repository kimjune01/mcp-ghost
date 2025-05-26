# mcp_ghost/tools/adapter.py
"""
Adapters for transforming tool names and definitions for different LLM providers.
"""
import re
from typing import Dict, List

from .models import ToolInfo


class ToolNameAdapter:
    """Handles adaptation between provider-compatible tool names and MCP original names."""
    
    @staticmethod
    def to_openai_compatible(namespace: str, name: str) -> str:
        """
        Convert MCP tool name to OpenAI-compatible format.
        
        OpenAI requires function names to match: ^[a-zA-Z0-9_-]+$
        """
        # Combine namespace and name with underscore
        combined = f"{namespace}_{name}"
        
        # Sanitize to ensure it matches OpenAI's pattern
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', combined)
        
        # Limit length to 200 characters (reasonable limit for function names)
        if len(sanitized) > 200:
            # Truncate but try to keep both namespace and name parts
            max_namespace = min(len(namespace), 80)
            max_name = 200 - max_namespace - 1  # -1 for underscore
            sanitized = f"{namespace[:max_namespace]}_{name[:max_name]}"
        
        return sanitized
    
    @staticmethod
    def to_anthropic_compatible(namespace: str, name: str) -> str:
        """
        Convert MCP tool name to Anthropic (Claude) compatible format.
        
        Claude is more flexible with tool names than OpenAI.
        """
        return f"{namespace}.{name}"
    
    @staticmethod
    def to_gemini_compatible(namespace: str, name: str) -> str:
        """
        Convert MCP tool name to Gemini compatible format.
        
        Gemini has its own naming requirements.
        """
        # Similar to OpenAI but may have different restrictions
        combined = f"{namespace}_{name}"
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', combined)
        return sanitized
    
    @staticmethod
    def from_openai_compatible(openai_name: str) -> str:
        """Convert OpenAI-compatible name back to MCP format."""
        if "_" in openai_name:
            parts = openai_name.split("_", 1)
            return f"{parts[0]}.{parts[1]}"
        return openai_name
    
    @staticmethod
    def adapt_for_provider(namespace: str, name: str, provider: str) -> str:
        """
        Adapt tool name for specific provider.
        
        Args:
            namespace: MCP namespace
            name: MCP tool name
            provider: Provider name ("openai", "anthropic", "gemini")
            
        Returns:
            Provider-compatible tool name
        """
        provider = provider.lower()
        
        if provider == "openai":
            return ToolNameAdapter.to_openai_compatible(namespace, name)
        elif provider == "anthropic":
            return ToolNameAdapter.to_anthropic_compatible(namespace, name)
        elif provider == "gemini":
            return ToolNameAdapter.to_gemini_compatible(namespace, name)
        else:
            # Default to namespace.name format
            return f"{namespace}.{name}"
    
    @staticmethod
    def build_mapping(tools: List[ToolInfo], provider: str) -> Dict[str, str]:
        """
        Build a mapping between provider-compatible names and original names.
        
        Args:
            tools: List of ToolInfo objects
            provider: Provider name
            
        Returns:
            Dictionary mapping provider names to original names
        """
        mapping = {}
        for tool in tools:
            provider_name = ToolNameAdapter.adapt_for_provider(tool.namespace, tool.name, provider)
            original_name = f"{tool.namespace}.{tool.name}"
            mapping[provider_name] = original_name
        return mapping
    
    @staticmethod
    def adapt_tools(tools: List[Dict], namespace: str, provider: str) -> List[Dict]:
        """
        Adapt a list of tools for a specific provider.
        
        Args:
            tools: List of tool dictionaries from MCP server
            namespace: Namespace to use for tool names
            provider: Provider name ("openai", "anthropic", "gemini")
            
        Returns:
            List of adapted tools with provider-compatible names
        """
        adapted_tools = []
        
        for tool in tools:
            # Create provider-compatible tool name
            original_name = tool["name"]
            adapted_name = ToolNameAdapter.adapt_for_provider(namespace, original_name, provider)
            
            # Create adapted tool definition
            adapted_tool = {
                "type": "function",
                "function": {
                    "name": adapted_name,
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {"type": "object", "properties": {}})
                }
            }
            
            # Store original name for mapping back during execution
            adapted_tool["original_name"] = original_name
            adapted_tool["server"] = tool.get("server", "unknown")
            
            adapted_tools.append(adapted_tool)
        
        return adapted_tools