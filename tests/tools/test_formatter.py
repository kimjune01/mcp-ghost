"""Tests for tool formatter."""
import pytest
import json
from mcp_ghost.tools.formatter import (
    format_tool_for_openai,
    format_tool_response,
    format_tool_call_result,
    format_tools_for_provider
)
from mcp_ghost.tools.models import ToolInfo, ToolCallResult


class TestFormatToolForOpenAI:
    """Test formatting tools for OpenAI function calling."""
    
    def test_basic_tool_formatting(self):
        """Test basic tool formatting for OpenAI."""
        tool = ToolInfo(
            name="test_tool",
            namespace="test_ns",
            description="A test tool",
            parameters={
                "type": "object",
                "properties": {
                    "arg1": {"type": "string", "description": "First argument"}
                },
                "required": ["arg1"]
            }
        )
        
        result = format_tool_for_openai(tool)
        
        assert result["type"] == "function"
        assert result["function"]["name"] == "test_tool"
        assert result["function"]["description"] == "A test tool"
        assert result["function"]["parameters"] == tool.parameters
    
    def test_tool_without_description(self):
        """Test formatting tool without description."""
        tool = ToolInfo(name="simple_tool", namespace="ns")
        
        result = format_tool_for_openai(tool)
        
        assert result["function"]["description"] == ""
        assert result["function"]["parameters"] == {"type": "object", "properties": {}}
    
    def test_tool_without_parameters(self):
        """Test formatting tool without parameters."""
        tool = ToolInfo(
            name="param_less_tool",
            namespace="ns",
            description="Tool without params"
        )
        
        result = format_tool_for_openai(tool)
        
        assert result["function"]["parameters"] == {"type": "object", "properties": {}}
    
    def test_tool_with_complex_parameters(self):
        """Test formatting tool with complex parameter schema."""
        complex_params = {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL query to execute"
                },
                "options": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "minimum": 1},
                        "timeout": {"type": "number", "default": 30.0}
                    }
                },
                "tables": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["query"]
        }
        
        tool = ToolInfo(
            name="sql_query",
            namespace="database",
            parameters=complex_params
        )
        
        result = format_tool_for_openai(tool)
        
        assert result["function"]["parameters"] == complex_params
        assert "properties" in result["function"]["parameters"]
        assert "query" in result["function"]["parameters"]["properties"]


class TestFormatToolResponse:
    """Test formatting tool responses."""
    
    def test_format_string_response(self):
        """Test formatting simple string response."""
        response = "Simple string response"
        result = format_tool_response(response)
        assert result == "Simple string response"
    
    def test_format_dict_response(self):
        """Test formatting dictionary response."""
        response = {"key": "value", "number": 42}
        result = format_tool_response(response)
        
        # Should be JSON formatted
        parsed = json.loads(result)
        assert parsed == response
        assert "key" in result
        assert "42" in result
    
    def test_format_list_response(self):
        """Test formatting list response."""
        response = [{"id": 1, "name": "item1"}, {"id": 2, "name": "item2"}]
        result = format_tool_response(response)
        
        parsed = json.loads(result)
        assert parsed == response
        assert len(parsed) == 2
    
    def test_format_text_records_response(self):
        """Test formatting list of text records."""
        response = [
            {"type": "text", "text": "Line 1"},
            {"type": "text", "text": "Line 2"},
            {"type": "text", "text": "Line 3"}
        ]
        
        result = format_tool_response(response)
        
        # Should join text content, not JSON serialize
        assert result == "Line 1\nLine 2\nLine 3"
        assert "type" not in result  # Should not contain the structure
    
    def test_format_mixed_list_response(self):
        """Test formatting list with mixed content."""
        response = [
            {"type": "text", "text": "Text item"},
            {"id": 1, "data": "Non-text item"}
        ]
        
        result = format_tool_response(response)
        
        # Should JSON serialize since not all items are text records
        parsed = json.loads(result)
        assert parsed == response
    
    def test_format_non_serializable_response(self):
        """Test formatting response that can't be JSON serialized."""
        class NonSerializable:
            def __str__(self):
                return "non-serializable object"
        
        response = {"data": NonSerializable()}
        result = format_tool_response(response)
        
        # Should fall back to string representation
        assert "non-serializable object" in result
    
    def test_format_none_response(self):
        """Test formatting None response."""
        result = format_tool_response(None)
        assert result == "None"
    
    def test_format_number_response(self):
        """Test formatting numeric response."""
        result = format_tool_response(42)
        assert result == "42"
        
        result = format_tool_response(3.14)
        assert result == "3.14"
    
    def test_format_empty_responses(self):
        """Test formatting empty responses."""
        assert format_tool_response([]) == "[]"
        assert format_tool_response({}) == "{}"
        assert format_tool_response("") == ""


class TestFormatToolCallResult:
    """Test formatting tool call results."""
    
    def test_format_successful_result(self):
        """Test formatting successful tool call result."""
        result = ToolCallResult(
            tool_name="test_tool",
            success=True,
            result={"data": "success"}
        )
        
        formatted = format_tool_call_result(result)
        
        # Should format the result data
        parsed = json.loads(formatted)
        assert parsed == {"data": "success"}
    
    def test_format_failed_result(self):
        """Test formatting failed tool call result."""
        result = ToolCallResult(
            tool_name="failing_tool",
            success=False,
            error="Tool execution failed"
        )
        
        formatted = format_tool_call_result(result)
        
        assert formatted == "Error: Tool execution failed"
    
    def test_format_failed_result_no_error(self):
        """Test formatting failed result without error message."""
        result = ToolCallResult(
            tool_name="failing_tool",
            success=False
        )
        
        formatted = format_tool_call_result(result)
        
        assert formatted == "Error: Unknown error"
    
    def test_format_result_with_complex_data(self):
        """Test formatting result with complex data structure."""
        complex_data = {
            "tables": [
                {"name": "users", "rows": 100},
                {"name": "orders", "rows": 500}
            ],
            "query_time": "0.05s",
            "metadata": {
                "database": "production",
                "version": "1.0"
            }
        }
        
        result = ToolCallResult(
            tool_name="sql_query",
            success=True,
            result=complex_data
        )
        
        formatted = format_tool_call_result(result)
        parsed = json.loads(formatted)
        
        assert parsed == complex_data
        assert len(parsed["tables"]) == 2
        assert "query_time" in formatted


