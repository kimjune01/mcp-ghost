"""Tests for OpenAI LLM client."""
import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from mcp_ghost.providers.openai_client import OpenAILLMClient
from tests.goldens.golden_framework import GoldenRecorder, MockLLMClient
from dotenv import load_dotenv

# Load environment variables for testing
load_dotenv()


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
        """Test basic completion creation with golden recording."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            pytest.skip("OPENAI_API_KEY not found in environment")
        
        # Create golden recorder for this test
        recorder = GoldenRecorder("test_create_completion_basic", "openai")
        
        # Set input data for golden recording
        recorder.set_input(
            server_config={},
            system_prompt="You are a helpful assistant.",
            user_prompt="Say hello in exactly 3 words",
            model="gpt-4o-mini"
        )
        
        if recorder.record_mode:
            # Record mode: make actual API call
            client = OpenAILLMClient(api_key=api_key)
            messages = [{"role": "user", "content": "Say hello in exactly 3 words"}]
            
            # Record the request
            request_data = {
                "messages": messages,
                "model": "gpt-4o-mini",
                "api_key": api_key
            }
            
            result = await client.create_completion(messages)
            
            # Record the provider interaction
            recorder.record_provider_interaction(
                request_data,
                result,
                {"total_tokens": 50, "prompt_tokens": 20, "completion_tokens": 30}
            )
            
            # Set golden output (for now, just the direct result)
            recorder.set_golden_output({
                "success": True,
                "final_result": result,
                "summary": "Basic completion test",
                "tool_chain": [],
                "conversation_history": [
                    {"role": "user", "content": "Say hello in exactly 3 words"},
                    {"role": "assistant", "content": result["response"]}
                ],
                "execution_metadata": {
                    "total_execution_time": 1.5,
                    "total_iterations": 1,
                    "token_usage": {"total_tokens": 50}
                }
            })
            
            # Save the golden file
            golden_path = recorder.save_golden()
            print(f"Saved golden file: {golden_path}")
        else:
            # Replay mode: use mock client
            mock_client = MockLLMClient(recorder)
            result = await mock_client.create_completion(
                messages=[{"role": "user", "content": "Say hello in exactly 3 words"}]
            )
        
        # Verify the result format
        assert "response" in result
        assert "tool_calls" in result
        assert isinstance(result["response"], str)
        assert isinstance(result["tool_calls"], list)
        # Basic sanity check on response
        assert len(result["response"]) > 0
    
    @pytest.mark.asyncio
    async def test_create_completion_with_tools(self):
        """Test completion with tool calls using golden framework."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            pytest.skip("OPENAI_API_KEY not found in environment")
            
        # Create golden recorder for this test
        recorder = GoldenRecorder("test_create_completion_with_tools", "openai")
        
        # Set input data for golden recording
        recorder.set_input(
            server_config={},
            system_prompt="You are a helpful assistant with access to tools.",
            user_prompt="Use tools to help me",
            model="gpt-4o-mini"
        )
        
        messages = [{"role": "user", "content": "Use tools to help me"}]
        tools = [{"type": "function", "function": {"name": "test_function", "description": "A test function"}}]
        
        if recorder.record_mode:
            # Record mode: make actual API call
            client = OpenAILLMClient(api_key=api_key)
            
            # Record the request
            request_data = {
                "messages": messages,
                "tools": tools,
                "model": "gpt-4o-mini",
                "api_key": api_key
            }
            
            result = await client.create_completion(messages, tools)
            
            # Record the provider interaction
            recorder.record_provider_interaction(
                request_data,
                result,
                {"total_tokens": 75, "prompt_tokens": 50, "completion_tokens": 25}
            )
            
            # Set golden output
            recorder.set_golden_output({
                "success": True,
                "final_result": result,
                "summary": "Tool completion test",
                "tool_chain": [],
                "conversation_history": [
                    {"role": "user", "content": "Use tools to help me"},
                    {"role": "assistant", "content": result["response"], "tool_calls": result["tool_calls"]}
                ],
                "execution_metadata": {
                    "total_execution_time": 2.0,
                    "total_iterations": 1,
                    "token_usage": {"total_tokens": 75}
                }
            })
            
            # Save the golden file
            golden_path = recorder.save_golden()
            print(f"Saved golden file: {golden_path}")
        else:
            # Replay mode: use mock client
            mock_client = MockLLMClient(recorder)
            result = await mock_client.create_completion(messages=messages, tools=tools)
        
        # Verify the result format
        assert "response" in result
        assert "tool_calls" in result
        assert isinstance(result["tool_calls"], list)
    
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
        """Test streaming completion functionality - placeholder for future implementation."""
        # Skip streaming tests for now as they require more complex golden recording
        pytest.skip("Streaming tests require advanced golden framework implementation")


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