# MCP-Ghost 👻

**Intelligent MCP tool orchestration library with Claude Desktop-level capabilities**

MCP-Ghost provides a programmatic interface for interacting with Model Context Protocol (MCP) servers through LLMs. Unlike CLI interfaces, MCP-Ghost accepts inputs directly from Python code and returns structured outputs with advanced tool orchestration features.

## ✨ Features

- 🔗 **Tool Chaining**: Automatically executes sequences of dependent tool calls
- 🔄 **Backtracking**: Retries failed operations with alternative approaches  
- 🧠 **Context Management**: Maintains conversation state across multiple tool interactions
- 🛠️ **Error Recovery**: Intelligent handling of tool failures with retry strategies
- 📊 **Result Synthesis**: Combines outputs from multiple tools into coherent responses

## 🎯 Supported Providers

- **OpenAI**: GPT-4o, GPT-4o-mini, GPT-4-turbo, GPT-3.5-turbo
- **Anthropic (Claude)**: Claude-3.5-sonnet, Claude-3-opus, Claude-3-sonnet, Claude-3-haiku  
- **Google (Gemini)**: Gemini-1.5-pro, Gemini-1.5-flash, Gemini-1.0-pro

## 📦 Installation

```bash
pip install mcp-ghost
```

## 🚀 Quick Start

```python
import asyncio
from mcp_ghost import mcp_ghost, MCPGhostConfig

async def main():
    config = MCPGhostConfig(
        server_config={
            "mcpServers": {
                "sqlite": {
                    "command": "uvx",
                    "args": ["mcp-server-sqlite", "--db-path", "test.db"]
                }
            }
        },
        system_prompt="You are a helpful database assistant.",
        provider="openai",
        api_key="sk-...",
        user_prompt="List all tables and describe their schemas"
    )
    
    result = await mcp_ghost(config)
    print(f"Success: {result.success}")
    print(f"Summary: {result.summary}")
    print(f"Tool calls made: {len(result.tool_chain)}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 🏗️ Architecture

MCP-Ghost is designed for use in larger architectures where:

1. **Human User** provides natural language input
2. **Prompt Builder** processes user input and ensures security constraints
3. **MCP-Ghost** executes the one-shot tool operation with intelligent orchestration
4. **Results** are returned for further processing

## 🔒 Security Model

- **Prompt Builder Responsibility**: Input validation and security filtering
- **MCP Server Trust**: Trusts provided MCP servers completely  
- **Stdio Isolation**: Each MCP server runs in its own subprocess
- **Timeout Protection**: Tool execution timeouts prevent hanging operations

## 📖 Documentation

- [Requirements Specification](docs/requirements.md)
- [API Reference](docs/api.md)
- [Examples](examples/)
- [Testing Guide](docs/testing.md)

## 🧪 Testing

MCP-Ghost uses a golden/snapshot testing framework to minimize LLM API costs:

```bash
# Run tests (uses recorded golden files)
pytest

# Record new golden tests (requires API keys)
pytest -m record_golden
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests (including golden tests for new features)
4. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built on top of:
- [CHUK-MCP](https://github.com/chrishayuk/chuk-mcp) - MCP protocol implementation
- [CHUK Tool Processor](https://github.com/chrishayuk/chuk-tool-processor) - Tool execution framework