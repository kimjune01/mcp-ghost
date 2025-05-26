# MCP-Ghost Testing Framework

This directory contains the test suite for MCP-Ghost, including a comprehensive golden test framework for LLM provider integration testing.

## Test Structure

```
tests/
├── README.md                   # This file
├── conftest.py                # Pytest configuration and fixtures
├── goldens/                   # Golden test framework
│   ├── golden_framework.py    # Core golden recording/replay logic
│   ├── openai/               # OpenAI provider golden files
│   ├── anthropic/            # Anthropic provider golden files  
│   ├── gemini/               # Gemini provider golden files
│   └── shared/               # Shared test data
├── providers/                # Provider integration tests
├── tools/                    # Tool utility tests
├── utils/                    # Utility module tests
└── core/                     # Core functionality tests
```

## Golden Test Framework

The golden test framework solves the challenge of testing LLM provider integrations without incurring API costs on every test run. It records real API interactions once, then replays them deterministically for fast, reliable testing.

### How Golden Tests Work

1. **Recording Mode**: Makes actual API calls and saves responses to JSON files
2. **Replay Mode**: Loads saved responses for deterministic testing
3. **Human-Inspectable**: Golden files are readable JSON for easy debugging

### Golden Test Format

Each golden file follows this structure (as specified in REQUIREMENTS.md):

```json
{
  "test_name": "test_create_completion_basic",
  "input": {
    "server_config": {},
    "system_prompt": "You are a helpful assistant.",
    "provider": "openai", 
    "user_prompt": "Say hello in exactly 3 words",
    "model": "gpt-4o-mini"
  },
  "golden_output": {
    "success": true,
    "final_result": {...},
    "summary": "Basic completion test",
    "tool_chain": [...],
    "conversation_history": [...],
    "execution_metadata": {...}
  },
  "recorded_at": "2025-05-25T21:30:06.230569Z",
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

## Using Golden Tests

### Running Tests

```bash
# Replay mode (default) - fast, no API calls
python -m pytest tests/providers/

# Recording mode - makes real API calls, updates golden files
RECORD_GOLDENS=true python -m pytest tests/providers/test_openai_client.py::TestOpenAILLMClient::test_create_completion_basic

