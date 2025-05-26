# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP-Ghost is an intelligent MCP (Model Context Protocol) tool orchestration library that provides Claude Desktop-level capabilities programmatically. It accepts inputs directly from Python code and returns structured outputs with advanced tool chaining, backtracking, and error recovery features.

## Development Commands

### Setup and Installation
```bash
# Install in development mode
make install-dev

# Or manually with uv
uv pip install -e ".[dev,testing]"
```

### Testing
```bash
# Run all tests
make test
# or
uv run pytest

# Run specific test markers
pytest -m unit                   # Unit tests only
pytest -m integration           # Integration tests only
pytest -m record_golden         # Record new golden tests (requires API keys)
pytest -m slow                  # Tests requiring API calls

# Run single test file
uv run pytest tests/test_core.py
```

### Code Quality
```bash
# Format code
make format
# or
uv run black src/ tests/ examples/

# Lint code
make lint  
# or
uv run ruff check src/ tests/ examples/

# Full development workflow
make dev  # clean, install-dev, format, lint, test
```

### Building and Running Examples
```bash
# Build package
make build

# Run example scripts
make example-basic
make example-multi
```

## Architecture

### Core Components

**Main Entry Point**: `src/mcp_ghost/core.py:mcp_ghost()` - The primary async function that orchestrates everything

**Configuration**: `MCPGhostConfig` dataclass - Configures server connections, LLM provider, and execution parameters

**Result Structure**: `MCPGhostResult` dataclass - Returns structured output including tool chain, conversation history, and execution metadata

### Provider System

**Multi-Provider Support**: `src/mcp_ghost/providers/` directory contains:
- `client_factory.py` - Factory for creating LLM clients (OpenAI, Anthropic, Gemini)
- `base.py` - Base provider interface
- Provider-specific implementations for each LLM

**Latest Supported Models** (as of May 2025):
- **Anthropic**: Claude-4-opus, Claude-4-sonnet, Claude-3.7-sonnet, Claude-3.5-sonnet, Claude-3-opus, Claude-3-sonnet, Claude-3-haiku
- **Google Gemini**: Gemini-2.5-pro, Gemini-2.5-flash, Gemini-2.0-flash, Gemini-1.5-pro, Gemini-1.5-flash
- **OpenAI**: GPT-4o, GPT-4o-mini, GPT-4-turbo, GPT-3.5-turbo

**Tool Adaptation**: `src/mcp_ghost/tools/adapter.py` - Converts MCP tool names to provider-compatible formats (handles OpenAI's regex restrictions, etc.)

### Key Orchestration Features

**Tool Chaining**: Maintains conversation state across multiple tool interactions (up to `max_iterations`)

**Backtracking**: When tools fail, automatically retries with alternative approaches using LLM reasoning

**Error Recovery**: Intelligent handling of tool failures with context-aware retry strategies

**Result Synthesis**: Combines outputs from multiple tools into coherent final responses

### MCP Integration

**Server Discovery**: Connects to MCP servers via stdio transport defined in `server_config["mcpServers"]`

**Tool Discovery**: Automatically discovers available tools from connected servers

**Tool Execution**: Executes tool calls returned by LLM with proper error handling and timeout protection

## Testing Strategy

### Golden/Snapshot Testing
- Primary testing approach to minimize LLM API costs
- Golden files stored in `tests/goldens/` with provider-specific subdirectories
- Use `pytest -m record_golden` to record new golden tests (requires API keys)
- Regular tests replay recorded interactions for fast, deterministic testing

### Test Structure
```
tests/
├── goldens/           # Golden test recordings by provider
├── providers/         # Provider-specific tests
├── tools/             # Tool system tests
├── test_core.py       # Core functionality tests
├── test_e2e_crud.py   # End-to-end tests
└── golden_viewer.py   # Tool for inspecting golden tests
```

## Key Implementation Details

### Configuration Format
Server configuration follows Claude Desktop format and can be provided as:

**Inline Dictionary:**
```python
server_config = {
  "mcpServers": {
    "sqlite": {
      "command": "uvx", 
      "args": ["mcp-server-sqlite", "--db-path", "test.db"]
    }
  }
}
```

**File Path (recommended):**
```python
# Pass path to JSON config file
server_config = "path/to/server_config.json"
```

The config file is automatically loaded and validated in `MCPGhostConfig.__post_init__()`. See `examples/server_config.json` for a complete example.

### Error Handling Strategy
- Infrastructure errors (MCP connection failures, LLM API errors) are handled gracefully
- Tool execution errors trigger backtracking when `enable_backtracking=True`
- All errors are tracked in `MCPGhostResult.errors` with recovery actions

### Provider Compatibility
- **OpenAI**: Tool names must match regex `^[a-zA-Z0-9_-]+$`
- **Anthropic**: More flexible tool naming
- **Gemini**: Google-specific function calling schema
- Tool names are automatically adapted per provider in `ToolNameAdapter`

## Development Notes

### Dependencies
- Uses `uv` for package management
- Core dependency: Official `mcp` Python SDK for MCP protocol
- Provider SDKs: `openai`, `anthropic`, `google-genai`
- Optional MCP SDK imports with fallback for testing

### Namespace Strategy
- Tools are namespaced (default: "mcp_ghost") to avoid naming conflicts
- Original tool names are preserved for actual MCP server communication
- Adapter handles bidirectional mapping between namespaced and original names