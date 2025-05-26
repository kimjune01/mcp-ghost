# MCP-Ghost Requirements Specification

## Overview

**MCP-Ghost** is a reusable Python component extracted from `mcp_round_trip.py` that provides a programmatic interface for interacting with MCP (Model Context Protocol) servers through LLMs. Unlike the CLI interface, MCP-Ghost accepts inputs directly from Python code and returns structured outputs.

## Core Functionality

MCP-Ghost acts as an intelligent MCP client that provides Claude Desktop-level tool orchestration:

### Basic Operations
1. Connects to specified MCP servers via stdio transport
2. Discovers available tools from connected servers
3. Sends user prompts to LLMs with tool context
4. Executes tool calls returned by the LLM
5. Returns structured results including tool execution summaries and errors

### Advanced Tool Orchestration
6. **Tool Chaining**: Automatically executes sequences of dependent tool calls
7. **Backtracking**: Retries failed operations with alternative approaches
8. **Context Management**: Maintains conversation state across multiple tool interactions
9. **Error Recovery**: Intelligent handling of tool failures with retry strategies
10. **Result Synthesis**: Combines outputs from multiple tools into coherent responses

## Input Parameters

### Required Parameters
- **`server_config`** (dict): MCP server configuration in the same format as `server_config.json`
  ```python
  {
    "mcpServers": {
      "sqlite": {
        "command": "uvx",
        "args": ["mcp-server-sqlite", "--db-path", "test.db"]
      }
    }
  }
  ```

- **`system_prompt`** (str): Natural language system prompt providing additional context for the LLM on how to use tools
  
- **`provider`** (str): LLM provider name - must support "openai", "anthropic", and "gemini"

- **`api_key`** (str): API key for the specified provider

- **`user_prompt`** (str): The user's natural language request

### Optional Parameters
- **`model`** (str): Specific model name (defaults to provider default)
- **`namespace`** (str): MCP namespace for tool organization (default: "mcp_ghost")
- **`timeout`** (float): Tool execution timeout in seconds (default: 30.0)
- **`max_iterations`** (int): Maximum number of tool chain iterations (default: 10)
- **`enable_backtracking`** (bool): Enable automatic retry with alternative approaches (default: True)
- **`conversation_memory`** (bool): Maintain context across tool calls (default: True)

## Output Structure

MCP-Ghost returns a structured dictionary containing:

```python
{
  "success": bool,                    # Overall success status
  "final_result": Any,                # Synthesized final result
  "summary": str,                     # Natural language summary of entire operation
  
  # Tool execution chain
  "tool_chain": [                     # Ordered list of all tool calls made
    {
      "iteration": int,               # Chain iteration number
      "tool_name": str,               # Original MCP tool name (e.g., "stdio.list_tables")
      "arguments": dict,              # Arguments passed to the tool
      "success": bool,                # Tool execution success status
      "result": Any,                  # Tool execution result
      "error": str | None,            # Error message if failed
      "execution_time": float,        # Execution time in seconds
      "reasoning": str,               # LLM's reasoning for this tool call
      "retry_attempt": int            # Retry attempt number (0 = first attempt)
    }
  ],
  
  # Conversation and reasoning
  "conversation_history": [           # Full conversation with LLM
    {
      "role": str,                    # "system", "user", "assistant", "tool"
      "content": str,                 # Message content
      "tool_calls": [...] | None,     # Tool calls if assistant message
      "tool_call_id": str | None      # Tool call ID if tool message
    }
  ],
  
  # Error handling and recovery
  "errors": [                         # List of all errors encountered
    {
      "iteration": int,
      "tool_name": str,
      "error": str,
      "recovery_action": str | None   # What recovery action was taken
    }
  ],
  
  # Execution metadata
  "execution_metadata": {
    "total_execution_time": float,
    "total_iterations": int,
    "tools_discovered": int,
    "servers_connected": int,
    "backtrack_count": int,           # Number of backtracking attempts
    "success_rate": float,            # Percentage of successful tool calls
    "token_usage": {                  # LLM token usage (if available)
      "prompt_tokens": int,
      "completion_tokens": int,
      "total_tokens": int
    }
  }
}
```

## Dependencies (Self-Contained)

MCP-Ghost should be copy-pastable with minimal external dependencies:

### Required Dependencies
- `asyncio` (stdlib)
- `json` (stdlib)
- `logging` (stdlib)
- `typing` (stdlib)
- `dotenv` - for environment variable loading
- `mcp` - Official MCP Python SDK for protocol handling
  - `mcp.ClientSession`
  - `mcp.StdioServerParameters`
  - `mcp.client.stdio.stdio_client`

### Dependencies to Rewrite (from mcp-cli)
These functions from `mcp-cli` should be rewritten within MCP-Ghost:

