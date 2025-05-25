"""Tests for OpenAI LLM client."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from mcp_ghost.providers.openai_client import OpenAILLMClient


class TestOpenAILLMClient:
    """Test OpenAI client implementation."""
    
    def test_client_initialization(self):
        """Test that OpenAI client initializes correctly."""
        client = OpenAILLMClient(api_key="test-key")
        assert client is not None
        assert client.model == "gpt-4o-mini"  # default model
        
        # Test custom model
        client = OpenAILLMClient(model="gpt-4", api_key="test-key")
        assert client.model == "gpt-4"
    
    def test_client_requires_api_key(self):
        """Test that client requires an API key."""
        # This should fail initially if no validation exists
        with pytest.raises(ValueError):
            OpenAILLMClient(api_key=None)
    
    @pytest.mark.asyncio
    async def test_create_completion_basic(self):
        """Test basic completion creation."""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # Mock the completion response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = Mock()
            mock_response.choices[0].message.content = "Test response"
            mock_response.choices[0].message.tool_calls = None
            
            mock_client.chat.completions.create.return_value = mock_response
            
            client = OpenAILLMClient(api_key="test-key")
            
            messages = [{"role": "user", "content": "Hello"}]
            result = await client.create_completion(messages)
            
            # Verify the result format
            assert "response" in result
            assert "tool_calls" in result
            assert result["response"] == "Test response"
            assert result["tool_calls"] == []
    
    @pytest.mark.asyncio
    async def test_create_completion_with_tools(self):
        """Test completion with tool calls."""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # Mock tool call response
            mock_tool_call = Mock()
            mock_tool_call.id = "call_123"
            mock_tool_call.function.name = "test_function"
            mock_tool_call.function.arguments = '{"arg": "value"}'
            
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = Mock()
            mock_response.choices[0].message.content = None
            mock_response.choices[0].message.tool_calls = [mock_tool_call]
            
            mock_client.chat.completions.create.return_value = mock_response
            
            client = OpenAILLMClient(api_key="test-key")
            
            messages = [{"role": "user", "content": "Use tools"}]
            tools = [{"type": "function", "function": {"name": "test_function"}}]
            
            result = await client.create_completion(messages, tools)
            
            # This should fail initially until tool call handling is implemented
            assert result["response"] is None
            assert len(result["tool_calls"]) == 1
            assert result["tool_calls"][0]["function"]["name"] == "test_function"
    
    def test_tool_name_sanitization(self):
        """Test that tool names are properly sanitized for OpenAI."""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "invalid.tool-name!",
                    "description": "Test tool"
                }
            }
        ]
        
        client = OpenAILLMClient(api_key="test-key")
        sanitized = client._sanitize_tool_names(tools)
        
        # This will fail initially until sanitization is implemented
        assert sanitized[0]["function"]["name"] == "invalid_tool_name_"
    
    @pytest.mark.asyncio
    async def test_streaming_completion(self):
        """Test streaming completion functionality."""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # Mock streaming response
            def mock_stream():
                chunk1 = Mock()
                chunk1.choices = [Mock()]
                chunk1.choices[0].delta = Mock()
                chunk1.choices[0].delta.content = "Hello"
                chunk1.choices[0].delta.tool_calls = []
                yield chunk1
                
                chunk2 = Mock()
                chunk2.choices = [Mock()]
                chunk2.choices[0].delta = Mock()
                chunk2.choices[0].delta.content = " world"
                chunk2.choices[0].delta.tool_calls = []
                yield chunk2
            
            mock_client.chat.completions.create.return_value = mock_stream()
            
            client = OpenAILLMClient(api_key="test-key")
            
            messages = [{"role": "user", "content": "Hello"}]
            stream = await client.create_completion(messages, stream=True)
            
            # This should fail initially until streaming is implemented
            chunks = []
            async for chunk in stream:
                chunks.append(chunk)
            
            assert len(chunks) == 2
            assert chunks[0]["response"] == "Hello"
            assert chunks[1]["response"] == " world"


class TestOpenAIStyleMixin:
    """Test the OpenAI style mixin functionality."""
    
    def test_tool_name_sanitization_regex(self):
        """Test the regex pattern for tool name sanitization."""
        from mcp_ghost.providers.openai_style_mixin import OpenAIStyleMixin
        
        tools = [
            {
                "function": {
                    "name": "valid_tool_name",
                    "description": "Valid name"
                }
            },
            {
                "function": {
                    "name": "invalid.tool@name#",
                    "description": "Invalid name"
                }
            }
        ]
        
        result = OpenAIStyleMixin._sanitize_tool_names(tools)
        
        # First tool should be unchanged
        assert result[0]["function"]["name"] == "valid_tool_name"
        
        # Second tool should be sanitized - this will fail initially
        assert result[1]["function"]["name"] == "invalid_tool_name_"
    
    def test_normalize_message_format(self):
        """Test message normalization."""
        from mcp_ghost.providers.openai_style_mixin import OpenAIStyleMixin
        
        # Mock message with tool calls
        mock_message = Mock()
        mock_message.content = "Test response"
        mock_message.tool_calls = None
        
        result = OpenAIStyleMixin._normalise_message(mock_message)
        
        assert result["response"] == "Test response"
        assert result["tool_calls"] == []
        
        # Test with tool calls - this will fail initially
        mock_tool_call = Mock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "test_func"
        mock_tool_call.function.arguments = '{"test": "value"}'
        
        mock_message.tool_calls = [mock_tool_call]
        mock_message.content = None
        
        result = OpenAIStyleMixin._normalise_message(mock_message)
        
        assert result["response"] is None
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["function"]["name"] == "test_func"