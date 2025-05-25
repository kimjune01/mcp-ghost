"""Tests for utils module interfaces."""
import pytest
from mcp_ghost.utils.prompt_generator import SystemPromptGenerator


class TestUtilsModuleInterface:
    """Test the utils module interface."""
    
    def test_module_exports_prompt_generator(self):
        """Test that utils module exports SystemPromptGenerator."""
        import mcp_ghost.utils as utils
        
        assert hasattr(utils, 'SystemPromptGenerator')
        
        # Should be a class that can be instantiated
        generator = utils.SystemPromptGenerator()
        assert isinstance(generator, SystemPromptGenerator)


class TestSystemPromptGeneratorInterface:
    """Test SystemPromptGenerator interface."""
    
    def test_generator_initialization(self):
        """Test SystemPromptGenerator can be initialized."""
        generator = SystemPromptGenerator()
        
        # Should have template and defaults
        assert hasattr(generator, 'template')
        assert hasattr(generator, 'default_user_system_prompt')
        assert hasattr(generator, 'default_tool_config')
        
        assert isinstance(generator.template, str)
        assert isinstance(generator.default_user_system_prompt, str)
        assert isinstance(generator.default_tool_config, str)
    
    def test_generate_prompt_interface(self):
        """Test generate_prompt method interface."""
        generator = SystemPromptGenerator()
        
        # Should have generate_prompt method
        assert hasattr(generator, 'generate_prompt')
        assert callable(generator.generate_prompt)
        
        # Test basic usage
        context = {"tools": []}
        result = generator.generate_prompt(context)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_generate_prompt_with_tools(self):
        """Test generate_prompt with tools."""
        generator = SystemPromptGenerator()
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "test_tool",
                    "description": "A test tool",
                    "parameters": {"type": "object"}
                }
            }
        ]
        
        context = {"tools": tools}
        result = generator.generate_prompt(context)
        
        # Should include tool information in prompt
        assert "test_tool" in result
        assert "A test tool" in result
    
    def test_generate_prompt_with_custom_prompts(self):
        """Test generate_prompt with custom system prompt."""
        generator = SystemPromptGenerator()
        
        context = {"tools": []}
        custom_prompt = "You are a specialized assistant."
        
        result = generator.generate_prompt(
            context, 
            user_system_prompt=custom_prompt
        )
        
        assert custom_prompt in result
    
    def test_generate_prompt_with_tool_config(self):
        """Test generate_prompt with tool configuration."""
        generator = SystemPromptGenerator()
        
        context = {"tools": []}
        tool_config = "Use tools carefully and validate inputs."
        
        result = generator.generate_prompt(
            context,
            tool_config=tool_config
        )
        
        assert tool_config in result
    
    def test_generate_for_tools_list_interface(self):
        """Test generate_for_tools_list method interface."""
        generator = SystemPromptGenerator()
        
        # This will fail initially if method doesn't exist
        assert hasattr(generator, 'generate_for_tools_list')
        assert callable(generator.generate_for_tools_list)
        
        tools = [
            {
                "name": "tool1",
                "description": "First tool"
            },
            {
                "name": "tool2", 
                "description": "Second tool"
            }
        ]
        
        result = generator.generate_for_tools_list(tools)
        
        assert isinstance(result, str)
        assert "tool1" in result
        assert "tool2" in result
    
    def test_template_placeholders(self):
        """Test that template contains expected placeholders."""
        generator = SystemPromptGenerator()
        
        # Template should contain placeholders for replacement
        template = generator.template
        
        # This will fail initially if template doesn't have proper placeholders
        expected_placeholders = [
            "{{ TOOL DEFINITIONS }}",
            "{{ USER SYSTEM PROMPT }}",
            "{{ TOOL CONFIGURATION }}"
        ]
        
        for placeholder in expected_placeholders:
            assert placeholder in template
    
    def test_prompt_generation_replaces_placeholders(self):
        """Test that prompt generation replaces all placeholders."""
        generator = SystemPromptGenerator()
        
        context = {
            "tools": [{"name": "test_tool"}]
        }
        
        result = generator.generate_prompt(context)
        
        # Generated prompt should not contain unreplaced placeholders
        assert "{{" not in result
        assert "}}" not in result
    
    def test_defaults_are_used_when_none_provided(self):
        """Test that defaults are used when parameters are None."""
        generator = SystemPromptGenerator()
        
        context = {"tools": []}
        
        # Call with None values
        result = generator.generate_prompt(
            context,
            user_system_prompt=None,
            tool_config=None
        )
        
        # Should use defaults
        assert generator.default_user_system_prompt in result
        assert generator.default_tool_config in result
    
    def test_custom_prompt_from_context(self):
        """Test that custom_prompt from context is used."""
        generator = SystemPromptGenerator()
        
        context = {
            "tools": [],
            "custom_prompt": "Custom prompt from context"
        }
        
        result = generator.generate_prompt(context)
        
        # Should use custom prompt from context
        assert "Custom prompt from context" in result
    
    def test_custom_prompt_overrides_parameter(self):
        """Test that custom_prompt from context overrides parameter."""
        generator = SystemPromptGenerator()
        
        context = {
            "tools": [],
            "custom_prompt": "Context prompt"
        }
        
        result = generator.generate_prompt(
            context,
            user_system_prompt="Parameter prompt"
        )
        
        # Context custom_prompt should take precedence
        assert "Context prompt" in result
        assert "Parameter prompt" not in result


class TestSystemPromptGeneratorEdgeCases:
    """Test edge cases for SystemPromptGenerator."""
    
    def test_empty_tools_list(self):
        """Test prompt generation with empty tools list."""
        generator = SystemPromptGenerator()
        
        context = {"tools": []}
        result = generator.generate_prompt(context)
        
        assert isinstance(result, str)
        assert len(result) > 0
        # Should handle empty tools gracefully
        assert "[]" in result or "no tools" in result.lower()
    
    def test_missing_tools_key(self):
        """Test prompt generation with missing tools key."""
        generator = SystemPromptGenerator()
        
        context = {}  # No tools key
        result = generator.generate_prompt(context)
        
        assert isinstance(result, str)
        # Should handle missing tools key gracefully
    
    def test_malformed_tools(self):
        """Test prompt generation with malformed tools."""
        generator = SystemPromptGenerator()
        
        context = {
            "tools": [
                {"name": "valid_tool"},
                {"invalid": "structure"},
                None,  # Invalid tool entry
            ]
        }
        
        # Should handle malformed tools without crashing
        result = generator.generate_prompt(context)
        assert isinstance(result, str)
    
    def test_very_long_prompts(self):
        """Test handling of very long prompts."""
        generator = SystemPromptGenerator()
        
        # Create many tools
        many_tools = [
            {"name": f"tool_{i}", "description": f"Tool number {i}"}
            for i in range(100)
        ]
        
        context = {"tools": many_tools}
        result = generator.generate_prompt(context)
        
        # Should handle large tool lists
        assert isinstance(result, str)
        assert "tool_0" in result
        assert "tool_99" in result
    
    def test_unicode_in_prompts(self):
        """Test handling of Unicode characters in prompts."""
        generator = SystemPromptGenerator()
        
        context = {
            "tools": [{"name": "测试工具", "description": "Unicode tool 🛠️"}],
            "custom_prompt": "You are a helpful assistant 🤖"
        }
        
        result = generator.generate_prompt(context)
        
        # Should handle Unicode properly
        assert "测试工具" in result
        assert "🛠️" in result
        assert "🤖" in result