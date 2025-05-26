# Testing Strategy

MCP-Ghost uses a **focused core test suite** approach to provide fast, reliable testing without external dependencies.

## Quick Start

```bash
# Default - run core functionality tests (recommended)
make test

# Full test suite (requires external setup)
make test-all
```

## Test Categories

### Core Tests (Default)
**Run with**: `make test` or `python run_core_tests.py`
- ✅ **145 tests** in ~1 second
- ✅ **No external dependencies** required
- ✅ **100% core functionality** coverage
- ✅ **Runs in CI/CD** reliably

**Covers**:
- Core MCP-Ghost functionality (`tests/test_core.py`)
- Basic imports and module structure (`tests/test_basic_imports.py`)
- Tools system (adapters, formatters, models) (`tests/tools/`)
- Utilities (`tests/test_utils.py`)
- Client factory (`tests/providers/test_client_factory.py`)

### Full Test Suite
**Run with**: `make test-all` or `uv run pytest`
- ⚠️ **214 tests** (slow, hangs on missing dependencies)
- ⚠️ **Requires external setup** (see below)
- ⚠️ **May fail due to environment** issues

**Additional coverage**:
- Provider API integration tests
- End-to-end MCP server tests
- Golden/snapshot tests with real LLM calls
- Complex async integration scenarios

## External Dependencies (for Full Suite)

The full test suite requires significant external setup:

### MCP Servers
```bash
# Install required MCP servers
uvx install mcp-server-sqlite
uvx install mcp-server-filesystem
```

### API Keys
Set environment variables:
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="AIza..."
```

### Network Access
- Tests make real HTTP calls to LLM providers
- May fail due to network issues, rate limits, API changes

### Process Management
- Tests spawn MCP server subprocesses
- May fail due to process conflicts, timeouts

## Golden Tests

Golden tests record real LLM interactions for regression testing:

```bash
# Record new golden tests (requires API keys)
pytest -m record_golden

# Replay golden tests (uses recorded data)
pytest tests/test_golden_e2e_crud.py
```

## Why Make vs Pytest?

**`pytest`** (direct test runner):
- ✅ Standard Python testing tool, full control
- ❌ Runs ALL 214 tests by default, including those requiring external dependencies
- ❌ Hangs on missing MCP servers, API keys, network issues

**`make test`** (curated wrapper):
- ✅ Project-customized behavior, skips problematic tests  
- ✅ Runs only 145 reliable core tests (~1 second)
- ✅ Consistent experience across team, no external setup needed
- ❌ Extra abstraction layer

We chose `make test` as default because `pytest` by itself runs tests that:
- Try to spawn MCP server subprocesses (hang if not installed)
- Make real HTTP API calls (fail/timeout without valid keys)
- Have complex async mocking (event loop conflicts)

Alternative approaches considered:
- `pytest -m "not external"` (requires marking all tests)
- Separate test directories (`tests/unit/`, `tests/integration/`)  
- `pyproject.toml` ignores (static, can't be easily toggled)

## Philosophy

We prioritize **golden tests over mocks** for LLM integration testing:
- **Golden tests**: Record real interactions, replay for regression testing
- **Mocks**: Complex, brittle, don't test actual integrations
- **Core tests**: Fast feedback loop for development

## Development Workflow

1. **Daily development**: Use `make test` for fast feedback
2. **Before commits**: Ensure `make test` passes (required)
3. **Integration testing**: Use `make test-all` when testing with real services
4. **CI/CD**: Runs `make test` for reliability

## Troubleshooting

### "Tests hang" 
- You're running `make test-all` without required dependencies
- Solution: Use `make test` for daily development

### "External dependency errors"
- Missing MCP servers or API keys for full test suite
- Solution: Use `make test` or set up external dependencies

### "Core tests fail"
- Indicates actual bugs in core functionality
- Solution: Fix the failing functionality before proceeding