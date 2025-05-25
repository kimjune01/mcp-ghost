"""Tests for tools module interfaces."""
import pytest
from mcp_ghost.tools import (
    ToolInfo, 
    ServerInfo, 
    ToolCallResult, 
    ResourceInfo,
    ToolNameAdapter,
    format_tool_for_openai,
    format_tool_response,
    format_tools_for_provider
)


class TestToolsModuleInterface:
    """Test the tools module interface."""
    
    def test_module_exports_all_models(self):
        """Test that tools module exports all expected models."""
        import mcp_ghost.tools as tools
        
        # Should export all model classes
        assert hasattr(tools, 'ToolInfo')
        assert hasattr(tools, 'ServerInfo')
        assert hasattr(tools, 'ToolCallResult')
        assert hasattr(tools, 'ResourceInfo')
        
        # Should export adapter and formatter utilities
        assert hasattr(tools, 'ToolNameAdapter')
        assert hasattr(tools, 'format_tool_for_openai')
        assert hasattr(tools, 'format_tool_response')
        assert hasattr(tools, 'format_tools_for_provider')
    
    def test_all_models_are_dataclasses(self):
        """Test that all model classes are proper dataclasses."""
        import dataclasses
        
        models = [ToolInfo, ServerInfo, ToolCallResult, ResourceInfo]
        
        for model in models:
            assert dataclasses.is_dataclass(model)
            # Should be able to create instances
            fields = dataclasses.fields(model)
            assert len(fields) > 0


class TestToolInfoInterface:
    """Test ToolInfo model interface."""
    
    def test_tool_info_required_fields(self):
        """Test ToolInfo has required name and namespace fields."""
        tool = ToolInfo(name="test_tool", namespace="test_ns")
        assert tool.name == "test_tool"
        assert tool.namespace == "test_ns"
    
    def test_tool_info_optional_fields(self):
        """Test ToolInfo optional fields have proper defaults."""
        tool = ToolInfo(name="test", namespace="ns")
        
        # These should have sensible defaults
        assert tool.description is None
        assert tool.parameters is None
        assert tool.is_async is False
        assert tool.tags == []
        assert tool.supports_streaming is False
    
    def test_tool_info_equality(self):
        """Test ToolInfo equality comparison works."""
        tool1 = ToolInfo(name="test", namespace="ns")
        tool2 = ToolInfo(name="test", namespace="ns")
        tool3 = ToolInfo(name="different", namespace="ns")
        
        assert tool1 == tool2
        assert tool1 != tool3


class TestServerInfoInterface:
    """Test ServerInfo model interface."""
    
    def test_server_info_creation(self):
        """Test ServerInfo can be created with required fields."""
        server = ServerInfo(
            id=1,
            name="test_server",
            status="connected",
            tool_count=5,
            namespace="test_ns"
        )
        
        assert server.id == 1
        assert server.name == "test_server"
        assert server.status == "connected"
        assert server.tool_count == 5
        assert server.namespace == "test_ns"


class TestToolCallResultInterface:
    """Test ToolCallResult model interface."""
    
    def test_tool_call_result_success(self):
        """Test successful tool call result structure."""
        result = ToolCallResult(
            tool_name="test_tool",
            success=True,
            result={"data": "value"}
        )
        
        assert result.tool_name == "test_tool"
        assert result.success is True
        assert result.result == {"data": "value"}
        assert result.error is None
    
    def test_tool_call_result_failure(self):
        """Test failed tool call result structure."""
        result = ToolCallResult(
            tool_name="failing_tool",
            success=False,
            error="Execution failed"
        )
        
        assert result.success is False
        assert result.error == "Execution failed"
        assert result.result is None


class TestResourceInfoInterface:
    """Test ResourceInfo model interface."""
    
    def test_resource_info_creation(self):
        """Test ResourceInfo can be created."""
        resource = ResourceInfo(
            id="res_1",
            name="Test Resource",
            type="file"
        )
        
        assert resource.id == "res_1"
        assert resource.name == "Test Resource"
        assert resource.type == "file"
        assert resource.extra == {}
    
    def test_resource_info_from_raw_interface(self):
        """Test ResourceInfo.from_raw class method interface."""
        # Should handle dictionary input
        raw_dict = {"id": "test", "name": "Test", "custom": "value"}
        resource = ResourceInfo.from_raw(raw_dict)
        
        assert resource.id == "test"
        assert resource.name == "Test"
        assert resource.extra["custom"] == "value"
        
        # Should handle primitive input
        resource = ResourceInfo.from_raw("simple_value")
        assert resource.extra["value"] == "simple_value"


