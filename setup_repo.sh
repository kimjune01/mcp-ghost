#!/bin/bash
# Setup script for MCP-Ghost repository

set -e

echo "🚀 Setting up MCP-Ghost repository..."

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Run this script from the mcp-ghost root directory"
    exit 1
fi

echo "📦 Installing dependencies with uv..."
uv sync

echo "🧪 Running initial tests..."
uv run pytest tests/ -v

echo "🔍 Running example (requires API key)..."
if [ -n "$OPENAI_API_KEY" ]; then
    echo "  Found OpenAI API key, running basic example..."
    uv run python examples/basic_usage.py
else
    echo "  ⚠️  No OpenAI API key found. Set OPENAI_API_KEY to test examples."
    echo "  You can also use ANTHROPIC_API_KEY or GOOGLE_API_KEY with other providers."
fi

echo ""
echo "✅ MCP-Ghost setup complete!"
echo ""
echo "📖 Next steps:"
echo "  1. Set API keys: export OPENAI_API_KEY=your_key"
echo "  2. Run examples: uv run python examples/basic_usage.py"
echo "  3. Run tests: uv run pytest"
echo "  4. Import in code: from mcp_ghost import mcp_ghost, MCPGhostConfig"
echo ""
echo "🔗 Repository: git@github.com:kimjune01/mcp-ghost.git"