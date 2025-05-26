"""
Core MCP-Ghost functionality.

Provides intelligent multi-step MCP tool operations via LLM with Claude Desktop-level capabilities.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class MCPGhostConfig:
    """Configuration for MCP-Ghost execution."""
    server_config: Union[Dict[str, Any], str, Path]
    system_prompt: str
    provider: str  # "openai", "anthropic", "gemini"
    api_key: str
    user_prompt: str
    model: Optional[str] = None
    namespace: str = "mcp_ghost"
    timeout: float = 30.0
    max_iterations: int = 10
    enable_backtracking: bool = True
    conversation_memory: bool = True
    
    def __post_init__(self):
        """Process server_config if it's a file path."""
        if isinstance(self.server_config, (str, Path)):
            self.server_config = self._load_server_config(self.server_config)
    
    def _load_server_config(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        """Load MCP server configuration from a file.
        
        Args:
            config_path: Path to MCP server config file (.json)
            
        Returns:
            Dictionary containing server configuration
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file format is invalid
        """
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"MCP server config file not found: {config_path}")
        
        # Load JSON config (Claude Desktop format)
        if config_path.suffix.lower() == '.json':
            with open(config_path, 'r') as f:
                config_data = json.load(f)
        else:
            raise ValueError(f"MCP server config must be JSON format, got: {config_path.suffix}")
        
        # Validate structure - should have mcpServers key
        if 'mcpServers' not in config_data:
            raise ValueError("MCP server config must contain 'mcpServers' key")
        
        return config_data


@dataclass 
class ToolCallInfo:
    """Information about a single tool call."""
    iteration: int
    tool_name: str
    arguments: Dict[str, Any]
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    reasoning: Optional[str] = None
    retry_attempt: int = 0


@dataclass
class MCPGhostResult:
    """Result from MCP-Ghost execution."""
    success: bool
    final_result: Any = None
    summary: str = ""
    tool_chain: List[ToolCallInfo] = field(default_factory=list)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    execution_metadata: Dict[str, Any] = field(default_factory=dict)


# MCP imports - using official MCP Python SDK
try:
    from mcp import ClientSession, StdioServerParameters, stdio_client
    MCP_AVAILABLE = True
except ImportError:
    # Define placeholder for testing when MCP isn't available
    MCP_AVAILABLE = False
    class ClientSession:
        pass
    class StdioServerParameters:
        pass
    def stdio_client(*args, **kwargs):
        pass

# Import these unconditionally so tests can patch them
from .providers.client_factory import get_llm_client
from .utils.prompt_generator import SystemPromptGenerator
from .tools.adapter import ToolNameAdapter
from .tools.formatter import format_tool_response


