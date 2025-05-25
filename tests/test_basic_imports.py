"""Test basic imports work correctly."""
import pytest
import sys
from pathlib import Path


class TestBasicImports:
    """Test that basic module structure exists."""
    
    def test_src_directory_exists(self):
        """Test that src directory exists."""
        src_path = Path(__file__).parent.parent / "src"
        assert src_path.exists(), "src directory should exist"
        assert src_path.is_dir(), "src should be a directory"
    
    def test_mcp_ghost_package_exists(self):
        """Test that mcp_ghost package directory exists."""
        package_path = Path(__file__).parent.parent / "src" / "mcp_ghost"
        assert package_path.exists(), "mcp_ghost package should exist"
        assert package_path.is_dir(), "mcp_ghost should be a directory"
        
        # Should have __init__.py
        init_file = package_path / "__init__.py"
        assert init_file.exists(), "mcp_ghost should have __init__.py"
    
    def test_submodule_directories_exist(self):
        """Test that expected submodule directories exist."""
        base_path = Path(__file__).parent.parent / "src" / "mcp_ghost"
        
        expected_dirs = ["providers", "tools", "utils"]
        for dir_name in expected_dirs:
            dir_path = base_path / dir_name
            assert dir_path.exists(), f"{dir_name} directory should exist"
            assert dir_path.is_dir(), f"{dir_name} should be a directory"
            
            # Should have __init__.py
            init_file = dir_path / "__init__.py"
            assert init_file.exists(), f"{dir_name} should have __init__.py"
    
    def test_core_files_exist(self):
        """Test that core files exist."""
        base_path = Path(__file__).parent.parent / "src" / "mcp_ghost"
        
        expected_files = ["core.py"]
        for file_name in expected_files:
            file_path = base_path / file_name
            assert file_path.exists(), f"{file_name} should exist"
            assert file_path.is_file(), f"{file_name} should be a file"
    
    def test_can_import_tools_module(self):
        """Test that tools module can be imported without external deps."""
        try:
            # This should work since tools module has minimal dependencies
            from mcp_ghost.tools.models import ToolInfo
            
            # Test basic instantiation
            tool = ToolInfo(name="test", namespace="test")
            assert tool.name == "test"
            assert tool.namespace == "test"
            
        except ImportError as e:
            pytest.fail(f"Cannot import tools.models: {e}")
    
    def test_can_import_tool_adapter(self):
        """Test that tool adapter can be imported."""
        try:
            from mcp_ghost.tools.adapter import ToolNameAdapter
            
            # Test basic functionality
            result = ToolNameAdapter.to_openai_compatible("test", "tool")
            assert isinstance(result, str)
            assert "test" in result
            assert "tool" in result
            
        except ImportError as e:
            pytest.fail(f"Cannot import tool adapter: {e}")
    
    def test_can_import_tool_formatter(self):
        """Test that tool formatter can be imported."""
        try:
            from mcp_ghost.tools.formatter import format_tool_response
            
            # Test basic functionality  
            result = format_tool_response("test response")
            assert result == "test response"
            
        except ImportError as e:
            pytest.fail(f"Cannot import tool formatter: {e}")
    
    def test_can_import_utils(self):
        """Test that utils can be imported."""
        try:
            from mcp_ghost.utils.prompt_generator import SystemPromptGenerator
            
            # Test basic instantiation
            generator = SystemPromptGenerator()
            assert hasattr(generator, 'template')
            
        except ImportError as e:
            pytest.fail(f"Cannot import utils: {e}")
    
    def test_provider_base_import(self):
        """Test that provider base can be imported."""
        try:
            from mcp_ghost.providers.base import BaseLLMClient
            
            # Should be abstract
            with pytest.raises(TypeError):
                BaseLLMClient()
                
        except ImportError as e:
            pytest.fail(f"Cannot import provider base: {e}")
    
    def test_main_package_import_succeeds(self):
        """Test that main package can be imported with basic functionality."""
        try:
            import mcp_ghost
            
            # Should have core classes available
            assert hasattr(mcp_ghost, 'MCPGhostConfig')
            assert hasattr(mcp_ghost, 'MCPGhostResult')
            assert hasattr(mcp_ghost, 'mcp_ghost')
            
        except ImportError as e:
            pytest.fail(f"Cannot import main package: {e}")


class TestModuleStructure:
    """Test the module structure is correct."""
    
    def test_tools_module_structure(self):
        """Test tools module has expected structure."""
        try:
            from mcp_ghost.tools import ToolInfo, ToolNameAdapter
            from mcp_ghost.tools.models import ServerInfo, ToolCallResult
            from mcp_ghost.tools.formatter import format_tool_for_openai
            
            # All should be importable
            assert ToolInfo is not None
            assert ToolNameAdapter is not None
            assert ServerInfo is not None
            assert ToolCallResult is not None
            assert format_tool_for_openai is not None
            
        except ImportError as e:
            pytest.fail(f"Tools module structure incorrect: {e}")
    
    def test_providers_module_structure(self):
        """Test providers module has expected files."""
        base_path = Path(__file__).parent.parent / "src" / "mcp_ghost" / "providers"
        
        expected_files = [
            "base.py",
            "openai_client.py", 
            "anthropic_client.py",
            "gemini_client.py",
            "client_factory.py",
            "openai_style_mixin.py"
        ]
        
        for file_name in expected_files:
            file_path = base_path / file_name
            assert file_path.exists(), f"providers/{file_name} should exist"
    
    def test_utils_module_structure(self):
        """Test utils module has expected files."""
        base_path = Path(__file__).parent.parent / "src" / "mcp_ghost" / "utils"
        
        expected_files = ["prompt_generator.py"]
        
        for file_name in expected_files:
            file_path = base_path / file_name
            assert file_path.exists(), f"utils/{file_name} should exist"