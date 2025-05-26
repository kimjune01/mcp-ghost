"""
System prompt generation - extracted from mcp_cli.llm.system_prompt_generator
"""
import json
from typing import Dict, Any, Optional


class SystemPromptGenerator:
    """
    A class for generating system prompts dynamically based on tools JSON and user inputs.
    """

    def __init__(self):
        """
        Initialize the SystemPromptGenerator with a default system prompt template.
        """
        self.template = """In this environment you have access to a set of tools you can use to answer the user's question.

You can invoke functions by writing tool calls in the format the user expects.

String and scalar parameters should be specified as is, while lists and objects should use JSON format. Note that spaces for string values are not stripped.

Here are the functions available:
{{ TOOL DEFINITIONS }}

{{ USER SYSTEM PROMPT }}

{{ TOOL CONFIGURATION }}

You are an intelligent assistant capable of using tools to solve user queries effectively. When you need to use tools, think step by step about what information you need and use the appropriate tools to gather that information. If a tool call fails, try alternative approaches or tools to accomplish the goal."""

        self.default_user_system_prompt = "You are an intelligent assistant capable of using tools to solve user queries effectively."
        self.default_tool_config = "Use tools as needed to provide comprehensive and accurate responses."

    def generate_prompt(
        self, 
        context: Dict[str, Any], 
        user_system_prompt: Optional[str] = None, 
        tool_config: Optional[str] = None
    ) -> str:
        """
        Generate a system prompt based on the provided context and options.

        Args:
            context: Dictionary containing tools and other context
            user_system_prompt: A user-provided description or instruction for the assistant (optional).
            tool_config: Additional tool configuration information (optional).

        Returns:
            str: The dynamically generated system prompt.
        """

        # Extract tools from context
        tools = context.get("tools", [])
        custom_prompt = context.get("custom_prompt", "")
        
        # set the user system prompt
        if custom_prompt:
            user_system_prompt = custom_prompt
        else:
            user_system_prompt = user_system_prompt or self.default_user_system_prompt

        # set the tools config
        tool_config = tool_config or self.default_tool_config

        # get the tools schema
        tools_json_schema = json.dumps(tools, indent=2, ensure_ascii=False)

        # perform replacements
        prompt = self.template.replace("{{ TOOL DEFINITIONS }}", tools_json_schema)
        prompt = prompt.replace("{{ USER SYSTEM PROMPT }}", user_system_prompt)
        prompt = prompt.replace("{{ TOOL CONFIGURATION }}", tool_config)

        # return the prompt
        return prompt
    
    def generate(self, tools=None, namespace="mcp_ghost", additional_context=None):
        """
        Simple generate method that core.py expects.
        """
        tools = tools or []
        context = {"tools": tools}
        if additional_context:
            context["custom_prompt"] = additional_context
        return self.generate_prompt(context)
    
    def generate_for_tools_list(self, tools):
        """
        Generate system prompt for a list of tools.
        
        Args:
            tools: List of tool dictionaries
            
        Returns:
            str: Generated system prompt
        """
        context = {"tools": tools}
        return self.generate_prompt(context)