1. **`get_llm_client`** from `mcp_cli.llm.llm_client`
   - Provider-specific client instantiation
   - **Required Support**: OpenAI, Anthropic (Claude), and Gemini providers
   - API key and endpoint configuration
   - Model selection and parameter handling

2. **`SystemPromptGenerator`** from `mcp_cli.llm.system_prompt_generator`
   - System prompt template generation
   - Tool schema injection into prompts
   - Provider-specific prompt formatting

3. **Tool name adaptation utilities**:
   - Provider-specific tool name formatting:
     - **OpenAI**: Function name sanitization (regex pattern: `^[a-zA-Z0-9_-]+$`)
     - **Anthropic (Claude)**: Tool name formatting for Claude's function calling
     - **Gemini**: Tool schema adaptation for Google's function calling format

4. **Tool response formatting**:
   - `format_tool_response()` for consistent output formatting
   - JSON serialization handling for complex objects

## Security Model

### Security Boundaries
1. **Prompt Builder Responsibility**: The prompt builder ensures only allowlisted actions are passed to MCP-Ghost
2. **MCP Server Trust**: MCP-Ghost trusts the provided MCP servers completely
3. **Stdio Isolation**: Each MCP server runs in its own stdio subprocess for isolation

### Security Features
- **Server Allowlisting**: Only specified servers in `server_config` are accessible
- **Tool Discovery**: Only tools exposed by connected servers are available
- **Subprocess Isolation**: MCP servers run as separate processes
- **Timeout Protection**: Tool execution timeouts prevent hanging operations

### Security Assumptions
- The calling system (prompt builder) performs input validation and security filtering
- MCP servers provided in configuration are trusted
- The LLM provider API is trusted for processing prompts

## Usage Context

MCP-Ghost is designed for use in a larger architecture where:

1. **Human User** provides natural language input
2. **Prompt Builder** processes user input and:
   - Ensures security constraints are met
   - Produces structured inputs for MCP-Ghost
   - Filters allowable actions and servers
3. **MCP-Ghost** executes the one-shot tool operation
4. **Results** are returned to the prompt builder for further processing

## Advanced Tool Orchestration Features

### Tool Chaining
MCP-Ghost maintains conversation state to enable multi-step tool execution:

```python
# Example: File analysis workflow
# 1. LLM decides to list files
# 2. Analyzes file list and chooses specific files
# 3. Reads file contents
# 4. Performs analysis on contents
# 5. Synthesizes final report
```

**Implementation Requirements:**
- Maintain conversation history across all tool calls
- Pass tool results back to LLM for next step reasoning
- Continue until LLM indicates completion or max_iterations reached
- Track dependencies between tool calls

### Backtracking and Error Recovery
When tool calls fail, MCP-Ghost automatically attempts recovery:

**Recovery Strategies:**
1. **Retry with modified arguments** - Adjust parameters based on error message
2. **Alternative tool selection** - Try different tools that accomplish similar goals
3. **Decomposition** - Break complex operations into smaller steps
4. **Context clarification** - Ask LLM to rethink approach with error context

**Backtracking Implementation:**
```python
# Pseudo-code for backtracking
if tool_call_fails:
    error_context = f"Tool {tool_name} failed: {error_message}"
    recovery_prompt = f"The previous approach failed. {error_context}. Please try a different approach."
    # Send back to LLM with failure context
    continue_conversation_with_error_context(recovery_prompt)
```

### Context Management
**Conversation State Preservation:**
- Full conversation history maintained throughout execution
- Tool results formatted for LLM consumption
- Error messages included in context for learning
- Previous reasoning preserved for consistency

**Memory Optimization:**
- Summarize older parts of conversation when context gets long
- Keep recent tool calls and results in full detail
- Preserve critical context identified by LLM

### Result Synthesis
**Multi-Tool Result Combination:**
- Aggregate results from multiple tool calls
- Resolve conflicts between different tool outputs
- Generate coherent final response combining all information
- Provide reasoning trail showing how conclusion was reached

## Multi-Provider Support Requirements

MCP-Ghost must provide seamless integration across the three major LLM providers:

### Supported Providers

#### 1. **OpenAI** 
- **Models**: GPT-4o, GPT-4o-mini, GPT-4-turbo, GPT-3.5-turbo
- **Function Calling**: Native OpenAI function calling format
- **Tool Names**: Strict regex pattern `^[a-zA-Z0-9_-]+$`
- **Authentication**: API key via `OPENAI_API_KEY` or parameter

#### 2. **Anthropic (Claude)**
- **Models**: Claude-4-opus, Claude-4-sonnet, Claude-3.7-sonnet, Claude-3.5-sonnet, Claude-3-opus, Claude-3-sonnet, Claude-3-haiku
- **Function Calling**: Anthropic's tool use format
- **Tool Names**: More flexible naming compared to OpenAI
- **Authentication**: API key via `ANTHROPIC_API_KEY` or parameter

