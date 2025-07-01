# Test Suite Documentation

This document describes the test organization and types in the Yandex SpeechKit STT plugin test suite.

## Test Directory Structure

```
tests/
├── README.md                      # This file - test documentation
├── test_fixture_validation.py    # Consolidated fixture validation tests
├── conftest.py                    # Global test configuration and fixtures
├── __init__.py                    # Test package initialization
├── unit/                          # Unit tests (no external dependencies)
├── integration/                   # Integration tests (requires credentials)
├── functional/                    # Functional tests (mocked external services)
├── e2e/                          # End-to-end tests (real API calls)
├── e2e_agent/                    # LiveKit agent integration tests
└── fixtures/                     # Audio test fixtures
```

## Test Type Distinctions

### **Unit Tests** (`tests/unit/`)

- **Purpose**: Test individual components in isolation
- **Dependencies**: None (no external services, no credentials)
- **Speed**: Very fast (milliseconds)
- **Reliability**: Very high (no external dependencies)
- **Examples**:
    - STT class initialization and configuration
    - Credential validation logic
    - Utility function testing
    - Error handling for invalid inputs

### **Integration Tests** (`tests/integration/`)

- **Purpose**: Test component interactions with minimal external dependencies
- **Dependencies**: May require credentials for configuration
- **Speed**: Fast (seconds)
- **Reliability**: High (minimal external dependencies)
- **Examples**:
    - STT instance creation with real credentials
    - Configuration validation with environment variables
    - Component interaction testing

### **Functional Tests** (`tests/functional/`)

- **Purpose**: Test application functionality with mocked/stubbed external services
- **Dependencies**: May require credentials for configuration but should **NOT make real API calls**
- **Speed**: Fast to moderate (seconds)
- **Reliability**: High (no network dependencies)
- **Focus**: Testing business logic, data flow, and component interaction
- **Examples**:
    - STT stream creation and configuration
    - Audio file loading and validation
    - Error handling scenarios
    - Performance testing with mocked services

### **End-to-End Tests** (`tests/e2e/`)

- **Purpose**: Test complete workflows with real external API calls
- **Dependencies**:
    - Real Yandex Cloud credentials (`YANDEX_API_KEY`, `YANDEX_FOLDER_ID`)
    - Network connectivity to Yandex SpeechKit service
    - Audio fixture files
- **Speed**: Slow (seconds to minutes)
- **Reliability**: Moderate (depends on network and service availability)
- **Focus**: Test actual integration with Yandex SpeechKit service
- **Examples**:
    - Real audio transcription with Russian and English files
    - API error handling with invalid credentials
    - Performance analysis with real service calls
    - Service timeout and retry logic

### **E2E Agent Tests** (`tests/e2e_agent/`)

- **Purpose**: Test complete LiveKit agent workflows with real services
- **Dependencies**:
    - Yandex Cloud credentials (`YANDEX_API_KEY`, `YANDEX_FOLDER_ID`)
    - LiveKit credentials (`LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `LIVEKIT_WS_URL`)
    - Network connectivity to both services
    - Audio fixture files
- **Speed**: Very slow (minutes)
- **Reliability**: Lower (depends on multiple external services)
- **Focus**: Most complex and comprehensive integration testing
- **Examples**:
    - Complete participant → room → agent → STT → transcription pipeline
    - Real LiveKit room creation and management
    - Participant simulation with audio streaming
    - Agent deployment and lifecycle management

## Test Execution

### Running Specific Test Types

```bash
# Run all tests
make test

# Run only unit tests (fastest)
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Run only functional tests
pytest tests/functional/ -v

# Run only e2e tests (requires credentials)
pytest tests/e2e/ -v

# Run only e2e agent tests (requires all credentials)
pytest tests/e2e_agent/ -v

# Run fixture validation tests
pytest tests/test_fixture_validation.py -v
```

### Test Dependencies

Tests use `pytest-dependency` markers to ensure proper execution order:

- **Fixture validation tests** run first (no dependencies)
- **Functional and E2E tests** depend on fixture validation passing
- If fixture validation fails, dependent tests are automatically skipped

## Environment Setup

### Required Environment Variables

**For Integration/Functional Tests:**

```bash
YANDEX_API_KEY=your_yandex_api_key
YANDEX_FOLDER_ID=your_yandex_folder_id
```

**For E2E Tests (additional):**

- Same as above, plus network connectivity to Yandex Cloud

**For E2E Agent Tests (additional):**

```bash
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
LIVEKIT_WS_URL=wss://your-livekit-server.com
```

### Audio Fixtures

Audio test files are located in `tests/fixtures/`:

- `russian_*.wav` - Russian language audio samples
- `english_*.wav` - English language audio samples
- `mixed_languages.wav` - Mixed language content
- `silence.wav` - Silent audio for edge case testing

Run `make fixtures` to generate test audio files if they don't exist.

## Test Markers

The test suite uses pytest markers for organization:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.functional` - Functional tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Tests that take longer to run
- `@pytest.mark.dependency` - Tests with dependencies on other tests

## Best Practices

1. **Start with unit tests** - They're fastest and catch basic issues
2. **Use functional tests** for business logic validation without external calls
3. **Reserve e2e tests** for actual service integration validation
4. **Keep e2e agent tests** for comprehensive pipeline validation
5. **Ensure fixture validation passes** before running dependent tests
6. **Use appropriate test markers** for selective test execution

## Troubleshooting

### Common Issues

**Tests skipped due to missing credentials:**

- Ensure environment variables are set in `.env` file
- Check that credentials are valid and have proper permissions

**Audio fixture tests failing:**

- Run `make fixtures` to generate test audio files
- Ensure `tests/fixtures/` directory exists and is readable

**E2E tests timing out:**

- Check network connectivity to external services
- Verify service endpoints are accessible
- Consider increasing timeout values for slow networks

**Agent tests failing:**

- Ensure both Yandex and LiveKit credentials are valid
- Check that LiveKit server is accessible
- Verify audio fixtures are available and valid
