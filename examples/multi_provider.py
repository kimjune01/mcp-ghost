#!/usr/bin/env python3
"""
Multi-provider comparison example for MCP-Ghost
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_ghost import mcp_ghost, MCPGhostConfig


async def test_provider(provider: str, model: str, api_key: str, user_prompt: str):
    """Test a specific provider."""
    
    server_config = {
        "mcpServers": {
            "sqlite": {
                "command": "uvx", 
                "args": ["mcp-server-sqlite", "--db-path", "test.db"]
            }
        }
    }
    
    config = MCPGhostConfig(
        server_config=server_config,
        system_prompt="You are a helpful assistant. Use the available tools to answer user questions.",
        provider=provider,
        api_key=api_key,
        model=model,
        user_prompt=user_prompt
    )
    
    print(f"\n🤖 Testing {provider} ({model})...")
    
    try:
        result = await mcp_ghost(config)
        
        print(f"  ✅ Success: {result.success}")
        print(f"  🔧 Tools used: {len(result.tool_chain)}")
        print(f"  ⏱️  Time: {result.execution_metadata['total_execution_time']:.2f}s")
        print(f"  🪙 Tokens: {result.execution_metadata['token_usage']['total_tokens']}")
        
        if result.final_result:
            print(f"  📝 Response preview: {result.final_result[:100]}...")
            
        return result
        
    except Exception as exc:
        print(f"  ❌ Error: {exc}")
        return None


async def main():
    """Compare different providers on the same task."""
    
    user_prompt = "What tables are in the database? Give me a quick summary of what data each table contains."
    
    providers = [
        {
            "name": "openai",
            "model": "gpt-4o-mini", 
            "api_key": os.getenv("OPENAI_API_KEY")
        },
        {
            "name": "anthropic",
            "model": "claude-3-5-sonnet-20241022",
            "api_key": os.getenv("ANTHROPIC_API_KEY")
        },
        {
            "name": "gemini", 
            "model": "gemini-1.5-pro",
            "api_key": os.getenv("GOOGLE_API_KEY")
        }
    ]
    
    results = []
    
    for provider_config in providers:
        if provider_config["api_key"]:
            result = await test_provider(
                provider_config["name"],
                provider_config["model"], 
                provider_config["api_key"],
                user_prompt
            )
            if result:
                results.append((provider_config["name"], result))
        else:
            print(f"\n⚠️  Skipping {provider_config['name']} - no API key found")
    
    # Compare results
    if len(results) > 1:
        print(f"\n📊 Comparison of {len(results)} providers:")
        print("Provider     | Success | Tools | Time   | Tokens")
        print("-------------|---------|-------|--------|--------")
        
        for provider_name, result in results:
            success = "✅" if result.success else "❌"
            tools = len(result.tool_chain)
            time = result.execution_metadata['total_execution_time']
            tokens = result.execution_metadata['token_usage']['total_tokens']
            
            print(f"{provider_name:<12} | {success:<7} | {tools:<5} | {time:<6.2f} | {tokens}")


if __name__ == "__main__":
    asyncio.run(main())