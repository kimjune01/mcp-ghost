"""Test that all modules can be imported correctly."""
import pytest


class TestImports:
    """Test module import interfaces."""
    
    def test_can_import_main_package(self):
        """Test that main mcp_ghost package can be imported."""
        try:
            import mcp_ghost
            assert hasattr(mcp_ghost, '__version__')
        except ImportError as e:
            pytest.fail(f"Cannot import mcp_ghost: {e}")
    
    def test_can_import_core_functions(self):
        """Test that core functions can be imported.""" 
        try:
            from mcp_ghost import mcp_ghost, MCPGhostConfig, MCPGhostResult
            # These will fail initially until implemented
            assert callable(mcp_ghost)
            assert MCPGhostConfig is not None
            assert MCPGhostResult is not None
        except ImportError as e:
            pytest.fail(f"Cannot import core functions: {e}")
    
    def test_can_import_providers(self):
        """Test that provider modules can be imported."""
        try:
            from mcp_ghost.providers import (
                BaseLLMClient, 
                OpenAILLMClient, 
                AnthropicLLMClient, 
                GeminiLLMClient,
                get_llm_client
            )
            assert all(cls is not None for cls in [
                BaseLLMClient, OpenAILLMClient, AnthropicLLMClient, GeminiLLMClient
            ])
            assert callable(get_llm_client)
        except ImportError as e:
            pytest.fail(f"Cannot import providers: {e}")
    
    def test_can_import_tools(self):
        """Test that tool modules can be imported."""
        try:
            from mcp_ghost.tools import (
                ToolInfo, 
                ServerInfo, 
                ToolCallResult, 
                ResourceInfo,
                ToolNameAdapter,
                format_tool_for_openai,
                format_tool_response
            )
            # All should be importable
            assert all(item is not None for item in [
                ToolInfo, ServerInfo, ToolCallResult, ResourceInfo,
                ToolNameAdapter, format_tool_for_openai, format_tool_response
            ])
        except ImportError as e:
            pytest.fail(f"Cannot import tools: {e}")
    
    def test_can_import_utils(self):
        """Test that utility modules can be imported."""
        try:
            from mcp_ghost.utils.prompt_generator import SystemPromptGenerator
            assert SystemPromptGenerator is not None
        except ImportError as e:
            pytest.fail(f"Cannot import utils: {e}")
    
    def test_package_structure(self):
        """Test that package has expected structure."""
        import mcp_ghost
        
        # Should have expected attributes
        expected_attrs = ['mcp_ghost', 'MCPGhostConfig', 'MCPGhostResult']
        for attr in expected_attrs:
            assert hasattr(mcp_ghost, attr), f"Missing attribute: {attr}"
    
    def test_submodules_exist(self):
        """Test that all expected submodules exist."""
        try:
            import mcp_ghost.core
            import mcp_ghost.providers  
            import mcp_ghost.tools
            import mcp_ghost.utils
            
            # All should import without error
            assert True
        except ImportError as e:
            pytest.fail(f"Missing submodule: {e}")
    
    def test_provider_clients_instantiable(self):
        """Test that provider clients can be instantiated."""
        from mcp_ghost.providers import OpenAILLMClient, AnthropicLLMClient, GeminiLLMClient
        
        # These will fail initially if constructors are broken
        try:
            openai_client = OpenAILLMClient(api_key="test")
            assert openai_client is not None
        except Exception as e:
            pytest.fail(f"Cannot instantiate OpenAI client: {e}")
        
        try:
            anthropic_client = AnthropicLLMClient(api_key="test")
            assert anthropic_client is not None
        except Exception as e:
            pytest.fail(f"Cannot instantiate Anthropic client: {e}")
        
        # Gemini might fail due to environment requirements
        try:
            with pytest.raises(ValueError):  # Should fail with no API key
                GeminiLLMClient(api_key=None)
        except Exception as e:
            pytest.fail(f"Unexpected error with Gemini client: {e}")
    
    def test_tool_models_instantiable(self):
        """Test that tool models can be instantiated."""
        from mcp_ghost.tools import ToolInfo, ServerInfo, ToolCallResult, ResourceInfo
        
        # These will fail initially if dataclass definitions are broken
        try:
            tool = ToolInfo(name="test", namespace="ns")
            assert tool.name == "test"
        except Exception as e:
            pytest.fail(f"Cannot instantiate ToolInfo: {e}")
        
        try:
            server = ServerInfo(id=1, name="test", status="connected", tool_count=0, namespace="ns")
            assert server.id == 1
        except Exception as e:
            pytest.fail(f"Cannot instantiate ServerInfo: {e}")
        
        try:
            result = ToolCallResult(tool_name="test", success=True)
            assert result.success is True
        except Exception as e:
            pytest.fail(f"Cannot instantiate ToolCallResult: {e}")
        
        try:
            resource = ResourceInfo()
            assert resource is not None
        except Exception as e:
            pytest.fail(f"Cannot instantiate ResourceInfo: {e}")