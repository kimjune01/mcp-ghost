#!/usr/bin/env python3
"""
Basic usage example for MCP-Ghost
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_ghost import mcp_ghost, MCPGhostConfig


async def main():
    """Example of basic MCP-Ghost usage."""
    
    # Server configuration
    server_config = {
        "mcpServers": {
            "sqlite": {
                "command": "uvx",
                "args": ["mcp-server-sqlite", "--db-path", "test.db"]
            }
        }
    }
    
    # Configuration
    config = MCPGhostConfig(
        server_config=server_config,
        system_prompt="You are a helpful database assistant. Use the available tools to help users work with their SQLite database.",
        provider="openai",  # or "anthropic", "gemini"
        api_key=os.getenv("OPENAI_API_KEY"),  # or set directly
        user_prompt="List all tables in the database and show me the first few rows from each table"
    )
    
    print("🚀 Starting MCP-Ghost execution...")
    
    # Execute
    result = await mcp_ghost(config)
    
    # Display results
    print(f"\n✅ Success: {result.success}")
    print(f"📝 Summary: {result.summary}")
    print(f"🔧 Tool calls made: {len(result.tool_chain)}")
    print(f"⏱️  Total time: {result.execution_metadata['total_execution_time']:.2f}s")
    
    if result.tool_chain:
        print("\n🛠️  Tool execution details:")
        for i, tool_call in enumerate(result.tool_chain, 1):
            print(f"  {i}. {tool_call['tool_name']}")
            print(f"     Args: {tool_call['arguments']}")
            print(f"     Success: {tool_call['success']}")
            if tool_call['error']:
                print(f"     Error: {tool_call['error']}")
            print(f"     Time: {tool_call['execution_time']:.3f}s")
    
    if result.final_result:
        print(f"\n📋 Final result:\n{result.final_result}")
    
    if result.errors:
        print(f"\n❌ Errors encountered: {len(result.errors)}")
        for error in result.errors:
            print(f"  - {error}")


if __name__ == "__main__":
    asyncio.run(main())