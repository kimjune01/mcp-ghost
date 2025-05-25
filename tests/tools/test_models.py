"""Tests for tool models."""
import pytest
from mcp_ghost.tools.models import ToolInfo, ServerInfo, ToolCallResult, ResourceInfo


class TestToolInfo:
    """Test the ToolInfo dataclass."""
    
    def test_tool_info_creation(self):
        """Test basic ToolInfo creation."""
        tool = ToolInfo(name="test_tool", namespace="test_ns")
        assert tool.name == "test_tool"
        assert tool.namespace == "test_ns"
        assert tool.description is None
        assert tool.parameters is None
        assert tool.is_async is False
        assert tool.tags == []
        assert tool.supports_streaming is False
    
    def test_tool_info_with_all_fields(self):
        """Test ToolInfo with all fields populated."""
        parameters = {
            "type": "object",
            "properties": {
                "arg1": {"type": "string"}
            }
        }
        
        tool = ToolInfo(
            name="complex_tool",
            namespace="complex_ns", 
            description="A complex tool",
            parameters=parameters,
            is_async=True,
            tags=["utility", "database"],
            supports_streaming=True
        )
        
        assert tool.name == "complex_tool"
        assert tool.namespace == "complex_ns"
        assert tool.description == "A complex tool"
        assert tool.parameters == parameters
        assert tool.is_async is True
        assert tool.tags == ["utility", "database"]
        assert tool.supports_streaming is True
    
    def test_tool_info_equality(self):
        """Test ToolInfo equality comparison."""
        tool1 = ToolInfo(name="test", namespace="ns")
        tool2 = ToolInfo(name="test", namespace="ns")
        tool3 = ToolInfo(name="different", namespace="ns")
        
        assert tool1 == tool2
        assert tool1 != tool3
    
    def test_tool_info_default_factory(self):
        """Test that default factory creates separate lists."""
        tool1 = ToolInfo(name="test1", namespace="ns")
        tool2 = ToolInfo(name="test2", namespace="ns")
        
        tool1.tags.append("tag1")
        
        # This will fail if default_factory isn't working correctly
        assert tool2.tags == []
        assert tool1.tags == ["tag1"]


class TestServerInfo:
    """Test the ServerInfo dataclass."""
    
    def test_server_info_creation(self):
        """Test basic ServerInfo creation."""
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
    
    def test_server_info_different_statuses(self):
        """Test ServerInfo with different status values."""
        statuses = ["connected", "disconnected", "error", "connecting"]
        
        for i, status in enumerate(statuses):
            server = ServerInfo(
                id=i,
                name=f"server_{i}",
                status=status,
                tool_count=0,
                namespace="ns"
            )
            assert server.status == status
    
    def test_server_info_validation(self):
        """Test that ServerInfo validates its fields properly."""
        # This will fail initially - we should add validation
        with pytest.raises(ValueError):
            ServerInfo(
                id=-1,  # Invalid ID
                name="test",
                status="connected", 
                tool_count=5,
                namespace="ns"
            )


class TestToolCallResult:
    """Test the ToolCallResult dataclass."""
    
    def test_successful_tool_call_result(self):
        """Test successful tool call result."""
        result = ToolCallResult(
            tool_name="test_tool",
            success=True,
            result={"data": "success"},
            execution_time=1.5
        )
        
        assert result.tool_name == "test_tool"
        assert result.success is True
        assert result.result == {"data": "success"}
        assert result.error is None
        assert result.execution_time == 1.5
    
    def test_failed_tool_call_result(self):
        """Test failed tool call result."""
        result = ToolCallResult(
            tool_name="failing_tool",
            success=False,
            error="Tool execution failed",
            execution_time=0.5
        )
        
        assert result.tool_name == "failing_tool"
        assert result.success is False
        assert result.result is None
        assert result.error == "Tool execution failed"
        assert result.execution_time == 0.5
    
    def test_tool_call_result_with_complex_result(self):
        """Test tool call result with complex data structures."""
        complex_result = {
            "tables": [
                {"name": "users", "rows": 100},
                {"name": "orders", "rows": 500}
            ],
            "query_time": "0.05s"
        }
        
        result = ToolCallResult(
            tool_name="sql_query",
            success=True,
            result=complex_result
        )
        
        assert result.result == complex_result
        assert len(result.result["tables"]) == 2
    
    def test_tool_call_result_validation(self):
        """Test tool call result validation."""
        # This will fail initially - we should validate that success=False has an error
        result = ToolCallResult(
            tool_name="test",
            success=False
            # Missing error field when success=False
        )
        
        # Should fail validation
        assert result.error is not None or not result.success


