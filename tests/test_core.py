"""Tests for core MCP-Ghost functionality interfaces."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from mcp_ghost.core import mcp_ghost, MCPGhostConfig, MCPGhostResult


class TestMCPGhostConfig:
    """Test the MCPGhostConfig interface."""
    
    def test_config_creation_minimal(self):
        """Test creating config with minimal required fields."""
        config = MCPGhostConfig(
            server_config={"mcpServers": {}},
            system_prompt="Test prompt",
            provider="openai",
            api_key="test-key",
            user_prompt="Test user prompt"
        )
        
        assert config.server_config == {"mcpServers": {}}
        assert config.system_prompt == "Test prompt"
        assert config.provider == "openai"
        assert config.api_key == "test-key"
        assert config.user_prompt == "Test user prompt"
    
    def test_config_creation_with_all_fields(self):
        """Test creating config with all optional fields."""
        config = MCPGhostConfig(
            server_config={"mcpServers": {"sqlite": {}}},
            system_prompt="System prompt",
            provider="anthropic",
            api_key="api-key",
            user_prompt="User prompt",
            model="claude-3-opus",
            namespace="test_namespace",
            timeout=60.0,
            max_iterations=5,
            enable_backtracking=False,
            conversation_memory=False
        )
        
        assert config.model == "claude-3-opus"
        assert config.namespace == "test_namespace"
        assert config.timeout == 60.0
        assert config.max_iterations == 5
        assert config.enable_backtracking is False
        assert config.conversation_memory is False
    
    def test_config_defaults(self):
        """Test that config has proper default values."""
        config = MCPGhostConfig(
            server_config={},
            system_prompt="",
            provider="openai",
            api_key="key",
            user_prompt=""
        )
        
        assert config.model is None  # Should default based on provider
        assert config.namespace == "mcp_ghost"
        assert config.timeout == 30.0
        assert config.max_iterations == 10
        assert config.enable_backtracking is True
        assert config.conversation_memory is True


class TestMCPGhostResult:
    """Test the MCPGhostResult interface."""
    
    def test_result_structure(self):
        """Test that result has expected structure."""
        result = MCPGhostResult(
            success=True,
            final_result="Test result",
            summary="Test summary",
            tool_chain=[],
            conversation_history=[],
            errors=[],
            execution_metadata={}
        )
        
        assert result.success is True
        assert result.final_result == "Test result"
        assert result.summary == "Test summary"
        assert isinstance(result.tool_chain, list)
        assert isinstance(result.conversation_history, list)
        assert isinstance(result.errors, list)
        assert isinstance(result.execution_metadata, dict)
    
    def test_result_tool_chain_structure(self):
        """Test tool chain structure in results."""
        tool_call = {
            "iteration": 1,
            "tool_name": "test_tool",
            "arguments": {"arg": "value"},
            "success": True,
            "result": "tool result",
            "error": None,
            "execution_time": 1.5,
            "reasoning": "LLM reasoning",
            "retry_attempt": 0
        }
        
        result = MCPGhostResult(
            success=True,
            final_result=None,
            summary="",
            tool_chain=[tool_call],
            conversation_history=[],
            errors=[],
            execution_metadata={}
        )
        
        assert len(result.tool_chain) == 1
        assert result.tool_chain[0]["tool_name"] == "test_tool"
        assert result.tool_chain[0]["success"] is True


class TestMCPGhostMainFunction:
    """Test the main mcp_ghost function interface."""
    
    @pytest.mark.asyncio
    async def test_mcp_ghost_accepts_config(self):
        """Test that mcp_ghost accepts MCPGhostConfig."""
        config = MCPGhostConfig(
            server_config={"mcpServers": {}},
            system_prompt="Test",
            provider="openai",
            api_key="test-key",
            user_prompt="Test prompt"
        )
        
        # Mock the LLM client to avoid real API calls
        with patch('mcp_ghost.core.get_llm_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_completion.return_value = {
                "content": "Test response",
                "tool_calls": None,
                "finish_reason": "stop"
            }
            mock_get_client.return_value = mock_client
            
            result = await mcp_ghost(config)
            assert isinstance(result, MCPGhostResult)
    
    @pytest.mark.asyncio
    async def test_mcp_ghost_returns_proper_structure(self):
        """Test that mcp_ghost returns properly structured result."""
        config = MCPGhostConfig(
            server_config={"mcpServers": {}},
            system_prompt="Test",
            provider="openai", 
            api_key="test-key",
            user_prompt="Test"
        )
        
        # Mock the LLM client
        with patch('mcp_ghost.core.get_llm_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_completion.return_value = {
                "content": "Test response",
                "tool_calls": None,
                "finish_reason": "stop"
            }
            mock_get_client.return_value = mock_client
            
            result = await mcp_ghost(config)
            
            # Verify result structure
            assert hasattr(result, 'success')
            assert hasattr(result, 'final_result')
            assert hasattr(result, 'summary')
            assert hasattr(result, 'tool_chain')
            assert hasattr(result, 'conversation_history')
            assert hasattr(result, 'errors')
            assert hasattr(result, 'execution_metadata')
    
    @pytest.mark.asyncio
    async def test_mcp_ghost_handles_server_connection_failure(self):
        """Test mcp_ghost handles server connection failures."""
        config = MCPGhostConfig(
            server_config={"mcpServers": {"bad_server": {"command": "nonexistent", "args": []}}},
            system_prompt="Test",
            provider="openai",
            api_key="test-key", 
            user_prompt="Test"
        )
        
        # Mock LLM client but let server connection fail naturally
        with patch('mcp_ghost.core.get_llm_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_completion.return_value = {
                "content": "Test response",
                "tool_calls": None,
                "finish_reason": "stop"
            }
            mock_get_client.return_value = mock_client
            
            result = await mcp_ghost(config)
            
            # Should handle failure gracefully and still return a result
            assert isinstance(result, MCPGhostResult)
            # May succeed with 0 tools discovered if server connection fails
            assert result.execution_metadata.get("servers_connected", 0) == 0
    
    @pytest.mark.asyncio
    async def test_mcp_ghost_handles_llm_failure(self):
        """Test mcp_ghost handles LLM provider failures."""
        config = MCPGhostConfig(
            server_config={"mcpServers": {}},
            system_prompt="Test",
            provider="invalid_provider",
            api_key="test-key",
            user_prompt="Test"
        )
        
        # This should fail when trying to get invalid provider
        result = await mcp_ghost(config)
        assert result.success is False
        assert len(result.errors) > 0


class TestMCPGhostIntegrationInterface:
    """Test MCP-Ghost integration points."""
    
    def test_mcp_ghost_module_exports(self):
        """Test that mcp_ghost module exports expected interface."""
        import mcp_ghost
        
        # Should export these main components
        assert hasattr(mcp_ghost, 'mcp_ghost')
        assert hasattr(mcp_ghost, 'MCPGhostConfig')
        assert hasattr(mcp_ghost, 'MCPGhostResult')
        
        # mcp_ghost should be callable
        assert callable(mcp_ghost.mcp_ghost)
    
    def test_config_is_dataclass(self):
        """Test that MCPGhostConfig is a proper dataclass."""
        import dataclasses
        
        assert dataclasses.is_dataclass(MCPGhostConfig)
        
        # Should have expected fields
        fields = [f.name for f in dataclasses.fields(MCPGhostConfig)]
        expected_fields = [
            'server_config', 'system_prompt', 'provider', 
            'api_key', 'user_prompt', 'model', 'namespace',
            'timeout', 'max_iterations', 'enable_backtracking',
            'conversation_memory'
        ]
        
        for field in expected_fields:
            assert field in fields
    
    def test_result_is_dataclass(self):
        """Test that MCPGhostResult is a proper dataclass.""" 
        import dataclasses
        
        assert dataclasses.is_dataclass(MCPGhostResult)
        
        fields = [f.name for f in dataclasses.fields(MCPGhostResult)]
        expected_fields = [
            'success', 'final_result', 'summary', 'tool_chain',
            'conversation_history', 'errors', 'execution_metadata'
        ]
        
        for field in expected_fields:
            assert field in fields


class TestMCPGhostProviderIntegration:
    """Test MCP-Ghost provider integration interface."""
    
    @pytest.mark.asyncio
    async def test_supports_all_required_providers(self):
        """Test that all required providers are supported."""
        required_providers = ["openai", "anthropic", "gemini"]
        
        for provider in required_providers:
            config = MCPGhostConfig(
                server_config={"mcpServers": {}},
                system_prompt="Test",
                provider=provider,
                api_key="test-key",
                user_prompt="Test"
            )
            
            # Mock LLM client for each provider
            with patch('mcp_ghost.core.get_llm_client') as mock_get_client:
                mock_client = AsyncMock()
                mock_client.create_completion.return_value = {
                    "content": "Test response",
                    "tool_calls": None,
                    "finish_reason": "stop"
                }
                mock_get_client.return_value = mock_client
                
                result = await mcp_ghost(config)
                assert isinstance(result, MCPGhostResult)
    
    def test_provider_validation(self):
        """Test that invalid providers are handled gracefully."""
        # Invalid providers should be handled in runtime, not validation
        config = MCPGhostConfig(
            server_config={},
            system_prompt="Test",
            provider="invalid_provider",
            api_key="test-key",
            user_prompt="Test"
        )
        
        # Should create config successfully, validation happens at runtime
        assert config.provider == "invalid_provider"