class TestToolNameAdapterInterface:
    """Test ToolNameAdapter interface."""
    
    def test_adapter_has_required_methods(self):
        """Test that ToolNameAdapter has all required methods."""
        # Should have provider-specific conversion methods
        assert hasattr(ToolNameAdapter, 'to_openai_compatible')
        assert hasattr(ToolNameAdapter, 'to_anthropic_compatible')
        assert hasattr(ToolNameAdapter, 'to_gemini_compatible')
        assert hasattr(ToolNameAdapter, 'from_openai_compatible')
        
        # Should have generic adapter method
        assert hasattr(ToolNameAdapter, 'adapt_for_provider')
        
        # Should have mapping builder
        assert hasattr(ToolNameAdapter, 'build_mapping')
        
        # All should be static methods
        assert callable(ToolNameAdapter.to_openai_compatible)
        assert callable(ToolNameAdapter.adapt_for_provider)
        assert callable(ToolNameAdapter.build_mapping)
    
    def test_adapter_openai_conversion(self):
        """Test OpenAI name conversion interface."""
        result = ToolNameAdapter.to_openai_compatible("namespace", "tool_name")
        assert isinstance(result, str)
        assert "_" in result  # Should combine with underscore
    
    def test_adapter_provider_selection(self):
        """Test provider-specific adapter selection."""
        providers = ["openai", "anthropic", "gemini"]
        
        for provider in providers:
            result = ToolNameAdapter.adapt_for_provider("ns", "tool", provider)
            assert isinstance(result, str)
    
    def test_adapter_mapping_builder(self):
        """Test mapping builder interface."""
        tools = [
            ToolInfo(name="tool1", namespace="ns1"),
            ToolInfo(name="tool2", namespace="ns2")
        ]
        
        mapping = ToolNameAdapter.build_mapping(tools, "openai")
        
        assert isinstance(mapping, dict)
        assert len(mapping) == 2
        # Should map provider names to original names
        for provider_name, original_name in mapping.items():
            assert isinstance(provider_name, str)
            assert isinstance(original_name, str)
            assert "." in original_name  # Original should have namespace.tool format


class TestFormatterInterface:
    """Test formatter functions interface."""
    
    def test_format_tool_for_openai_interface(self):
        """Test format_tool_for_openai interface."""
        tool = ToolInfo(name="test_tool", namespace="ns", description="Test")
        
        result = format_tool_for_openai(tool)
        
        # Should return OpenAI function format
        assert isinstance(result, dict)
        assert "type" in result
        assert result["type"] == "function"
        assert "function" in result
        assert "name" in result["function"]
        assert "description" in result["function"]
        assert "parameters" in result["function"]
    
    def test_format_tool_response_interface(self):
        """Test format_tool_response interface."""
        # Should handle various response types
        test_responses = [
            "string response",
            {"dict": "response"},
            [{"list": "response"}],
            42,
            None
        ]
        
        for response in test_responses:
            result = format_tool_response(response)
            assert isinstance(result, str)
    
    def test_format_tools_for_provider_interface(self):
        """Test format_tools_for_provider interface."""
        tools = [
            ToolInfo(name="tool1", namespace="ns1"),
            ToolInfo(name="tool2", namespace="ns2")
        ]
        
        providers = ["openai", "anthropic", "gemini"]
        
        for provider in providers:
            result = format_tools_for_provider(tools, provider)
            
            assert isinstance(result, list)
            assert len(result) == 2
            
            # Each tool should be properly formatted
            for formatted_tool in result:
                assert isinstance(formatted_tool, dict)
                assert "type" in formatted_tool
                assert "function" in formatted_tool


class TestToolsIntegration:
    """Test tools module integration points."""
    
    def test_tools_work_together(self):
        """Test that tools components work together properly."""
        # Create a tool
        tool = ToolInfo(
            name="complex@tool.name",
            namespace="special.namespace",
            description="A complex tool"
        )
        
        # Adapt name for OpenAI
        adapted_name = ToolNameAdapter.to_openai_compatible(tool.namespace, tool.name)
        
        # Format for provider
        formatted = format_tool_for_openai(tool)
        
        # Should work together
        assert isinstance(adapted_name, str)
        assert isinstance(formatted, dict)
        
        # The formatted tool should use the original name (not adapted)
        # This documents current behavior
        assert formatted["function"]["name"] == tool.name
    
    def test_result_formatting_integration(self):
        """Test tool result and formatting integration."""
        # Create a tool result
        result = ToolCallResult(
            tool_name="test_tool",
            success=True,
            result={"data": [1, 2, 3], "status": "complete"}
        )
        
        # Format the result
        formatted = format_tool_response(result.result)
        
        assert isinstance(formatted, str)
        # Should be valid JSON for dict results
        import json
        parsed = json.loads(formatted)
        assert parsed == result.result
    
    def test_end_to_end_tool_workflow(self):
        """Test complete tool workflow interface."""
        # This will fail initially - tests the complete workflow
        
        # 1. Create tool info
        tool = ToolInfo(name="sql_query", namespace="database")
        
        # 2. Format for provider
        openai_format = format_tool_for_openai(tool)
        
        # 3. Adapt name for provider
        adapted_name = ToolNameAdapter.adapt_for_provider(tool.namespace, tool.name, "openai")
        
        # 4. Create execution result
        execution_result = ToolCallResult(
            tool_name=f"{tool.namespace}.{tool.name}",
            success=True,
            result={"rows": [{"id": 1, "name": "test"}]}
        )
        
        # 5. Format result for LLM
        formatted_result = format_tool_response(execution_result.result)
        
        # All components should work together
        assert openai_format["function"]["name"] == tool.name
        assert adapted_name == "database_sql_query"
        assert execution_result.tool_name == "database.sql_query"
        assert "rows" in formatted_result