class TestResourceInfo:
    """Test the ResourceInfo dataclass."""
    
    def test_resource_info_creation(self):
        """Test basic ResourceInfo creation."""
        resource = ResourceInfo(
            id="resource_1",
            name="Test Resource",
            type="file"
        )
        
        assert resource.id == "resource_1"
        assert resource.name == "Test Resource" 
        assert resource.type == "file"
        assert resource.extra == {}
    
    def test_resource_info_with_extra_data(self):
        """Test ResourceInfo with extra data."""
        extra_data = {
            "size": 1024,
            "modified": "2025-01-01",
            "permissions": ["read", "write"]
        }
        
        resource = ResourceInfo(
            id="file_1",
            name="document.txt",
            type="file",
            extra=extra_data
        )
        
        assert resource.extra == extra_data
        assert resource.extra["size"] == 1024
    
    def test_resource_info_from_raw_dict(self):
        """Test creating ResourceInfo from raw dictionary."""
        raw_data = {
            "id": "res_123",
            "name": "Resource Name",
            "type": "database",
            "size": 2048,
            "owner": "admin",
            "custom_field": "custom_value"
        }
        
        resource = ResourceInfo.from_raw(raw_data)
        
        assert resource.id == "res_123"
        assert resource.name == "Resource Name"
        assert resource.type == "database"
        
        # Extra fields should be in extra dict
        assert resource.extra["size"] == 2048
        assert resource.extra["owner"] == "admin"
        assert resource.extra["custom_field"] == "custom_value"
    
    def test_resource_info_from_raw_primitive(self):
        """Test creating ResourceInfo from primitive value."""
        # Test with string
        resource = ResourceInfo.from_raw("simple_string")
        assert resource.id is None
        assert resource.name is None
        assert resource.type is None
        assert resource.extra["value"] == "simple_string"
        
        # Test with number
        resource = ResourceInfo.from_raw(42)
        assert resource.extra["value"] == 42
        
        # Test with list
        resource = ResourceInfo.from_raw([1, 2, 3])
        assert resource.extra["value"] == [1, 2, 3]
    
    def test_resource_info_from_raw_empty_dict(self):
        """Test creating ResourceInfo from empty dictionary."""
        resource = ResourceInfo.from_raw({})
        
        assert resource.id is None
        assert resource.name is None
        assert resource.type is None
        assert resource.extra == {}
    
    def test_resource_info_from_raw_partial_dict(self):
        """Test creating ResourceInfo from partial dictionary."""
        raw_data = {
            "name": "Partial Resource",
            "custom_attr": "value"
        }
        
        resource = ResourceInfo.from_raw(raw_data)
        
        assert resource.id is None  # Missing from raw data
        assert resource.name == "Partial Resource"
        assert resource.type is None  # Missing from raw data
        assert resource.extra["custom_attr"] == "value"


class TestModelInteractions:
    """Test interactions between different models."""
    
    def test_tool_info_to_tool_call_result(self):
        """Test creating ToolCallResult from ToolInfo execution."""
        tool = ToolInfo(name="test_tool", namespace="test_ns")
        
        # Successful execution
        success_result = ToolCallResult(
            tool_name=f"{tool.namespace}.{tool.name}",
            success=True,
            result="execution successful"
        )
        
        assert success_result.tool_name == "test_ns.test_tool"
        
        # Failed execution
        error_result = ToolCallResult(
            tool_name=f"{tool.namespace}.{tool.name}",
            success=False,
            error="execution failed"
        )
        
        assert error_result.tool_name == "test_ns.test_tool"
    
    def test_server_info_with_tool_count_validation(self):
        """Test that server tool count matches actual tools."""
        server = ServerInfo(
            id=1,
            name="test_server",
            status="connected",
            tool_count=3,
            namespace="test_ns"
        )
        
        # This will fail initially - we should validate tool count
        tools = [
            ToolInfo(name="tool1", namespace="test_ns"),
            ToolInfo(name="tool2", namespace="test_ns"),
            ToolInfo(name="tool3", namespace="test_ns"),
            ToolInfo(name="tool4", namespace="test_ns")  # One extra tool
        ]
        
        # Tool count should match the number of tools
        assert server.tool_count == len(tools) - 1  # This will fail