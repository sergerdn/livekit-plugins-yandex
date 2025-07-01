# Development Guide - Yandex SpeechKit STT Plugin

> **⚠️ IMPORTANT DISCLAIMER**
> This is an **independent, community-developed plugin** and is
> **NOT officially affiliated with or endorsed by LiveKit or Yandex**.
>
> This project is **NOT part of either the official LiveKit or Yandex ecosystems**.          
> For issues, support, or contributions related to this plugin, please use this project's repository directly.         
> Do not use LiveKit's or Yandex's official support channels for plugin-specific matters.

This document provides detailed development information for the Yandex SpeechKit STT plugin for LiveKit Agents.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing Strategy](#testing-strategy)
- [Code Quality](#code-quality)
- [Utilities and Tools](#utilities-and-tools)
- [Debugging](#debugging)
- [Contributing](#contributing)
- [External API Documentation](#external-api-documentation)

## Development Setup

### Prerequisites

**Required Tools:**

- **Python 3.9+**
- **Official Yandex Cloud SDK** - automatically installed as a dependency
- **Make (Optional)**: While not strictly required for development (as Hatch handles build and environment management),
  a `Makefile` is provided for convenience with common commands.
    - **Windows users**: If you wish to use the `Makefile`, `make` can be installed
      via [Chocolatey](https://community.chocolatey.org/packages/make): `choco install make`.
    - **Other OS**: `make` is typically available through system package managers (e.g., `apt-get install make` on
      Debian/Ubuntu, `brew install make` on macOS).
- **FFmpeg (Optional - for test fixture generation)**: Needed if you plan to use or modify the
  `utils/fixture_generator.py` script to create/convert audio test files. If you only intend to run existing tests with
  provided fixtures, or not work with fixtures at all, FFmpeg is not strictly necessary for core plugin development or
  usage.
    - **Windows**: Install via Chocolatey: `choco install ffmpeg`
    - **macOS**: Install via Homebrew: `brew install ffmpeg`
    - **Linux**: Install via package manager: `sudo apt-get install ffmpeg` (Ubuntu/Debian)

### Environment Setup

1. **Clone the repository:**
   ```bash
   git clone git@github.com:sergerdn/livekit-plugins-yandex.git
   cd livekit-plugins-yandex
   ```

2. **Install development dependencies using Hatch:**

   **Option 1: Using Makefile (recommended):**
   ```bash
   make install
   ```

   **Option 2: Using Hatch directly:**
   ```bash
   # Create the default Hatch environment and install dependencies
   hatch env create

   # Install the plugin in editable mode with dev dependencies
   hatch run pip install -e ".[dev]"

   # Optional: Install with fixtures support (Windows TTS for test audio generation)
   hatch run pip install -e ".[dev,fixtures]"

   # Activate the environment for the current session
   hatch shell
   ```

3. **Set up environment variables:**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env with your Yandex Cloud credentials
   # YANDEX_API_KEY=your_api_key_here
   # YANDEX_FOLDER_ID=your_folder_id_here
   ```

4. **Verify installation:**
   ```bash
   # Test that the plugin can be imported
   hatch run python -c "from livekit.plugins import yandex; print('Plugin installed successfully')"
   ```

### Optional Dependencies

#### Fixtures Category

The `fixtures` optional dependency category includes Windows-specific tools for generating test audio files:

**What's included:**

- `pywin32==310` - Windows COM interface for accessing Windows TTS (SAPI)

**When to install:**

- You're developing on Windows
- You need to regenerate speech test fixtures
- You're working with the `utils/fixture_generator.py` script

**Installation:**

```bash
# Install with fixtures support
hatch run pip install -e ".[dev,fixtures]"

# Or just fixtures without dev dependencies
hatch run pip install -e ".[fixtures]"
```

**Note**: This is only available on Windows (`sys_platform == 'win32'`) and is completely optional. The plugin works
without it, and existing test fixtures are provided via Git LFS.

### Git LFS for Test Fixtures

**Important**: After cloning the repository, if developers want to run tests with fixtures (functional and e2e tests),
they need to check out Git LFS files:

```bash
# Install Git LFS if not already installed
git lfs install

# Pull LFS files (audio test fixtures)
git lfs pull
```

**What's included:**

- Sample audio files in multiple languages (Russian, English)
- Various audio formats and sample rates for testing
- Test fixtures for functional and end-to-end tests

## Project Structure

```
livekit-plugins-yandex/
├── livekit/plugins/yandex/          # Main plugin code
│   ├── __init__.py                  # Public API exports
│   ├── stt.py                       # Main STT implementation
│   ├── _utils.py                    # Internal utilities
│   ├── models.py                    # Type definitions
│   ├── log.py                       # Logging configuration
│   ├── version.py                   # Version information
│   └── yandex_api.py                # Yandex Cloud API helpers (uses official SDK)
├── tests/                           # Test suite
│   ├── conftest.py                  # Shared test configuration
│   ├── unit/                        # Unit tests (no external deps)
│   │   ├── conftest.py
│   │   └── test_stt.py
│   ├── integration/                 # Integration tests (requires credentials)
│   │   ├── conftest.py
│   │   └── test_stt.py
│   ├── functional/                  # Functional tests (requires audio)
│   │   ├── conftest.py
│   │   └── test_stt.py
│   ├── e2e/                         # End-to-end tests (full workflow)
│   │   ├── conftest.py
│   │   └── test_real_audio_processing.py
│   └── fixtures/                    # Test audio files
│       └── *.wav                    # Generated audio fixtures
├── utils/                           # Development utilities
│   ├── README.md
│   ├── fixture_generator.py         # Audio fixture generator
│   └── __init__.py
├── docs/                            # Documentation
├── pyproject.toml                   # Project configuration
├── Makefile                         # Development commands
├── README.md                        # Basic usage documentation
├── DEVELOPMENT.md                   # This file
└── .env.example                     # Environment template
```

## Development Workflow

### Daily Development

1. **Start development session:**
   ```bash
   # Activate environment
   hatch shell

   # Or see available commands
   make help
   ```

2. **Run linters before coding:**
   ```bash
   make lint
   ```

3. **Make changes and test:**
   ```bash
   # Run unit tests (fast, no credentials needed)
   make test_unit
   
   # Run integration tests (requires credentials)
   make test_integration
   
   # Run all tests
   make test
   ```

4. **Fix code style issues:**
   ```bash
   make lint_fix
   ```

### Making Changes

**Code Changes:**

- Follow existing code style and patterns
- Add type hints for all public APIs
- Update docstrings for any API changes
- Add tests for new functionality

**Adding Features:**

1. Write unit tests first (TDD approach)
2. Implement the feature
3. Add integration tests if needed
4. Update documentation
5. Run full test suite

**Bug Fixes:**

1. Write a test that reproduces the bug
2. Fix the bug
3. Ensure the test passes
4. Run regression tests

## Testing Strategy

### Test Types

**Unit Tests (`tests/unit/`):**

- No external dependencies
- Mock all external services
- Fast execution (< 1 second)
- Test individual components in isolation

**Integration Tests (`tests/integration/`):**

- Require real Yandex Cloud credentials
- Test component interactions
- Moderate execution time
- Test API integration without audio processing

**Functional Tests (`tests/functional/`):**

- Require credentials AND audio files
- Test end-to-end functionality
- Slower execution
- Test real audio processing

**End-to-End Tests (`tests/e2e/`):**

- Require credentials AND audio files
- Test complete workflows
- Comprehensive real-world scenarios
- Full integration testing

### Running Tests

```bash
# Unit tests only (no credentials required)
make test_unit

# Integration tests (requires .env with credentials)
make test_integration

# Functional tests (no credentials required)
make test_functional

# All end-to-end tests (plugin + agent)
make test_e2e

# Plugin-level E2E tests (STT functionality, requires Yandex credentials)
make test_e2e_plugin

# Agent-level E2E tests (LiveKit integration, requires LiveKit + Yandex credentials)
make test_e2e_agent

# All tests
make test

# Fixture validation tests (checks test infrastructure)
make test_fixtures
```

### E2E Test Structure

The E2E tests are organized into two distinct categories:

#### **Plugin-level E2E Tests** (`tests/e2e/plugin_e2e/`)

- **Purpose**: Test STT plugin functionality with real Yandex Cloud API
- **Requirements**: Yandex credentials only (`YANDEX_API_KEY`, `YANDEX_FOLDER_ID`)
- **Scope**: Audio processing, transcription accuracy, STT streaming, error handling
- **Run with**: `make test_e2e_plugin`

#### **Agent-level E2E Tests** (`tests/e2e/agent_e2e/`)

- **Purpose**: Test LiveKit room management and agent deployment (NOT STT functionality)
- **Requirements**: LiveKit credentials (Yandex credentials only for full pipeline tests)
- **Scope**: Room creation/deletion, participant connections, agent deployment, LiveKit infrastructure
- **Run with**: `make test_e2e_agent`
- **Infrastructure**: Dedicated infrastructure modules for room management

### Development Testing Options

**For debugging individual tests with dependencies:**

When developing, you may want to run a specific test that depends on other tests without running the full dependency
chain. Use the `--ignore-unknown-dependency` flag:

```bash
# Run individual test ignoring missing dependencies (development only)
hatch run pytest tests/test_fixture_validation.py::TestFixtureValidation::test_audio_fixtures_available -v --ignore-unknown-dependency

# Run specific functional test without running fixture validation first
hatch run pytest tests/functional/test_stt.py::TestYandexSTTAudioProcessing::test_specific_method -v --ignore-unknown-dependency

# Run specific plugin E2E test
hatch run pytest tests/e2e/plugin_e2e/test_real_audio_processing.py::TestRealAudioProcessing::test_russian_audio_processing -v --ignore-unknown-dependency

# Run specific agent E2E test
hatch run pytest tests/e2e/agent_e2e/test_basic_livekit_integration.py::TestBasicLiveKitIntegration::test_basic_room_creation_and_cleanup -v --ignore-unknown-dependency
```

**Important Notes:**

- This flag should **only be used during development/debugging**
- Do **not** use this flag in CI/CD or production test runs
- The flag allows tests to run even if their dependencies haven't been validated
- Use this when you want to quickly test a specific piece of functionality during development

### Test Data

**Audio Fixtures:**
Generate test audio files using the fixture generator:

```bash
# Generate all fixtures (speech + basic audio)
make fixtures

# Generate only speech fixtures
make fixtures_speech

# Generate only basic fixtures (tones, noise)
make fixtures_basic

# List available TTS voices
make fixtures_voices
```

## Code Quality

### Linting and Formatting

The project uses multiple tools for code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Style guide enforcement
- **pylint**: Code analysis
- **mypy**: Type checking
- **docformatter**: Docstring formatting

```bash
# Check all linters
make lint

# Auto-fix issues
make lint_fix
```

### Type Checking

All public APIs must have type hints:

```python
from typing import Optional, Dict, Any
from livekit.agents import stt


def process_audio(
        audio_data: bytes,
        language: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
) -> stt.SpeechEvent:
    """Process audio data and return speech events."""
    ...
```

### Documentation Standards

- All public classes and methods must have docstrings
- Use Google-style docstrings
- Include type information in docstrings
- Provide usage examples for complex APIs

## Utilities and Tools

### Fixture Generator (`utils/fixture_generator.py`)

Unified tool for generating test audio files:

**Features:**

- Cross-platform TTS support (Windows SAPI, macOS say, Linux espeak)
- Basic audio generation (tones, noise, silence)
- Proper file naming with content descriptions
- Validation and reporting

**Requirements:**

- For Windows TTS: Install with `hatch run pip install -e ".[fixtures]"` (includes pywin32)
- For other platforms: Basic installation is enough

**Usage:**

```bash
# Generate all fixtures
python utils/fixture_generator.py --type all

# Generate only speech
python utils/fixture_generator.py --type speech

# Generate only basic audio
python utils/fixture_generator.py --type basic

# List TTS voices
python utils/fixture_generator.py --list-voices

# Custom output directory
python utils/fixture_generator.py --output-dir custom/path
```

### Makefile Commands

```bash
make help              # Show all available commands
make install           # Install development dependencies
make lint              # Check code quality
make lint_fix          # Auto-fix code issues
make test              # Run all tests
make test_unit         # Run unit tests only
make test_integration  # Run integration tests
make test_functional   # Run functional tests
make fixtures          # Generate test fixtures
make build             # Build the package
make clean             # Clean build artifacts
```

## Debugging

### Common Issues

**Import Errors:**

```bash
# Ensure package is installed in development mode
pip install -e .
```

**gRPC Issues:**

```bash
# Check if Yandex Cloud SDK is properly installed
hatch run python -c "from yandex.cloud.ai.stt.v3 import stt_pb2; print('Yandex Cloud SDK working')"
```

**Test Failures:**

```bash
# Check credentials
echo $YANDEX_API_KEY
echo $YANDEX_FOLDER_ID

# Generate test fixtures
make fixtures
```

### Debugging Tests

**Run specific tests:**

```bash
# Single test file
pytest tests/unit/test_stt.py -v

# Single test class
pytest tests/unit/test_stt.py::TestYandexCredentials -v

# Single test method
pytest tests/unit/test_stt.py::TestYandexCredentials::test_credentials_creation -v
```

**Debug with verbose output:**

```bash
pytest tests/ -v -s --tb=long
```

### Logging

Enable debug logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)

# Or for specific logger
logger = logging.getLogger("livekit.plugins.yandex")
logger.setLevel(logging.DEBUG)
```

## Agent Integration Testing

To test the plugin with LiveKit Agents in a real cloud environment:

1. **Set up LiveKit Cloud credentials**

   Add the following to your `.env` file:
   ```
   # LiveKit Cloud credentials
   LIVEKIT_API_KEY=your_livekit_api_key
   LIVEKIT_API_SECRET=your_livekit_api_secret
   LIVEKIT_WS_URL=wss://your-project.livekit.cloud
   ```

2. **Run agent integration tests**

   ```bash
   make test_agent
   ```

3. **Interpreting results**

   The tests validate:
    - Successful connection to LiveKit Cloud
    - Agent session creation with Yandex STT
    - Real-time audio processing
    - Transcription delivery
    - Session cleanup

4. **Troubleshooting**

    - Ensure both Yandex and LiveKit credentials are valid
    - **Check Yandex Cloud account balance** - E2E tests will fail if account balance is negative
    - Check network connectivity to both services

## Real LiveKit Cloud Integration Tests

This plugin includes comprehensive **REAL LiveKit Cloud integration tests** that provide complete end-to-end validation
of the LiveKit pipeline.

### 🎯 Live Dashboard Monitoring

All tests create rooms in **LiveKit Cloud** that can be monitored at: **https://cloud.livekit.io/projects/*/sessions**

#### Room Naming Convention

Tests use **descriptive room names** that indicate the test type and expected participant counts for easy debugging:

- **`test-simple-expect-0p-room-XXXXXXXX`** - Simple infrastructure tests with **0 participants expected**
- **`test-simple-expect-1p-room-XXXXXXXX`** - Simple connection tests with **1 participant expected**
- **`test-agent-expect-2p-room-XXXXXXXX`** - Agent tests with **2 participants expected** (agent and participant)

#### Dashboard Validation

When running tests, check the LiveKit dashboard to verify:

- ✅ **Participant count matches** the number in the room name
- ✅ **Room duration** reflects test execution time
- ✅ **Status shows "Closed"** after test completion
- ✅ **No resource leaks** (all rooms properly cleaned up)

#### ⚠️ Important Dashboard Limitations

**Dashboard Data Delay**: LiveKit Cloud dashboard may have **up to 30-minute delay** for:

- Participant count updates
- Session detail synchronization
- Room status changes

**Brief Connection Handling**: Tests with very short durations (1–3 seconds) may:

- Not appear in dashboard sampling
- Show 0 participants even if participants connected briefly
- This is **normal behavior** for quick infrastructure tests

### 🏗️ Complete Infrastructure

The LiveKit integration includes production-ready infrastructure components:

- **Real LiveKit rooms** - Actual room creation/deletion via LiveKit Cloud API
- **Real participant simulation** - WebSocket connections with threaded execution to avoid event loop conflicts
- **Real agent deployment** - Agents connect to rooms and process audio through a complete pipeline
- **Resource management** - Proper cleanup with session monitoring
- **Type-safe implementation** - Zero `Any` types, no `# type: ignore` comments

### 🧪 Running LiveKit Integration Tests

#### Basic Infrastructure Tests

```bash
# Recommended: Use Makefile target (stable, fast)
make test_livekit_basic

# Or run individual tests manually:
# Test room creation/deletion (0 participants expected)
hatch run pytest tests/e2e_agent/test_basic_livekit_integration.py::TestBasicLiveKitIntegration::test_basic_room_creation_and_cleanup -v

# Test participant connection (1 participant expected)
hatch run pytest tests/e2e_agent/test_basic_livekit_integration.py::TestBasicLiveKitIntegration::test_participant_connection_to_room -v

# Note: Full test suite includes complex agent tests that may hang
# Use make test_livekit_basic for stable infrastructure testing
```

#### Monitoring Results

After running tests, check the LiveKit Cloud dashboard:

1. **Go to**: https://cloud.livekit.io/projects/*/sessions
2. **Look for rooms** with descriptive names like `test-simple-expect-1p-room-abc12345`
3. **Verify participant counts** match the expected number in the room name
4. **Check duration** reflects test execution time
5. **Confirm status** shows "Closed" after completion

### 🔧 Troubleshooting LiveKit Integration

**Issue**: Room shows 0 participants but test passed

- **Cause**: Very brief connection (< 3 seconds) not captured by dashboard sampling
- **Solution**: This is normal for quick infrastructure tests

**Issue**: Room not visible in the dashboard

- **Cause**: Dashboard sync delay (up to 30 minutes)
- **Solution**: Wait or check test logs for room creation confirmation

**Issue**: Participant count mismatch

- **Cause**: Timing issues or cleanup order
- **Solution**: Check test logs for connection/disconnection events

**Issue**: Tests fail with connection errors

- **Cause**: LiveKit credentials or network issues
- **Solution**: Verify `.env` file has correct LiveKit Cloud credentials

**Issue**: E2E tests fail with Yandex API errors

- **Cause**: Negative Yandex Cloud account balance
- **Solution**: Top up your Yandex Cloud account balance before running E2E tests

### 🔮 Future Improvements (TODO)

- **Yandex Account Balance Verification**: Implement automatic balance checks before running E2E tests
- **Balance-dependent Test Skipping**: Skip E2E tests automatically when account balance is insufficient
- **Balance Monitoring**: Add balance monitoring and warnings in test output

### 🎯 What This Enables

**TRUE end-to-end validation** of the complete LiveKit pipeline:
**Participant → Room → Agent → STT → Transcription**

This infrastructure provides the foundation for comprehensive agent testing with Russian STT processing in real LiveKit
environments.

- Verify audio fixtures are available
- Enable DEBUG logging for detailed information

## Contributing

### Before Submitting

1. **Run full test suite:**
   ```bash
   make test
   ```

2. **Check code quality:**
   ```bash
   make lint
   ```

3. **Update documentation:**
    - Update README.md for user-facing changes
    - Update DEVELOPMENT.md for development changes
    - Add docstrings for new APIs

4. **Clean up:**
   ```bash
   make clean
   ```

### Commit Guidelines

- Use clear, descriptive commit messages
- Reference issue numbers when applicable
- Keep commits focused and atomic
- Test before committing

### Pull Request Process

1. Fork the repository on GitHub
2. Create feature branch from main
3. Make changes with tests
4. Update documentation
5. Run full test suite
6. Submit pull request with description to this repository

**Important**: Submit issues and pull requests to this project's repository at:
https://github.com/sergerdn/livekit-plugins-yandex

## Environment Variables

**Required for Integration/Functional Tests:**

- `YANDEX_API_KEY`: Your Yandex Cloud API key
- `YANDEX_FOLDER_ID`: Your Yandex Cloud folder ID

**Optional:**

- `YANDEX_STT_ENDPOINT`: Custom STT endpoint (defaults to Yandex Cloud)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Performance Considerations

- STT initialization is lightweight (< 100ms)
- Streaming sessions have minimal overhead
- Audio processing is done by Yandex Cloud
- Network latency affects real-time performance
- Consider connection pooling for high-volume usage

## Security Notes

- Never commit credentials to version control
- Use environment variables for sensitive data
- Rotate API keys regularly
- Monitor API usage and costs
- Use least-privilege access for Yandex Cloud resources

## External API Documentation

For developers looking to understand the underlying Yandex SpeechKit API in more detail, especially for advanced
scenarios not directly covered by this plugin's abstractions, the following resources may be helpful:

- **Streaming audio from a microphone (Official Yandex Cloud Docs - Russian):**
  [https://github.com/yandex-cloud/docs/blob/master/ru/speechkit/stt/api/microphone-streaming.md](https://github.com/yandex-cloud/docs/blob/master/ru/speechkit/stt/api/microphone-streaming.md)
  This document provides insights into direct microphone input with the SpeechKit API, which can be useful for debugging
  or extending plugin capabilities.
