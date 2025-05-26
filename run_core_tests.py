#!/usr/bin/env python3
"""
Run core MCP-Ghost tests excluding problematic test categories.

This script runs the essential functionality tests while skipping:
- Provider API tests (prefer golden tests)
- E2E tests (require running MCP servers)  
- Complex mock-based tests (prefer golden tests)
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
    print("Skipping: provider API tests, E2E tests, complex mocks")
    print("Command:", " ".join(cmd))
    print()
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    if result.returncode == 0:
        print("\n✅ All core functionality tests passed!")
        print("Core components working: config, tools, utils, client factory")
    else:
        print(f"\n❌ Some tests failed (exit code: {result.returncode})")
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())