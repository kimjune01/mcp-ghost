#!/usr/bin/env python3
"""
Run core MCP-Ghost tests excluding tests with external dependencies.

This script runs the essential functionality tests while skipping:
- Provider API tests (require real API keys and network calls)
- E2E tests (require running MCP servers like mcp-server-sqlite)  
- Golden tests (require API keys for recording)
- Complex integration tests (require external processes)

This ensures fast, reliable testing without external dependencies.
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Run core tests and return exit code."""
    test_paths = [
        "tests/test_core.py",
        "tests/test_basic_imports.py", 
        "tests/test_tools.py",
        "tests/test_utils.py",
        "tests/tools/",
        "tests/providers/test_client_factory.py",  # Factory tests are solid
    ]
    
    cmd = [
        "pytest",
        "--tb=short",
        "-v",
        *test_paths
    ]
    
    print("Running core MCP-Ghost functionality tests...")
    print("Skipping: provider API tests, E2E tests, tests requiring external dependencies")
    print("Command:", " ".join(cmd))
    print()
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    if result.returncode == 0:
        print("\n✅ All core functionality tests passed!")
        print("Core components working: config, tools, utils, client factory")
        print("\nFor full test suite (with external dependencies): make test-all")
    else:
        print(f"\n❌ Some tests failed (exit code: {result.returncode})")
        print("This indicates issues with core functionality, not external dependencies.")
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())