"""Test configuration and fixtures for MCP-Ghost tests."""
import pytest
import asyncio
import sys
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Configure pytest-asyncio to avoid deprecation warnings
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture
def sample_tool_info():
    """Fixture providing a sample ToolInfo instance."""
    try:
        from mcp_ghost.tools.models import ToolInfo
        return ToolInfo(
            name="test_tool",
            namespace="test_namespace",
            description="A sample test tool",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Query parameter"},
                    "limit": {"type": "integer", "default": 10}
                },
                "required": ["query"]
            },
            is_async=True,
            tags=["test", "sample"],
            supports_streaming=False
        )
    except ImportError:
        # Return a mock if ToolInfo can't be imported
        return Mock(
            name="test_tool",
            namespace="test_namespace", 
            description="A sample test tool"
        )


@pytest.fixture
def sample_server_config():
    """Sample server configuration for testing."""
    return {
        "mcpServers": {
            "test_server": {
                "command": "echo", 
                "args": ["test"]
            }
        }
    }


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    mock = AsyncMock()
    mock.create_completion.return_value = {
        "response": "Test response",
        "tool_calls": [],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
    }
    return mock


@pytest.fixture
def sample_openai_tools():
    """Fixture providing sample tools in OpenAI format."""
    return [
        {
            "type": "function",
            "function": {
                "name": "test_tool",
                "description": "A test tool",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    },
                    "required": ["query"]
                }
            }
        }
    ]


# Test markers for different test categories
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (requires API calls)"
    )
    config.addinivalue_line(
        "markers", "record_golden: mark test for golden test recording"
    )