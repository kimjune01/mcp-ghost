#!/usr/bin/env python
"""Test runner for MCP-Ghost."""
import sys
import subprocess
from pathlib import Path

def run_tests():
    """Run the test suite."""
    # Add src to path for imports
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))
    
    # Run pytest with coverage if available
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/",
            "-v",
            "--tb=short",
            "-m", "not slow"  # Skip slow tests by default
        ], cwd=Path(__file__).parent)
        return result.returncode
    except FileNotFoundError:
        print("pytest not found. Install with: pip install pytest")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())