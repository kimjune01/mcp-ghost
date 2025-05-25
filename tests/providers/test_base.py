"""Tests for base LLM client interface."""
import pytest
from mcp_ghost.providers.base import BaseLLMClient


class TestBaseLLMClient:
    """Test the abstract base class for LLM clients."""
    
    def test_base_client_is_abstract(self):
        """Test that BaseLLMClient cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseLLMClient()
    
    def test_create_completion_method_required(self):
        """Test that subclasses must implement create_completion."""
        
        class IncompleteClient(BaseLLMClient):
            pass
            
        with pytest.raises(TypeError):
            IncompleteClient()
    
    def test_concrete_implementation_works(self):
        """Test that a properly implemented subclass works."""
        
        class ConcreteClient(BaseLLMClient):
            async def create_completion(self, messages, tools=None):
                return {"response": "test", "tool_calls": []}
        
        client = ConcreteClient()
        assert client is not None
        
        # This should fail initially because the method isn't actually async
        import asyncio
        result = asyncio.run(client.create_completion([]))
        assert result == {"response": "test", "tool_calls": []}


class TestBaseLLMClientInterface:
    """Test the interface contract for LLM clients."""
    
    def test_create_completion_signature(self):
        """Test that create_completion has the correct signature."""
        
        class TestClient(BaseLLMClient):
            async def create_completion(self, messages, tools=None):
                return {"response": None, "tool_calls": []}
        
        client = TestClient()
        
        # Test method exists and is callable
        assert hasattr(client, 'create_completion')
        assert callable(client.create_completion)
        
        # This will fail initially - we need to verify the method signature
        import inspect
        sig = inspect.signature(client.create_completion)
        params = list(sig.parameters.keys())
        
        # Should have 'self', 'messages', and 'tools' parameters
        assert 'messages' in params
        assert 'tools' in params
        
        # Tools should have a default value
        assert sig.parameters['tools'].default is None
    
    def test_return_format_contract(self):
        """Test that implementations return the expected format."""
        
        class TestClient(BaseLLMClient):
            async def create_completion(self, messages, tools=None):
                # This should return the expected format but will fail initially
                return {"response": "test response", "tool_calls": []}
        
        client = TestClient()
        
        import asyncio
        result = asyncio.run(client.create_completion([{"role": "user", "content": "test"}]))
        
        # Verify expected keys exist
        assert "response" in result
        assert "tool_calls" in result
        
        # Verify types
        assert isinstance(result["response"], (str, type(None)))
        assert isinstance(result["tool_calls"], list)
        
        # This assertion will fail initially to force implementation
        assert result["response"] == "Expected response format not implemented"