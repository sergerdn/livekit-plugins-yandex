# Yandex SpeechKit STT Plugin - Development Commands

# Load environment variables from .env file if it exists
include .env
export

# Git information
GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
GIT_COMMIT := $(shell git rev-list -1 HEAD)
GIT_VERSION := $(shell git describe --tags --always)

.PHONY: help install lint lint_fix test test_functional test_unit test_integration test_e2e fixtures fixtures_speech fixtures_basic fixtures_voices clean build check_env
.DEFAULT_GOAL := help

# Show help information
help:
	@echo "Yandex SpeechKit STT Plugin - Available Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  install           Install development dependencies"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint              Check code for style issues"
	@echo "  lint_fix          Automatically fix code style issues"
	@echo ""
	@echo "Testing:"
	@echo "  test              Run all tests (requires credentials)"
	@echo "  test_unit         Run unit tests only (no credentials required)"
	@echo "  test_integration  Run integration tests (requires credentials)"
	@echo "  test_functional   Run functional tests (no credentials required)"
	@echo "  test_e2e          Run all end-to-end tests (plugin + agent)"
	@echo "  test_e2e_plugin   Run plugin-level E2E tests (STT functionality with real API)"
	@echo "  test_e2e_agent    Run agent-level E2E tests (LiveKit rooms and agent deployment)"
	@echo "  test_livekit_basic Run basic LiveKit integration tests (stable, fast)"
	@echo "  test_fixtures     Run fixture validation tests (checks test infrastructure)"
	@echo ""
	@echo "Test Fixtures:"
	@echo "  fixtures          Generate all test fixtures"
	@echo "  fixtures_speech   Generate speech test fixtures"
	@echo "  fixtures_basic    Generate basic test fixtures (tones, noise)"
	@echo "  fixtures_voices   List available TTS voices"
	@echo ""
	@echo "Build:"
	@echo "  build             Build the package"
	@echo "  clean             Clean build artifacts"
	@echo ""
	@echo "Environment:"
	@echo "  check_env         Check required environment variables"

# Install development dependencies
install:
	hatch env create
	hatch run pip install -e ".[dev]"

# Check code for style issues without fixing them
lint:
	@echo "Running linters..."
	hatch run docformatter --black --check --recursive livekit/ tests/ || echo ""
	hatch run black --check livekit/ tests/
	hatch run isort --check livekit/ tests/
	hatch run flake8 livekit/ tests/
	hatch run mypy livekit/
	hatch run mypy tests/
	hatch run pylint livekit/
	hatch run pylint tests/

# Automatically fix code style issues
lint_fix:
	@echo "Fixing code style..."
	hatch run docformatter --black --in-place --recursive livekit/ tests/ || echo ""
	hatch run black livekit/ tests/
	hatch run isort livekit/ tests/

# Environment check
check_env:
	@echo "Checking required environment variables..."
	@if [ -z "$(YANDEX_API_KEY)" ]; then \
		echo "YANDEX_API_KEY value: $(YANDEX_API_KEY)"; \
		echo "Error: YANDEX_API_KEY is not set"; \
		exit 1; \
	fi
	@if [ -z "$(YANDEX_FOLDER_ID)" ]; then \
		echo "YANDEX_FOLDER_ID value: $(YANDEX_FOLDER_ID)"; \
		echo "Error: YANDEX_FOLDER_ID is not set"; \
		exit 1; \
	fi
	@echo "Environment variables present"

# Check LiveKit environment variables
check_livekit_env:
	@echo "Checking required LiveKit environment variables..."
	@if [ -z "$(LIVEKIT_API_KEY)" ]; then \
		echo "LIVEKIT_API_KEY is not set"; \
		exit 1; \
	fi
	@if [ -z "$(LIVEKIT_API_SECRET)" ]; then \
		echo "LIVEKIT_API_SECRET is not set"; \
		exit 1; \
	fi
	@if [ -z "$(LIVEKIT_WS_URL)" ]; then \
		echo "LIVEKIT_WS_URL is not set"; \
		exit 1; \
	fi
	@echo "LiveKit environment variables present"

# Legacy alias
tests: test

# Run all tests
test: check_env check_livekit_env
	@echo "Running all tests..."
	#hatch run pytest tests/ -v -s --tb=long -o log_cli=true
	$(MAKE) test_unit
	$(MAKE) test_integration
	$(MAKE) test_functional
	$(MAKE) test_e2e_plugin
	$(MAKE) test_e2e_agent

# Install package in development mode
install_dev:
	@echo "Installing package in development mode..."
	hatch run pip install -e .

# Run unit tests only (no credentials required)
test_unit: install_dev
	@echo "Running unit tests..."
	hatch run pytest tests/unit/ -v -s --tb=long -o log_cli=true

# Run integration tests (requires .env with credentials)
test_integration: install_dev check_env
	@echo "Running integration tests..."
	hatch run pytest tests/integration/ -v -s --tb=long -o log_cli=true

# Run functional tests (no credentials required)
test_functional: install_dev
	@echo "Running functional tests..."
	hatch run pytest tests/functional/ -v -s --tb=long -o log_cli=true

# Run all end-to-end tests (plugin + agent)
test_e2e: install_dev check_env check_livekit_env
	@echo "Running all end-to-end tests (plugin + agent)..."
	hatch run pytest tests/e2e/ -v -s --tb=long -o log_cli=true

# Run plugin-level E2E tests (STT functionality with real Yandex API, requires Yandex credentials)
test_e2e_plugin: install_dev check_env
	@echo "Running plugin-level E2E tests (STT functionality with real API)..."
	hatch run pytest tests/e2e/plugin_e2e/ -v -s --tb=long -o log_cli=true

# Run agent-level E2E tests (LiveKit rooms and agent deployment, requires LiveKit credentials)
test_e2e_agent: install_dev check_livekit_env
	@echo "Running agent-level E2E tests (LiveKit rooms and agent deployment)..."
	hatch run pytest tests/e2e/agent_e2e/ -v -s --tb=long -o log_cli=true

# Run basic LiveKit integration tests only (requires LiveKit and Yandex credentials)
test_livekit_basic: install_dev check_env check_livekit_env
	@echo "Running basic LiveKit integration tests..."
	hatch run pytest tests/e2e/agent_e2e/test_basic_livekit_integration.py -v -s --tb=long -o log_cli=true

# Run fixture validation tests (checks test infrastructure)
test_fixtures: install_dev
	@echo "Running fixture validation tests..."
	hatch run pytest tests/test_fixture_validation.py -v -s --tb=long -o log_cli=true

# Generate all test fixtures (speech + basic)
fixtures:
	@echo "Generating all test fixtures..."
	hatch run python utils/fixture_generator.py --type all

# Generate speech fixtures only
fixtures_speech:
	@echo "Generating speech test fixtures..."
	hatch run python utils/fixture_generator.py --type speech

# Generate basic fixtures only (tones and noise)
fixtures_basic:
	@echo "Generating basic test fixtures..."
	hatch run python utils/fixture_generator.py --type basic

# List available TTS voices
fixtures_voices:
	@echo "Listing available TTS voices..."
	hatch run python utils/fixture_generator.py --list-voices

# Build the package
build:
	@echo "Building package..."
	hatch build

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

