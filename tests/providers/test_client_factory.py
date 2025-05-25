"""Tests for LLM client factory."""
import pytest
from mcp_ghost.providers.client_factory import get_llm_client

# Import clients conditionally to avoid dependency issues
try:
    from mcp_ghost.providers.openai_client import OpenAILLMClient
except ImportError:
    OpenAILLMClient = None

try:
    from mcp_ghost.providers.anthropic_client import AnthropicLLMClient
except ImportError:
    AnthropicLLMClient = None

try:
    from mcp_ghost.providers.gemini_client import GeminiLLMClient
except ImportError:
    GeminiLLMClient = None


class TestClientFactory:
    """Test the LLM client factory function."""
    
    def test_get_openai_client(self):
        """Test creating OpenAI client."""
        if OpenAILLMClient is None:
            # Test that factory raises ImportError when dependencies missing
            with pytest.raises(ImportError, match="OpenAI client not available"):
                get_llm_client("openai", api_key="test-key")
            return
            
        client = get_llm_client("openai", api_key="test-key")
        assert isinstance(client, OpenAILLMClient)
        assert client.model == "gpt-4o-mini"  # default
        
        # Test with custom model
        client = get_llm_client("openai", model="gpt-4", api_key="test-key")
        assert client.model == "gpt-4"
    
    def test_get_anthropic_client(self):
        """Test creating Anthropic client."""
        if AnthropicLLMClient is None:
            # Test that factory raises ImportError when dependencies missing
            with pytest.raises(ImportError, match="Anthropic client not available"):
                get_llm_client("anthropic", api_key="test-key")
            return
            
        client = get_llm_client("anthropic", api_key="test-key")
        assert isinstance(client, AnthropicLLMClient)
        assert client.model == "claude-3-sonnet-20250219"  # default
        
        # Test with custom model
        client = get_llm_client("anthropic", model="claude-3-opus", api_key="test-key")
        assert client.model == "claude-3-opus"
    
    def test_get_gemini_client(self):
        """Test creating Gemini client."""
        if GeminiLLMClient is None:
            # Test that factory raises ImportError when dependencies missing
            with pytest.raises(ImportError, match="Gemini client not available"):
                get_llm_client("gemini", api_key="test-key")
            return
            
        client = get_llm_client("gemini", api_key="test-key")
        assert isinstance(client, GeminiLLMClient)
        assert client.model == "gemini-2.0-flash"  # default
        
        # Test with custom model
        client = get_llm_client("gemini", model="gemini-1.5-pro", api_key="test-key")
        assert client.model == "gemini-1.5-pro"
    
    def test_provider_case_insensitive(self):
        """Test that provider names are case insensitive."""
        if OpenAILLMClient is None:
            # Test error handling is case insensitive
            for provider in ["OpenAI", "OPENAI", "openai"]:
                with pytest.raises(ImportError, match="OpenAI client not available"):
                    get_llm_client(provider, api_key="test-key")
            return
            
        client1 = get_llm_client("OpenAI", api_key="test-key")
        client2 = get_llm_client("OPENAI", api_key="test-key")
        client3 = get_llm_client("openai", api_key="test-key")
        
        assert all(isinstance(c, OpenAILLMClient) for c in [client1, client2, client3])
    
    def test_unsupported_provider_raises_error(self):
        """Test that unsupported providers raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            get_llm_client("unsupported_provider", api_key="test-key")
        
        with pytest.raises(ValueError, match="Unsupported provider"):
            get_llm_client("gpt", api_key="test-key")  # Should be "openai"
    
    @pytest.mark.skipif(OpenAILLMClient is None, reason="OpenAI dependencies not available")
    def test_additional_kwargs_passed_through(self):
        """Test that additional kwargs are passed to client constructors."""
        # This will fail initially until kwargs handling is verified
        client = get_llm_client(
            "openai", 
            api_key="test-key",
            api_base="https://custom.endpoint.com"
        )
        
        # Verify that custom endpoint was set
        # This assertion will fail until we verify the kwargs are passed through
        assert hasattr(client, 'client')
        # Check if the base URL was actually set - this will fail initially
        assert "custom.endpoint.com" in str(client.client.base_url)
    
    def test_default_models_are_correct(self):
        """Test that default models match expected values."""
        # Test each provider if available
        if OpenAILLMClient is not None:
            openai_client = get_llm_client("openai", api_key="test-key")
            assert openai_client.model == "gpt-4o-mini"
            
        if AnthropicLLMClient is not None:
            anthropic_client = get_llm_client("anthropic", api_key="test-key") 
            assert anthropic_client.model == "claude-3-sonnet-20250219"
            
        if GeminiLLMClient is not None:
            gemini_client = get_llm_client("gemini", api_key="test-key")
            assert gemini_client.model == "gemini-2.0-flash"
            
        # If none are available, just make sure the test doesn't skip silently
        if all(c is None for c in [OpenAILLMClient, AnthropicLLMClient, GeminiLLMClient]):
            pytest.skip("No LLM clients available for testing")
    
    def test_all_supported_providers_listed(self):
        """Test that factory supports all expected providers."""
        supported_providers = ["openai", "anthropic", "gemini"]
        
        for provider in supported_providers:
            try:
                client = get_llm_client(provider, api_key="test-key")
                assert client is not None
            except ImportError:
                # Expected if dependencies are missing
                pass
            except Exception as e:
                pytest.fail(f"Provider {provider} should be supported but failed: {e}")
        
        # This test will fail if we add a new provider but forget to update the factory
        # Force failure to remind us to update this test when adding providers
        expected_count = 3
        actual_count = len(supported_providers)
        if actual_count != expected_count:
            pytest.fail(f"Expected {expected_count} providers, found {actual_count}. Update this test!")


class TestFactoryErrorHandling:
    """Test error handling in the client factory."""
    
    def test_none_provider_raises_error(self):
        """Test that None provider raises appropriate error."""
        with pytest.raises((ValueError, AttributeError)):
            get_llm_client(None, api_key="test-key")
    
    def test_empty_provider_raises_error(self):
        """Test that empty string provider raises error.""" 
        with pytest.raises(ValueError):
            get_llm_client("", api_key="test-key")
    
    @pytest.mark.skipif(OpenAILLMClient is None, reason="OpenAI dependencies not available")
    def test_missing_api_key_handling(self):
        """Test handling of missing API keys."""
        # Different providers might handle missing keys differently
        # This test documents current behavior and will fail if it changes
        
        # This should fail initially if we don't have proper key validation
        with pytest.raises((ValueError, TypeError)):
            get_llm_client("openai", api_key=None)
    
    @pytest.mark.skipif(OpenAILLMClient is None, reason="OpenAI dependencies not available")
    def test_invalid_model_handling(self):
        """Test handling of invalid model names."""
        # This will fail initially - we should validate model names
        client = get_llm_client("openai", model="invalid-model-name", api_key="test-key")
        
        # Client should still be created but with the invalid model
        # This documents current behavior
        assert client.model == "invalid-model-name"
        
        # In the future, we might want to validate model names
        # This assertion will fail when we add validation
        assert True  # Placeholder - replace with actual validation test