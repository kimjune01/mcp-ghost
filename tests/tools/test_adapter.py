"""Tests for tool name adapter."""
import pytest
from mcp_ghost.tools.adapter import ToolNameAdapter
from mcp_ghost.tools.models import ToolInfo


class TestToolNameAdapter:
    """Test the ToolNameAdapter class."""
    
    def test_to_openai_compatible_basic(self):
        """Test basic OpenAI-compatible name conversion."""
        result = ToolNameAdapter.to_openai_compatible("sqlite", "list_tables")
        assert result == "sqlite_list_tables"
        
        result = ToolNameAdapter.to_openai_compatible("filesystem", "read_file")
        assert result == "filesystem_read_file"
    
    def test_to_openai_compatible_with_invalid_chars(self):
        """Test OpenAI name conversion with invalid characters."""
        # Test with dots
        result = ToolNameAdapter.to_openai_compatible("my.namespace", "tool.name")
        assert result == "my_namespace_tool_name"
        
        # Test with special characters
        result = ToolNameAdapter.to_openai_compatible("ns@special", "tool#name!")
        assert result == "ns_special_tool_name_"
        
        # Test with spaces
        result = ToolNameAdapter.to_openai_compatible("my namespace", "tool name")
        assert result == "my_namespace_tool_name"
    
    def test_to_openai_compatible_regex_compliance(self):
        """Test that OpenAI names match the required regex pattern."""
        import re
        openai_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
        
        test_cases = [
            ("sqlite", "list_tables"),
            ("complex.namespace", "complex-tool@name"),
            ("123numeric", "tool$with%symbols"),
            ("unicode🔧", "tool✨name"),
        ]
        
        for namespace, name in test_cases:
            result = ToolNameAdapter.to_openai_compatible(namespace, name)
            # This will fail initially if regex isn't properly implemented
            assert openai_pattern.match(result), f"'{result}' doesn't match OpenAI pattern"
    
    def test_to_anthropic_compatible(self):
        """Test Anthropic-compatible name conversion."""
        result = ToolNameAdapter.to_anthropic_compatible("sqlite", "list_tables")
        # Anthropic allows dots, so should preserve original format
        assert result == "sqlite.list_tables"
        
        result = ToolNameAdapter.to_anthropic_compatible("filesystem", "read_file")
        assert result == "filesystem.read_file"
    
    def test_to_gemini_compatible(self):
        """Test Gemini-compatible name conversion."""
        result = ToolNameAdapter.to_gemini_compatible("sqlite", "list_tables")
        assert result == "sqlite_list_tables"
        
        # Test with special characters
        result = ToolNameAdapter.to_gemini_compatible("ns.special", "tool@name")
        # This will fail initially until proper Gemini sanitization is implemented
        assert result == "ns_special_tool_name"
    
    def test_from_openai_compatible_basic(self):
        """Test converting OpenAI names back to MCP format."""
        result = ToolNameAdapter.from_openai_compatible("sqlite_list_tables")
        assert result == "sqlite.list_tables"
        
        result = ToolNameAdapter.from_openai_compatible("filesystem_read_file")
        assert result == "filesystem.read_file"
    
    def test_from_openai_compatible_no_underscore(self):
        """Test converting OpenAI names without underscore."""
        result = ToolNameAdapter.from_openai_compatible("simple_tool")
        assert result == "simple.tool"
        
        # Edge case: no underscore at all
        result = ToolNameAdapter.from_openai_compatible("tool")
        assert result == "tool"
    
    def test_from_openai_compatible_multiple_underscores(self):
        """Test converting OpenAI names with multiple underscores."""
        result = ToolNameAdapter.from_openai_compatible("complex_namespace_tool_name")
        # Should only split on first underscore
        assert result == "complex.namespace_tool_name"
    
    def test_adapt_for_provider_openai(self):
        """Test provider-specific adaptation for OpenAI."""
        result = ToolNameAdapter.adapt_for_provider("sqlite", "list_tables", "openai")
        assert result == "sqlite_list_tables"
        
        result = ToolNameAdapter.adapt_for_provider("ns.complex", "tool@name", "OPENAI")
        assert result == "ns_complex_tool_name"
    
    def test_adapt_for_provider_anthropic(self):
        """Test provider-specific adaptation for Anthropic."""
        result = ToolNameAdapter.adapt_for_provider("sqlite", "list_tables", "anthropic")
        assert result == "sqlite.list_tables"
        
        result = ToolNameAdapter.adapt_for_provider("filesystem", "read_file", "ANTHROPIC")
        assert result == "filesystem.read_file"
    
    def test_adapt_for_provider_gemini(self):
        """Test provider-specific adaptation for Gemini."""
        result = ToolNameAdapter.adapt_for_provider("sqlite", "list_tables", "gemini")
        assert result == "sqlite_list_tables"
        
        # This will fail initially until Gemini adaptation is properly implemented
        result = ToolNameAdapter.adapt_for_provider("ns.special", "tool@name", "gemini")
        assert result == "ns_special_tool_name"
    
    def test_adapt_for_provider_unknown(self):
        """Test provider-specific adaptation for unknown provider."""
        result = ToolNameAdapter.adapt_for_provider("sqlite", "list_tables", "unknown")
        # Should default to namespace.name format
        assert result == "sqlite.list_tables"
    
    def test_build_mapping_basic(self):
        """Test building tool name mapping."""
        tools = [
            ToolInfo(name="list_tables", namespace="sqlite"),
            ToolInfo(name="read_file", namespace="filesystem"),
            ToolInfo(name="complex@tool", namespace="special.ns")
        ]
        
        mapping = ToolNameAdapter.build_mapping(tools, "openai")
        
        expected = {
            "sqlite_list_tables": "sqlite.list_tables",
            "filesystem_read_file": "filesystem.read_file", 
            "special_ns_complex_tool": "special.ns.complex@tool"
        }
        
        # This will fail initially until mapping is properly implemented
        assert mapping == expected
    
    def test_build_mapping_different_providers(self):
        """Test building mappings for different providers."""
        tools = [
            ToolInfo(name="list_tables", namespace="sqlite"),
            ToolInfo(name="read_file", namespace="filesystem")
        ]
        
        openai_mapping = ToolNameAdapter.build_mapping(tools, "openai")
        anthropic_mapping = ToolNameAdapter.build_mapping(tools, "anthropic")
        
        # OpenAI uses underscores
        assert "sqlite_list_tables" in openai_mapping
        assert openai_mapping["sqlite_list_tables"] == "sqlite.list_tables"
        
        # Anthropic preserves dots
        assert "sqlite.list_tables" in anthropic_mapping
        assert anthropic_mapping["sqlite.list_tables"] == "sqlite.list_tables"
    
    def test_build_mapping_empty_tools(self):
        """Test building mapping with empty tools list."""
        mapping = ToolNameAdapter.build_mapping([], "openai")
        assert mapping == {}
    
    def test_round_trip_conversion(self):
        """Test that round-trip conversion works correctly."""
        original_namespace = "sqlite"
        original_name = "list_tables"
        original_full = f"{original_namespace}.{original_name}"
        
        # Convert to OpenAI format and back
        openai_name = ToolNameAdapter.to_openai_compatible(original_namespace, original_name)
        converted_back = ToolNameAdapter.from_openai_compatible(openai_name)
        
        assert converted_back == original_full
    
    def test_round_trip_with_special_chars(self):
        """Test round-trip conversion with special characters."""
        original_namespace = "complex.namespace"
        original_name = "tool@name"
        
        # Convert to OpenAI and back
        openai_name = ToolNameAdapter.to_openai_compatible(original_namespace, original_name)
        
        # This will fail initially - we lose information in the conversion
        # because special chars are replaced with underscores
        converted_back = ToolNameAdapter.from_openai_compatible(openai_name)
        
        # We can't perfectly round-trip when special chars are involved
        # This documents the limitation
        assert converted_back != f"{original_namespace}.{original_name}"
        assert "_" in converted_back  # Should contain sanitized version


