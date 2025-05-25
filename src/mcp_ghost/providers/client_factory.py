# mcp_ghost/providers/client_factory.py
"""
LLM client factory for MCP-Ghost.
"""
from __future__ import annotations

from typing import Optional, Dict, Any

from .base import BaseLLMClient

# Import providers conditionally
try:
    from .openai_client import OpenAILLMClient
except ImportError:
    OpenAILLMClient = None

try:
    from .anthropic_client import AnthropicLLMClient
except ImportError:
    AnthropicLLMClient = None

try:
    from .gemini_client import GeminiLLMClient
except ImportError:
    GeminiLLMClient = None


def get_llm_client(
    provider: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs: Any
) -> BaseLLMClient:
    """
    Create an LLM client for the specified provider.
    
    Args:
        provider: Provider name ("openai", "anthropic", "gemini")
        model: Model name (provider-specific default if None)
        api_key: API key (env var used if None)
        **kwargs: Additional provider-specific parameters
        
    Returns:
        BaseLLMClient instance
        
    Raises:
        ValueError: If provider is not supported
    """
    provider = provider.lower()
    
    if provider == "openai":
        if OpenAILLMClient is None:
            raise ImportError(f"OpenAI client not available. Install required dependencies for {provider}")
        return OpenAILLMClient(
            model=model or "gpt-4o-mini",
            api_key=api_key,
            **kwargs
        )
    elif provider == "anthropic":
        if AnthropicLLMClient is None:
            raise ImportError(f"Anthropic client not available. Install required dependencies for {provider}")
        return AnthropicLLMClient(
            model=model or "claude-3-sonnet-20250219",
            api_key=api_key,
            **kwargs
        )
    elif provider == "gemini":
        if GeminiLLMClient is None:
            raise ImportError(f"Gemini client not available. Install required dependencies for {provider}")
        return GeminiLLMClient(
            model=model or "gemini-2.0-flash",
            api_key=api_key,
            **kwargs
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}. Supported: openai, anthropic, gemini")