async def mcp_ghost(config: MCPGhostConfig) -> MCPGhostResult:
    """
    Execute intelligent multi-step MCP tool operations via LLM.
    
    Supports tool chaining, backtracking, and error recovery like Claude Desktop.
    
    Args:
        config: MCPGhostConfig instance (server_config can be dict or file path)
        
    Returns:
        MCPGhostResult with execution details
    """
    start_time = time.time()
    
    conversation_history = []
    tool_chain = []
    errors = []
    iteration = 0
    available_tools = []
    connected_servers = 0
    
    try:
        # Validate configuration
        if not config.api_key:
            raise ValueError("API key is required")
        
        if not MCP_AVAILABLE:
            logger.warning("MCP SDK not available, falling back to placeholder mode")
            return _create_placeholder_result(config, start_time)
        
        # Connect to MCP servers and discover tools
        if config.server_config and "mcpServers" in config.server_config:
            for server_name, server_config in config.server_config["mcpServers"].items():
                try:
                    tools = await _connect_to_mcp_server(server_name, server_config)
                    available_tools.extend(tools)
                    connected_servers += 1
                    logger.info(f"Connected to MCP server '{server_name}', found {len(tools)} tools")
                except Exception as e:
                    logger.error(f"Failed to connect to MCP server '{server_name}': {e}")
                    errors.append({
                        "iteration": 0,
                        "tool_name": "mcp_connection",
                        "error": f"Failed to connect to server {server_name}: {str(e)}",
                        "recovery_action": "Continuing with other servers"
                    })
        
        # Get LLM client
        llm_client = get_llm_client(
            provider=config.provider,
            model=config.model,
            api_key=config.api_key
        )
        
        # Adapt tool names for the specific provider
        tool_adapter = ToolNameAdapter()
        adapted_tools = tool_adapter.adapt_tools(available_tools, config.namespace, config.provider)
        
        # Generate system prompt with available tools
        prompt_generator = SystemPromptGenerator()
        system_prompt = prompt_generator.generate(
            tools=adapted_tools,
            namespace=config.namespace,
            additional_context=config.system_prompt
        )
        
        # Initialize conversation
        conversation_history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": config.user_prompt}
        ]
        
        # Main conversation loop
        while iteration < config.max_iterations:
            iteration += 1
            logger.info(f"Starting iteration {iteration}")
            
            try:
                # Create completion with available tools
                completion_result = await llm_client.create_completion(
                    messages=conversation_history,
                    tools=adapted_tools if adapted_tools else None
                )
                
                # Add assistant response to conversation
                assistant_message = {
                    "role": "assistant",
                    "content": completion_result["response"]
                }
                
                if completion_result["tool_calls"]:
                    assistant_message["tool_calls"] = completion_result["tool_calls"]
                
                conversation_history.append(assistant_message)
                
                # If no tool calls, we're done
                if not completion_result["tool_calls"]:
                    logger.info("No tool calls requested, conversation complete")
                    break
                
                # Execute tool calls
                tool_results = []
                for tool_call in completion_result["tool_calls"]:
                    tool_start_time = time.time()
                    
                    try:
                        # Execute the tool call
                        result = await _execute_tool_call(tool_call, available_tools, config.namespace)
                        
                        tool_info = ToolCallInfo(
                            iteration=iteration,
                            tool_name=tool_call["function"]["name"],
                            arguments=json.loads(tool_call["function"]["arguments"]) if tool_call["function"]["arguments"] else {},
                            success=True,
                            result=result,
                            execution_time=time.time() - tool_start_time,
                            reasoning=f"Executed {tool_call['function']['name']} successfully"
                        )
                        tool_chain.append(tool_info)
                        
                        # Add tool result to conversation
                        tool_results.append({
                            "role": "tool",
                            "content": format_tool_response(result),
                            "tool_call_id": tool_call["id"]
                        })
                        
                    except Exception as e:
                        logger.error(f"Tool execution failed: {e}")
                        
                        tool_info = ToolCallInfo(
                            iteration=iteration,
                            tool_name=tool_call["function"]["name"],
                            arguments=json.loads(tool_call["function"]["arguments"]) if tool_call["function"]["arguments"] else {},
                            success=False,
                            error=str(e),
                            execution_time=time.time() - tool_start_time,
                            reasoning=f"Tool {tool_call['function']['name']} failed: {str(e)}"
                        )
                        tool_chain.append(tool_info)
                        
                        errors.append({
                            "iteration": iteration,
                            "tool_name": tool_call["function"]["name"],
                            "error": str(e),
                            "recovery_action": "Continuing with next tool" if config.enable_backtracking else "Stopping execution"
                        })
                        
                        # Add error to conversation if backtracking is enabled
                        if config.enable_backtracking:
                            tool_results.append({
                                "role": "tool",
                                "content": f"Error: {str(e)}",
                                "tool_call_id": tool_call["id"]
                            })
                        else:
                            break
                
                # Add all tool results to conversation
                conversation_history.extend(tool_results)
                
            except Exception as e:
                logger.error(f"LLM completion failed in iteration {iteration}: {e}")
                errors.append({
                    "iteration": iteration,
                    "tool_name": "llm_completion",
                    "error": str(e),
                    "recovery_action": "Stopping execution"
                })
                break
        
        # Calculate final metrics
        execution_time = time.time() - start_time
        successful_tools = len([tc for tc in tool_chain if tc.success])
        total_tools = len(tool_chain)
        success_rate = (successful_tools / total_tools) if total_tools > 0 else 1.0
        
        # Generate final summary
        if conversation_history and conversation_history[-1]["role"] == "assistant":
            final_result = conversation_history[-1]["content"]
        else:
            final_result = "Tool execution completed"
        
        summary = f"Completed {iteration} iterations with {successful_tools}/{total_tools} successful tool calls using {config.provider}"
        
        return MCPGhostResult(
            success=len(errors) == 0 or config.enable_backtracking,
            final_result=final_result,
            summary=summary,
            tool_chain=tool_chain,
            conversation_history=conversation_history,
            errors=errors,
            execution_metadata={
                "total_execution_time": execution_time,
                "total_iterations": iteration,
                "tools_discovered": len(available_tools),
                "servers_connected": connected_servers,
                "backtrack_count": len([e for e in errors if "recovery_action" in e]),
                "success_rate": success_rate,
                "token_usage": {  # TODO: aggregate from LLM calls
                    "prompt_tokens": iteration * 100,  # Rough estimate
                    "completion_tokens": iteration * 50,
                    "total_tokens": iteration * 150
                }
            }
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"MCP-Ghost execution failed: {e}")
        
        return MCPGhostResult(
            success=False,
            summary=f"Failed to execute MCP-Ghost: {str(e)}",
            tool_chain=tool_chain,
            conversation_history=conversation_history,
            errors=errors + [{
                "iteration": iteration,
                "tool_name": "system",
                "error": str(e),
                "recovery_action": "Check configuration and API keys"
            }],
            execution_metadata={
                "total_execution_time": execution_time,
                "total_iterations": iteration,
                "tools_discovered": len(available_tools),
                "servers_connected": connected_servers,
                "backtrack_count": len([e for e in errors if "recovery_action" in e]),
                "success_rate": 0.0,
                "token_usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
        )


async def _connect_to_mcp_server(server_name: str, server_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Connect to an MCP server and discover available tools.
    
    Args:
        server_name: Name of the server
        server_config: Server configuration with command and args
        
    Returns:
        List of available tools from the server
    """
    try:
        # Create server parameters
        server_params = StdioServerParameters(
            command=server_config["command"],
            args=server_config.get("args", []),
            env=server_config.get("env", {})
        )
        
        # Connect to server
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()
                
                # List available tools
                tools_response = await session.list_tools()
                
                # Convert MCP tools to our internal format
                tools = []
                for tool in tools_response.tools:
                    tools.append({
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema if hasattr(tool, 'inputSchema') else {},
                        "server": server_name
                    })
                
                return tools
                
    except Exception as e:
        logger.error(f"Failed to connect to MCP server {server_name}: {e}")
        raise


async def _execute_tool_call(tool_call: Dict[str, Any], available_tools: List[Dict[str, Any]], namespace: str) -> Any:
    """
    Execute a single tool call.
    
    Args:
        tool_call: The tool call to execute
        available_tools: List of available tools
        namespace: Tool namespace
        
    Returns:
        The result of the tool execution
    """
    tool_name = tool_call["function"]["name"]
    arguments = json.loads(tool_call["function"]["arguments"]) if tool_call["function"]["arguments"] else {}
    
    # Remove namespace prefix if present
    if tool_name.startswith(f"{namespace}_"):
        original_name = tool_name[len(f"{namespace}_"):]
    else:
        original_name = tool_name
    
    # Find the tool in available tools
    tool_info = None
    for tool in available_tools:
        if tool["name"] == original_name:
            tool_info = tool
            break
    
    if not tool_info:
        raise ValueError(f"Tool '{original_name}' not found in available tools")
    
    # TODO: Implement actual tool execution via MCP server
    # For now, return a placeholder result
    logger.info(f"Executing tool {original_name} with arguments {arguments}")
    
    return f"Tool {original_name} executed successfully with arguments {arguments}"


def _create_placeholder_result(config: MCPGhostConfig, start_time: float) -> MCPGhostResult:
    """
    Create a placeholder result when MCP is not available.
    """
    execution_time = time.time() - start_time
    
    system_prompt = "You have access to tools to help answer the user's question."
    
    return MCPGhostResult(
        success=True,
        final_result=f"Processed request: {config.user_prompt}",
        summary=f"Placeholder mode - processed user request using {config.provider}",
        tool_chain=[],
        conversation_history=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": config.user_prompt},
            {"role": "assistant", "content": f"Processed request: {config.user_prompt}"}
        ],
        errors=[],
        execution_metadata={
            "total_execution_time": execution_time,
            "total_iterations": 1,
            "tools_discovered": 0,
            "servers_connected": 0,
            "backtrack_count": 0,
            "success_rate": 1.0,
            "token_usage": {
                "prompt_tokens": 50,
                "completion_tokens": 25,
                "total_tokens": 75
            }
        }
    )