class TestFormatToolsForProvider:
    """Test formatting tools for different providers."""
    
    def test_format_tools_for_openai(self):
        """Test formatting tools specifically for OpenAI."""
        tools = [
            ToolInfo(name="tool1", namespace="ns1", description="First tool"),
            ToolInfo(name="tool2", namespace="ns2", description="Second tool")
        ]
        
        result = format_tools_for_provider(tools, "openai")
        
        assert len(result) == 2
        assert all(tool["type"] == "function" for tool in result)
        assert result[0]["function"]["name"] == "tool1"
        assert result[1]["function"]["name"] == "tool2"
    
    def test_format_tools_for_anthropic(self):
        """Test formatting tools for Anthropic."""
        tools = [
            ToolInfo(name="test_tool", namespace="test_ns", description="Test tool")
        ]
        
        result = format_tools_for_provider(tools, "anthropic")
        
        # Should use same format as OpenAI for now
        assert len(result) == 1
        assert result[0]["type"] == "function"
        assert result[0]["function"]["name"] == "test_tool"
    
    def test_format_tools_for_gemini(self):
        """Test formatting tools for Gemini."""
        tools = [
            ToolInfo(name="gemini_tool", namespace="gemini_ns")
        ]
        
        result = format_tools_for_provider(tools, "gemini")
        
        # Should use same format as OpenAI for now
        assert len(result) == 1
        assert result[0]["type"] == "function"
        assert result[0]["function"]["name"] == "gemini_tool"
    
    def test_format_tools_for_unknown_provider(self):
        """Test formatting tools for unknown provider."""
        tools = [
            ToolInfo(name="any_tool", namespace="any_ns")
        ]
        
        result = format_tools_for_provider(tools, "unknown_provider")
        
        # Should default to OpenAI format
        assert len(result) == 1
        assert result[0]["type"] == "function"
    
    def test_format_empty_tools_list(self):
        """Test formatting empty tools list."""
        result = format_tools_for_provider([], "openai")
        assert result == []
    
    def test_format_tools_case_insensitive_provider(self):
        """Test that provider name is case insensitive."""
        tools = [ToolInfo(name="test", namespace="ns")]
        
        result1 = format_tools_for_provider(tools, "OpenAI")
        result2 = format_tools_for_provider(tools, "OPENAI")
        result3 = format_tools_for_provider(tools, "openai")
        
        # All should produce the same result
        assert result1 == result2 == result3
    
    def test_format_tools_preserves_all_data(self):
        """Test that formatting preserves all tool data."""
        complex_tool = ToolInfo(
            name="complex_tool",
            namespace="complex_ns",
            description="A complex tool with many features",
            parameters={
                "type": "object",
                "properties": {
                    "required_param": {"type": "string"},
                    "optional_param": {"type": "integer", "default": 42}
                },
                "required": ["required_param"]
            },
            is_async=True,
            tags=["database", "query"],
            supports_streaming=True
        )
        
        result = format_tools_for_provider([complex_tool], "openai")
        
        formatted_tool = result[0]
        
        assert formatted_tool["function"]["name"] == "complex_tool"
        assert formatted_tool["function"]["description"] == "A complex tool with many features"
        assert formatted_tool["function"]["parameters"] == complex_tool.parameters
        
        # Note: is_async, tags, supports_streaming are not part of OpenAI format
        # This documents current behavior
        assert "is_async" not in formatted_tool["function"]
        assert "tags" not in formatted_tool["function"]


class TestFormatterEdgeCases:
    """Test edge cases for formatting functions."""
    
    def test_format_tool_with_none_values(self):
        """Test formatting tool with None values."""
        tool = ToolInfo(
            name="partial_tool",
            namespace="ns",
            description=None,
            parameters=None
        )
        
        result = format_tool_for_openai(tool)
        
        assert result["function"]["description"] == ""
        assert result["function"]["parameters"] == {"type": "object", "properties": {}}
    
    def test_format_response_with_circular_reference(self):
        """Test formatting response with circular references."""
        # This will fail initially - need to handle circular refs
        data = {"key": "value"}
        data["self"] = data  # Circular reference
        
        result = format_tool_response(data)
        
        # Should handle gracefully, not crash
        assert isinstance(result, str)
        # Can't JSON serialize circular refs, should fall back to str()
        assert "key" in result or "circular" in result.lower()
    
    def test_format_very_large_response(self):
        """Test formatting very large response."""
        # Create a large data structure
        large_data = {"data": ["item"] * 10000}
        
        result = format_tool_response(large_data)
        
        # Should handle large data without issues
        parsed = json.loads(result)
        assert len(parsed["data"]) == 10000
    
    def test_format_response_with_special_characters(self):
        """Test formatting response with special characters."""
        response = {
            "unicode": "Hello 世界 🌍",
            "quotes": 'Text with "quotes" and \'apostrophes\'',
            "newlines": "Line 1\nLine 2\rLine 3",
            "escapes": "\\backslash\ttab"
        }
        
        result = format_tool_response(response)
        parsed = json.loads(result)
        
        assert parsed == response
        assert "世界" in result
        assert "🌍" in result