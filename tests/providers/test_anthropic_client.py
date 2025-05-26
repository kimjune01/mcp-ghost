"""Tests for Anthropic LLM client."""
import pytest
import os
from unittest.mock import Mock, patch
from mcp_ghost.providers.anthropic_client import AnthropicLLMClient
from tests.goldens.golden_framework import GoldenRecorder, MockLLMClient
from dotenv import load_dotenv

# Load environment variables for testing
load_dotenv()


class TestAnthropicLLMClient:
    """Test Anthropic client implementation."""
    
    def test_client_initialization(self):
        """Test that Anthropic client initializes correctly."""
        client = AnthropicLLMClient(api_key="test-key")
        assert client is not None
        assert client.model == "claude-3-sonnet-20250219"  # default model
        
        # Test custom model
        client = AnthropicLLMClient(model="claude-3-opus", api_key="test-key")
        assert client.model == "claude-3-opus"
    
    def test_client_requires_api_key(self):
        """Test that client requires an API key."""
        # This should fail initially if no validation exists
        with pytest.raises(ValueError):
            AnthropicLLMClient(api_key=None)
    
    def test_convert_tools_to_anthropic_format(self):
        """Test conversion of OpenAI-style tools to Anthropic format."""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "test_function",
                    "description": "A test function",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "arg1": {"type": "string"}
                        }
                    }
                }
            }
        ]
        
        converted = AnthropicLLMClient._convert_tools(tools)
        
        # This will fail initially until conversion is properly implemented
        assert len(converted) == 1
        assert converted[0]["name"] == "test_function"
        assert converted[0]["description"] == "A test function"
        assert "input_schema" in converted[0]
        assert converted[0]["input_schema"]["type"] == "object"
    
    def test_split_messages_for_anthropic(self):
        """Test message splitting for Anthropic format."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {
                "role": "assistant", 
                "tool_calls": [
                    {
                        "id": "call_123",
                        "function": {
                            "name": "test_func",
                            "arguments": '{"arg": "value"}'
                        }
                    }
                ]
            },
            {
                "role": "tool",
                "tool_call_id": "call_123",
                "content": "Tool result"
            }
        ]
        
        system_text, anthropic_messages = AnthropicLLMClient._split_for_anthropic(messages)
        
        # This will fail initially until proper message splitting is implemented
        assert system_text == "You are a helpful assistant"
        assert len(anthropic_messages) == 4  # user, assistant, assistant w/ tools, tool result
        
        # Check tool use format
        tool_message = None
        for msg in anthropic_messages:
            if msg.get("role") == "assistant" and isinstance(msg.get("content"), list):
                tool_message = msg
                break
        
        assert tool_message is not None
        assert tool_message["content"][0]["type"] == "tool_use"
        assert tool_message["content"][0]["name"] == "test_func"
    
    @pytest.mark.asyncio
    async def test_create_completion_basic(self):
        """Test basic completion creation."""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            pytest.skip("ANTHROPIC_API_KEY not found in environment")
        
        # Create golden recorder
        recorder = GoldenRecorder("test_create_completion_basic", "anthropic")
        
        # Set input data for golden recording
        recorder.set_input(
            server_config={},
            system_prompt="You are a helpful assistant.",
            user_prompt="Say hello in exactly 3 words",
            model="claude-3-5-sonnet-20241022"
        )
        
        if recorder.record_mode:
            # Record mode: make actual API call
            client = AnthropicLLMClient(api_key=api_key)
            messages = [{"role": "user", "content": "Say hello in exactly 3 words"}]
            
            # Record the request
            request_data = {
                "messages": messages,
                "model": "claude-3-5-sonnet-20241022",
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
                "summary": "Basic Anthropic completion test",
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
        """Test completion with tool calls."""
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.return_value = mock_client
            
            # Mock tool use response
            mock_tool_block = Mock()
            mock_tool_block.type = "tool_use"
            mock_tool_block.id = "call_123"
            mock_tool_block.name = "test_function"
            mock_tool_block.input = {"arg": "value"}
            
            mock_response = Mock()
            mock_response.content = [mock_tool_block]
            
            mock_client.messages.create.return_value = mock_response
            
            client = AnthropicLLMClient(api_key="test-key")
            
            messages = [{"role": "user", "content": "Use tools"}]
            tools = [{"name": "test_function", "description": "Test tool"}]
            
            result = await client.create_completion(messages, tools)
            
            # This should fail initially until tool call parsing is implemented
            assert result["response"] is None
            assert len(result["tool_calls"]) == 1
            assert result["tool_calls"][0]["function"]["name"] == "test_function"
    
    def test_system_prompt_handling(self):
        """Test that system prompts are handled correctly."""
        messages = [
            {"role": "system", "content": "System instruction"},
            {"role": "user", "content": "User message"}
        ]
        
        system_text, claude_messages = AnthropicLLMClient._split_for_anthropic(messages)
        
        # System message should be extracted
        assert system_text == "System instruction"
        
        # Only user message should remain in claude_messages
        assert len(claude_messages) == 1
        assert claude_messages[0]["role"] == "user"
        assert claude_messages[0]["content"][0]["text"] == "User message"
    
    def test_empty_system_prompt_handling(self):
        """Test handling when no system prompt is provided."""
        messages = [{"role": "user", "content": "User message"}]
        
        system_text, claude_messages = AnthropicLLMClient._split_for_anthropic(messages)
        
        # This will fail initially - should return empty string, not None
        assert system_text == ""
        assert len(claude_messages) == 1


class TestAnthropicHelperFunctions:
    """Test helper functions for Anthropic client."""
    
    def test_safe_get_function(self):
        """Test the _safe_get helper function."""
        from mcp_ghost.providers.anthropic_client import _safe_get
        
        # Test with dict
        test_dict = {"key": "value"}
        assert _safe_get(test_dict, "key") == "value"
        assert _safe_get(test_dict, "missing", "default") == "default"
        
        # Test with object
        test_obj = Mock()
        test_obj.attr = "value"
        assert _safe_get(test_obj, "attr") == "value"
        assert _safe_get(test_obj, "missing", "default") == "default"
    
    def test_parse_claude_response_text_only(self):
        """Test parsing Claude response with text only."""
        from mcp_ghost.providers.anthropic_client import _parse_claude_response
        
        mock_response = Mock()
        mock_content = Mock()
        mock_content.text = "Hello world"
        mock_response.content = [mock_content]
        
        result = _parse_claude_response(mock_response)
        
        assert result["response"] == "Hello world"
        assert result["tool_calls"] == []
    
    def test_parse_claude_response_with_tools(self):
        """Test parsing Claude response with tool calls."""
        from mcp_ghost.providers.anthropic_client import _parse_claude_response
        
        mock_response = Mock()
        mock_tool_block = Mock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.id = "call_123"
        mock_tool_block.name = "test_func"
        mock_tool_block.input = {"arg": "value"}
        
        mock_response.content = [mock_tool_block]
        
        result = _parse_claude_response(mock_response)
        
        # This will fail initially until tool parsing is implemented correctly
        assert result["response"] is None
        assert len(result["tool_calls"]) == 1
        tool_call = result["tool_calls"][0]
        assert tool_call["id"] == "call_123"
        assert tool_call["function"]["name"] == "test_func"
        assert '"arg": "value"' in tool_call["function"]["arguments"]