#### 3. **Google (Gemini)**
- **Models**: Gemini-2.5-pro, Gemini-2.5-flash, Gemini-2.0-flash, Gemini-1.5-pro, Gemini-1.5-flash
- **Function Calling**: Google's function calling schema
- **Tool Names**: Google-specific formatting requirements
- **Authentication**: API key via `GOOGLE_API_KEY` or parameter

### Provider Abstraction Layer

**Unified Interface**: All providers must support the same core operations:
```python
async def create_completion(
    messages: List[Dict], 
    tools: List[Dict], 
    **kwargs
) -> Dict
```

**Provider-Specific Adaptations**:
- Tool schema conversion for each provider's format
- Response parsing and normalization
- Error handling and retry logic
- Token usage tracking and optimization

### Cross-Provider Consistency

**Tool Schema Normalization**:
- Convert MCP tool definitions to provider-specific formats
- Maintain bidirectional name mapping for all providers
- Handle parameter schema differences

**Response Standardization**:
- Normalize tool call responses across providers
- Consistent error message formatting
- Unified token usage reporting

**Quality Assurance**:
- Same tool chain should work across all providers
- Consistent behavior for error recovery and backtracking
- Provider-specific optimizations without breaking compatibility

## Implementation Requirements

### Core Interface
```python
async def mcp_ghost(
    server_config: dict,
    system_prompt: str, 
    provider: str,
    api_key: str,
    user_prompt: str,
    model: str = None,
    namespace: str = "mcp_ghost",
    timeout: float = 30.0,
    max_iterations: int = 10,
    enable_backtracking: bool = True,
    conversation_memory: bool = True
) -> dict:
    """
    Execute intelligent multi-step MCP tool operations via LLM.
    
    Supports tool chaining, backtracking, and error recovery like Claude Desktop.
    """
    pass
```

### Error Handling
**Infrastructure Errors:**
- Graceful handling of MCP server connection failures
- LLM API error handling with descriptive messages
- Tool execution timeouts and failures
- Malformed tool call handling

**Tool Chain Error Handling:**
- Automatic retry mechanisms for transient failures
- Context-aware error recovery using LLM reasoning
- Partial success handling (some tools succeed, others fail)
- Circuit breaker pattern for repeatedly failing tools
- Graceful degradation when max_iterations reached

### Resource Management
- Proper cleanup of MCP server connections
- Stream manager cleanup on completion/failure
- Tool processor shutdown

### Tool Name Adaptation
- Convert MCP tool names to provider-compatible format
- Maintain bidirectional name mapping for execution
- Handle namespace prefixing (e.g., "stdio.list_tables" → "stdio_list_tables")

## Testing Strategy

### Golden/Snapshot Testing Framework
**Purpose**: Minimize LLM API costs and provide fast, reliable testing with human-inspectable debugging.

**Golden Test Implementation**:
```python
# Example golden test structure
{
  "test_name": "multi_step_database_analysis",
  "input": {
    "server_config": {...},
    "system_prompt": "...",
    "provider": "openai",
    "user_prompt": "analyze database tables and create a summary report"
  },
  "golden_output": {
    "success": true,
    "tool_chain": [...],
    "conversation_history": [...],
    "execution_metadata": {...}
  },
  "recorded_at": "2024-01-15T10:30:00Z",
  "provider_responses": [
    {
      "iteration": 1,
      "request": {...},
      "response": {...},
      "token_usage": {...}
    }
  ]
}
```

**Golden Test Benefits**:
- **Cost Efficiency**: Record real LLM interactions once, replay for testing
- **Speed**: Fast test execution without API calls
- **Determinism**: Consistent test results across runs
- **Human Inspection**: JSON format allows easy debugging and validation
- **Regression Detection**: Changes in behavior immediately visible

**Golden Test Categories**:
1. **Happy Path Goldens**: Successful multi-step tool chains
2. **Error Recovery Goldens**: Backtracking and retry scenarios
3. **Provider Comparison Goldens**: Same input across OpenAI/Claude/Gemini
4. **Edge Case Goldens**: Complex tool interactions and error conditions

**Golden Test Workflow**:
```python
# Recording mode (expensive, run occasionally)
@pytest.mark.record_golden
def test_database_analysis_record():
    result = await mcp_ghost(...)
    save_golden("database_analysis.json", result)

# Replay mode (fast, run constantly)
def test_database_analysis_replay():
    golden = load_golden("database_analysis.json")
    mock_llm_with_golden(golden)
    result = await mcp_ghost(...)
    assert_matches_golden(result, golden)
```

