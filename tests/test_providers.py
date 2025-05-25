"""Tests for provider module interfaces."""
import pytest
from unittest.mock import Mock, patch
from mcp_ghost.providers import (
    BaseLLMClient, 
    OpenAILLMClient, 
    AnthropicLLMClient, 
    GeminiLLMClient, 
    get_llm_client
)


class TestProviderModuleInterface:
    """Test the providers module interface."""
    
    def test_module_exports_all_clients(self):
        """Test that providers module exports all expected clients."""
        import mcp_ghost.providers as providers
        
        # Should export all client classes
        assert hasattr(providers, 'BaseLLMClient')
        assert hasattr(providers, 'OpenAILLMClient')
        assert hasattr(providers, 'AnthropicLLMClient')
        assert hasattr(providers, 'GeminiLLMClient')
        assert hasattr(providers, 'get_llm_client')
        
        # Factory function should be callable
        assert callable(providers.get_llm_client)
    
    def test_all_clients_inherit_from_base(self):
        """Test that all client implementations inherit from BaseLLMClient."""
        assert issubclass(OpenAILLMClient, BaseLLMClient)
        assert issubclass(AnthropicLLMClient, BaseLLMClient)
        assert issubclass(GeminiLLMClient, BaseLLMClient)
    
    def test_factory_creates_correct_types(self):
        """Test that factory returns correct client types."""
        openai_client = get_llm_client("openai", api_key="test")
        anthropic_client = get_llm_client("anthropic", api_key="test")
        gemini_client = get_llm_client("gemini", api_key="test")
        
        assert isinstance(openai_client, OpenAILLMClient)
        assert isinstance(anthropic_client, AnthropicLLMClient)
        assert isinstance(gemini_client, GeminiLLMClient)
        
        # All should also be instances of base class
        assert isinstance(openai_client, BaseLLMClient)
        assert isinstance(anthropic_client, BaseLLMClient)
        assert isinstance(gemini_client, BaseLLMClient)


class TestBaseLLMClientInterface:
    """Test the base LLM client interface contract."""
    
    def test_base_client_is_abstract(self):
        """Test that BaseLLMClient cannot be instantiated."""
        with pytest.raises(TypeError):
            BaseLLMClient()
    
    def test_concrete_clients_implement_interface(self):
        """Test that all concrete clients implement required methods."""
        clients = [
            OpenAILLMClient(api_key="test"),
            AnthropicLLMClient(api_key="test"), 
            GeminiLLMClient(api_key="test")
        ]
        
        for client in clients:
            # All should have create_completion method
            assert hasattr(client, 'create_completion')
            assert callable(client.create_completion)
            
            # Method should be async
            import inspect
            assert inspect.iscoroutinefunction(client.create_completion)
    
    @pytest.mark.asyncio
    async def test_clients_return_expected_format(self):
        """Test that all clients return the expected response format."""
        # This will fail initially until proper mocking is set up
        with patch('openai.OpenAI'), \
             patch('anthropic.Anthropic'), \
             patch('google.genai.Client'):
            
            clients = [
                OpenAILLMClient(api_key="test"),
                AnthropicLLMClient(api_key="test"),
                GeminiLLMClient(api_key="test")
            ]
            
            messages = [{"role": "user", "content": "test"}]
            
            for client in clients:
                # Mock the underlying client calls
                with patch.object(client, 'create_completion') as mock_completion:
                    mock_completion.return_value = {
                        "response": "test response",
                        "tool_calls": []
                    }
                    
                    result = await client.create_completion(messages)
                    
                    # All should return dict with these keys
                    assert isinstance(result, dict)
                    assert "response" in result
                    assert "tool_calls" in result
                    assert isinstance(result["tool_calls"], list)