# Run specific provider tests
python -m pytest tests/providers/test_openai_client.py -v
```

### Writing New Golden Tests

1. **Create the test function** with golden recorder:

```python
@pytest.mark.asyncio
async def test_my_new_feature(self):
    """Test new feature with golden recording."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        pytest.skip("OPENAI_API_KEY not found in environment")
    
    # Create golden recorder
    recorder = GoldenRecorder("test_my_new_feature", "openai")
    
    # Set input data
    recorder.set_input(
        server_config={},
        system_prompt="System prompt here",
        user_prompt="User prompt here",
        model="gpt-4o-mini"
    )
    
    if recorder.record_mode:
        # Record mode: make actual API call
        client = OpenAILLMClient(api_key=api_key)
        result = await client.create_completion(messages)
        
        # Record the interaction
        recorder.record_provider_interaction(request_data, result, token_usage)
        recorder.set_golden_output(expected_output)
        golden_path = recorder.save_golden()
        print(f"Saved golden file: {golden_path}")
    else:
        # Replay mode: use mock client
        mock_client = MockLLMClient(recorder)
        result = await mock_client.create_completion(messages)
    
    # Assertions
    assert "response" in result
    assert isinstance(result["response"], str)
```

2. **Record the golden file**:
```bash
RECORD_GOLDENS=true python -m pytest tests/providers/test_openai_client.py::TestOpenAILLMClient::test_my_new_feature -v
```

3. **Verify replay works**:
```bash
python -m pytest tests/providers/test_openai_client.py::TestOpenAILLMClient::test_my_new_feature -v
```

### Inspecting Golden Files

#### Web Interface (Recommended)

Launch the interactive web viewer for the best inspection experience:

```bash
# Start web viewer (opens browser automatically)
cd tests
python golden_viewer.py

# Custom port
python golden_viewer.py --port 8080

# Don't auto-open browser
python golden_viewer.py --no-browser
```

The web viewer provides:
- 📊 **Provider Statistics Dashboard** - success rates, token usage, test counts
- 🗂️ **Interactive File Browser** - click to explore golden files
- 💬 **Conversation Visualization** - formatted chat flows with tool calls
- 📈 **Performance Metrics** - execution times, token usage, iteration counts
- 📄 **Raw JSON Viewer** - formatted, searchable JSON data
- 🔍 **Human-Readable Display** - easy-to-understand test breakdowns

#### Command Line Interface

Use the built-in CLI tool for quick inspections:

```bash
# Inspect a golden file
cd tests/goldens
python golden_framework.py inspect openai/test_create_completion_basic.json

# Set up directory structure
python golden_framework.py setup
```

CLI output example:
```
=== Golden Test: test_create_completion_basic ===
Provider: openai
Recorded: 2025-05-25T21:30:06.230569Z

--- Input ---
User Prompt: Say hello in exactly 3 words
System Prompt: You are a helpful assistant....

--- Conversation Flow ---
1. user: Say hello in exactly 3 words
2. assistant: Hello, how are you?

--- Performance Metrics ---
Total time: 1.5s
Iterations: 1
Tokens: 50 total

--- Provider Interactions ---
Iteration 1: 50 tokens
```

## Golden Test Maintenance

### When to Update Golden Files

- **New provider features**: Record new golden files for new functionality
- **Provider API changes**: Re-record if provider responses change significantly  
- **Test evolution**: Update goldens when test requirements change

### Best Practices

1. **Descriptive test names**: Use clear, specific test names for golden files
2. **Minimal API calls**: Only record what's necessary to avoid costs
3. **Version control**: Commit golden files to track changes over time
4. **Review changes**: Inspect golden file diffs before committing
5. **Provider parity**: Test same functionality across all providers

### Updating Existing Golden Files

```bash
# Re-record a specific test
RECORD_GOLDENS=true python -m pytest tests/providers/test_openai_client.py::TestOpenAILLMClient::test_create_completion_basic -v

# Re-record all tests for a provider (expensive!)
RECORD_GOLDENS=true python -m pytest tests/providers/test_openai_client.py -v
```

## Environment Setup

### Required Environment Variables

Create a `.env` file in the project root:

```bash
# API Keys for recording mode
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-api03-...
GOOGLE_API_KEY=AIza...

# Golden test control
RECORD_GOLDENS=false  # Set to 'true' to record new goldens
```

### Provider-Specific Setup

**OpenAI**: Requires `OPENAI_API_KEY`
**Anthropic**: Requires `ANTHROPIC_API_KEY`  
**Gemini**: Requires `GOOGLE_API_KEY`

## Troubleshooting

### Common Issues

1. **Missing API keys**: Tests will skip if required API keys aren't set
2. **Golden file not found**: Run in recording mode first to create the file
3. **Test failures after recording**: Check that replay logic matches recording logic
4. **API rate limits**: Space out recording sessions to avoid hitting limits

### Debugging Golden Tests

1. **Inspect golden files**: Use the inspection tool to understand what was recorded
2. **Check file structure**: Ensure golden files follow the expected JSON format
3. **Verify provider responses**: Compare recorded responses with expected format
4. **Review test logic**: Ensure recording and replay paths are consistent

### Performance Tips

- **Use replay mode** for regular development (fast, no API costs)
- **Record selectively** - only update goldens when necessary
- **Parallel testing** - golden replay tests can run in parallel safely
- **Cache golden files** - consider caching for CI/CD pipelines

## Integration with CI/CD

### Recommended CI Setup

```yaml
# Run tests in replay mode (fast)
- name: Run tests
  run: python -m pytest tests/ --tb=short

# Optional: Validate golden files exist
- name: Check golden files
  run: |
    test -f tests/goldens/openai/test_create_completion_basic.json
    test -f tests/goldens/openai/test_create_completion_with_tools.json
```

### Updating Goldens in CI

```yaml
# Scheduled job to update goldens (weekly)
- name: Update golden files
  if: github.event_name == 'schedule'
  env:
    RECORD_GOLDENS: true
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
  run: python -m pytest tests/providers/ -v
```

## Benefits of Golden Testing

- **Cost Efficiency**: Record once, replay many times
- **Speed**: Fast test execution (no API latency)
- **Determinism**: Consistent results across runs
- **Debugging**: Human-readable test artifacts
- **Regression Detection**: Immediate visibility into behavior changes
- **Cross-Provider Testing**: Easy comparison across OpenAI/Anthropic/Gemini

The golden test framework enables reliable, cost-effective testing of LLM provider integrations while maintaining the benefits of real API interaction recording.