### Unit Tests
- Tool name adaptation functions
- System prompt generation
- Error handling scenarios
- Response formatting
- Golden test validation logic

### Integration Tests
- End-to-end execution with mock MCP servers
- **Cross-provider testing**: OpenAI, Anthropic (Claude), and Gemini
- Tool execution with various argument types
- Timeout and error scenarios
- Multi-step tool chaining workflows
- Error recovery and backtracking scenarios
- Provider-specific feature testing

### Advanced Testing Scenarios
**Tool Chain Testing:**
- Multi-step workflows (5+ tool calls)
- Dependency resolution between tools
- Partial failure recovery
- Context preservation across iterations

**Backtracking Testing:**
- Forced tool failures with recovery
- Alternative approach discovery
- Max iteration boundary testing
- Error context propagation

**Performance Testing:**
- Long conversation memory management
- Token usage optimization across providers
- Concurrent tool execution
- Resource cleanup under failure conditions
- Cross-provider performance comparison

**Provider-Specific Testing:**
- OpenAI function calling edge cases
- Claude tool use format validation
- Gemini function calling schema compliance
- Provider-specific error handling
- Token limit management per provider

### Golden Test Management

**Human-Inspectable Debugging**:
```bash
# Golden test directory structure
tests/
├── goldens/
│   ├── openai/
│   │   ├── happy_path_database_query.json
│   │   ├── error_recovery_file_not_found.json
│   │   └── multi_tool_chain_analysis.json
│   ├── anthropic/
│   │   ├── happy_path_database_query.json
│   │   └── backtracking_scenario.json
│   ├── gemini/
│   │   └── complex_tool_orchestration.json
│   └── shared/
│       └── tool_schema_definitions.json
```

**Golden Test Inspection Tools**:
```python
# CLI tool for golden inspection
def inspect_golden(golden_path: str):
    """
    Human-readable golden test inspector:
    - Shows conversation flow step-by-step
    - Highlights tool calls and responses  
    - Displays token usage and timing
    - Identifies failure points in error scenarios
    """
    golden = load_golden(golden_path)
    print_conversation_flow(golden.conversation_history)
    print_tool_execution_summary(golden.tool_chain)
    print_performance_metrics(golden.execution_metadata)
```

**Golden Test Validation**:
- **Semantic Comparison**: Compare intent, not exact text matches
- **Tool Chain Validation**: Verify tool call sequence and arguments
- **Error Pattern Matching**: Ensure error recovery follows expected patterns
- **Performance Bounds**: Check execution time and token usage within limits

**Golden Test Maintenance**:
- **Regeneration Strategy**: When to update vs. create new goldens
- **Version Control**: Track golden changes with meaningful commits
- **Provider Drift Detection**: Alert when provider behavior changes significantly
- **Golden Expiry**: Automatic flagging of outdated test recordings

### Test Data Requirements
- **Golden Test Library**: Comprehensive collection of recorded real interactions
- Sample MCP server configurations
- Multi-step test scenarios with expected tool chains
- Error injection test cases
- Expected output structures for complex workflows
- **Provider-specific golden recordings**: OpenAI, Claude, and Gemini
- Conversation history test fixtures
- Cross-provider compatibility test cases
- Provider-specific tool schema examples
- **Human-readable golden test documentation** for debugging

## Future Extensibility

### Provider Support
- **Core Providers**: OpenAI, Anthropic (Claude), Gemini (required)
- Pluggable provider system for additional LLM providers
- Consistent interface across all providers
- Provider-specific optimizations without breaking compatibility
- Dynamic provider selection based on task requirements

### Tool Enhancement
- Streaming tool execution support
- Parallel tool execution (with dependency management)
- Tool call result caching
- Dynamic tool discovery during execution
- Tool performance profiling and optimization

### Advanced Orchestration Features
- **Planning Phase**: Pre-execution tool chain planning
- **Conditional Execution**: IF/THEN logic in tool chains
- **Loop Detection**: Prevent infinite tool call loops
- **Rollback Capability**: Undo previous tool actions when possible
- **Tool Interop**: Cross-server tool coordination

### Monitoring & Observability
- Execution metrics collection
- Tool usage analytics
- Performance monitoring hooks
- Chain decision tracing
- Token usage optimization tracking
- Success/failure pattern analysis
- **Golden test coverage tracking**
- **Provider behavior drift monitoring**

### Testing & Quality Assurance
- **Automated Golden Test Generation**: Convert production runs to test cases
- **Cross-Provider Golden Comparison**: Identify behavior differences
- **Golden Test Analytics**: Track test coverage and effectiveness
- **Regression Detection**: Immediate alerts on behavior changes
- **Human-in-the-Loop Validation**: Expert review of complex golden scenarios