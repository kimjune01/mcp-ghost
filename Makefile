# MCP-Ghost Makefile

.PHONY: help install install-dev test clean build docs format lint

help:
	@echo "Available commands:"
	@echo "  install      Install package in development mode"
	@echo "  install-dev  Install with development dependencies"
	@echo "  test         Run tests"
	@echo "  clean        Clean build artifacts"
	@echo "  build        Build package"
	@echo "  format       Format code with black"
	@echo "  lint         Lint code with ruff"

install:
	uv pip install -e .

install-dev:
	uv pip install -e ".[dev,testing]"

test:
	uv run pytest

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf src/*.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:
	uv run python -m build

format:
	uv run black src/ tests/ examples/

lint:
	uv run ruff check src/ tests/ examples/

# Development workflow
dev: clean install-dev format lint test

# Example runs
example-basic:
	cd examples && uv run python basic_usage.py

example-multi:
	cd examples && uv run python multi_provider.py