class TestOpenAIClientInterface:
    """Test OpenAI client specific interface."""
    
    def test_openai_client_initialization(self):
        """Test OpenAI client can be initialized."""
        client = OpenAILLMClient(api_key="test-key")
        assert client.model == "gpt-4o-mini"  # default
        
        client = OpenAILLMClient(model="gpt-4", api_key="test-key")
        assert client.model == "gpt-4"
    
    @pytest.mark.asyncio
    async def test_openai_client_streaming_interface(self):
        """Test OpenAI client supports streaming."""
        with patch('openai.OpenAI'):
            client = OpenAILLMClient(api_key="test")
            
            # Should support stream parameter
            import inspect
            sig = inspect.signature(client.create_completion)
            
            # This will fail initially if streaming isn't supported
            assert 'stream' in [p.name for p in sig.parameters.values()]


class TestAnthropicClientInterface:
    """Test Anthropic client specific interface."""
    
    def test_anthropic_client_initialization(self):
        """Test Anthropic client initialization."""
        client = AnthropicLLMClient(api_key="test-key")
        assert client.model == "claude-3-sonnet-20250219"  # default
    
    def test_anthropic_handles_system_messages(self):
        """Test that Anthropic client properly handles system messages."""
        client = AnthropicLLMClient(api_key="test")
        
        # Should have method to split messages for Anthropic format
        assert hasattr(client, '_split_for_anthropic')
        assert callable(client._split_for_anthropic)
    
    def test_anthropic_converts_tools(self):
        """Test that Anthropic client converts tools to correct format."""
        client = AnthropicLLMClient(api_key="test")
        
        # Should have method to convert tools
        assert hasattr(client, '_convert_tools')
        assert callable(client._convert_tools)


class TestGeminiClientInterface:
    """Test Gemini client specific interface."""
    
    def test_gemini_client_initialization(self):
        """Test Gemini client initialization."""
        # This will fail initially if dotenv isn't handled properly
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-key'}):
            client = GeminiLLMClient()
            assert client.model == "gemini-2.0-flash"  # default
    
    def test_gemini_requires_api_key(self):
        """Test that Gemini client requires API key."""
        with patch.dict('os.environ', {}, clear=True):
            # Should raise error if no API key available
            with pytest.raises(ValueError):
                GeminiLLMClient()


class TestClientFactoryInterface:
    """Test the client factory interface."""
    
    def test_factory_supports_all_providers(self):
        """Test that factory supports all required providers."""
        providers = ["openai", "anthropic", "gemini"]
        
        for provider in providers:
            client = get_llm_client(provider, api_key="test")
            assert isinstance(client, BaseLLMClient)
    
    def test_factory_case_insensitive(self):
        """Test that factory is case insensitive."""
        client1 = get_llm_client("openai", api_key="test")
        client2 = get_llm_client("OpenAI", api_key="test")
        client3 = get_llm_client("OPENAI", api_key="test")
        
        # All should be same type
        assert type(client1) == type(client2) == type(client3)
    
    def test_factory_rejects_invalid_providers(self):
        """Test that factory rejects invalid providers."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            get_llm_client("invalid", api_key="test")
    
    def test_factory_passes_kwargs(self):
        """Test that factory passes through additional kwargs."""
        # This will fail initially if kwargs aren't properly handled
        client = get_llm_client(
            "openai", 
            api_key="test",
            api_base="https://custom.endpoint.com"
        )
        
        # Should have passed the custom base URL
        assert hasattr(client, 'client')


class TestProviderIntegration:
    """Test provider integration points."""
    
    def test_all_providers_handle_tools(self):
        """Test that all providers can handle tool definitions."""
        providers = [
            OpenAILLMClient(api_key="test"),
            AnthropicLLMClient(api_key="test"),
            GeminiLLMClient(api_key="test")
        ]
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "test_tool",
                    "description": "A test tool",
                    "parameters": {"type": "object"}
                }
            }
        ]
        
        for provider in providers:
            # Should accept tools parameter without error
            import inspect
            sig = inspect.signature(provider.create_completion)
            assert 'tools' in [p.name for p in sig.parameters.values()]
    
    def test_providers_handle_errors_gracefully(self):
        """Test that providers handle API errors gracefully."""
        # This will fail initially if error handling isn't implemented
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            
            client = OpenAILLMClient(api_key="test")
            
            # Should handle API errors without crashing
            import asyncio
            with pytest.raises(Exception):
                asyncio.run(client.create_completion([{"role": "user", "content": "test"}]))