class TestToolNameAdapterEdgeCases:
    """Test edge cases for ToolNameAdapter."""
    
    def test_empty_namespace_and_name(self):
        """Test handling of empty namespace and name."""
        result = ToolNameAdapter.to_openai_compatible("", "")
        assert result == "_"
        
        result = ToolNameAdapter.to_openai_compatible("namespace", "")
        assert result == "namespace_"
        
        result = ToolNameAdapter.to_openai_compatible("", "tool")
        assert result == "_tool"
    
    def test_very_long_names(self):
        """Test handling of very long tool names."""
        long_namespace = "a" * 100
        long_name = "b" * 100
        
        result = ToolNameAdapter.to_openai_compatible(long_namespace, long_name)
        
        # This will fail initially if we don't handle length limits
        # OpenAI might have limits on function name length
        assert len(result) <= 200  # Arbitrary limit for testing
        assert "_" in result  # Should still have the separator
    
    def test_numeric_names(self):
        """Test handling of numeric names."""
        result = ToolNameAdapter.to_openai_compatible("123", "456")
        assert result == "123_456"
        
        # Should be valid for OpenAI pattern
        import re
        openai_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
        assert openai_pattern.match(result)
    
    def test_unicode_handling(self):
        """Test handling of Unicode characters."""
        result = ToolNameAdapter.to_openai_compatible("测试", "工具")
        
        # This will fail initially - need to handle Unicode properly
        # Should replace non-ASCII chars with underscores
        assert all(ord(c) < 128 for c in result), "Result should be ASCII only"
        
        import re
        openai_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
        assert openai_pattern.match(result)
    
    def test_case_sensitivity(self):
        """Test case sensitivity in conversions."""
        result1 = ToolNameAdapter.to_openai_compatible("SQLite", "ListTables")
        result2 = ToolNameAdapter.to_openai_compatible("sqlite", "listtables")
        
        # Should preserve case
        assert result1 == "SQLite_ListTables"
        assert result2 == "sqlite_listtables"
        assert result1 != result2