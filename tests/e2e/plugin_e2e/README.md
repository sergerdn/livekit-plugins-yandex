# Plugin-level End-to-End Tests

This directory contains end-to-end tests for the **Yandex SpeechKit STT plugin functionality** with real Yandex Cloud
API integration.

## 🎯 Purpose

These tests validate the **STT plugin functionality** by making actual API calls to Yandex Cloud SpeechKit service.

They focus on:

- **Audio processing**: Real audio file handling and streaming
- **Transcription accuracy**: Speech recognition quality with different languages
- **STT streaming**: Session management and real-time processing
- **Error handling**: API error scenarios and edge cases
- **Performance analysis**: Processing speed and resource usage

## 🔧 Requirements

### **Credentials (Required)**

- `YANDEX_API_KEY`: Your Yandex Cloud API key
- `YANDEX_FOLDER_ID`: Your Yandex Cloud folder ID

### **Audio Files (Required)**

- Audio fixture files in `tests/fixtures/` directory
- Run `make fixtures` to generate test audio files

### **Network (Required)**

- Internet connectivity to Yandex Cloud API endpoints
- No LiveKit infrastructure required

## 🚀 Running Tests

### **All Plugin E2E Tests**

```bash
make test_e2e_plugin
```

### **Individual Test Categories**

```bash
# English audio processing
hatch run pytest tests/e2e/plugin_e2e/test_real_audio_processing.py::TestRealAudioProcessing::test_english_audio_processing -v

# Russian audio processing  
hatch run pytest tests/e2e/plugin_e2e/test_real_audio_processing.py::TestRealAudioProcessing::test_russian_audio_processing -v

# Performance analysis
hatch run pytest tests/e2e/plugin_e2e/test_real_audio_processing.py::TestRealAudioProcessing::test_performance_analysis -v

# Error handling
hatch run pytest tests/e2e/plugin_e2e/test_real_audio_processing.py::TestRealAudioProcessing::test_error_handling -v
```

### **Development Mode**

```bash
# Run individual test with detailed output
hatch run pytest tests/e2e/plugin_e2e/test_real_audio_processing.py::TestRealAudioProcessing::test_russian_audio_processing -v --ignore-unknown-dependency
```

## 📋 Test Categories

### **🎵 Audio Processing Tests**

- **Purpose**: Validate STT with real audio files
- **Languages**: English (en-US), Russian (ru-RU), Mixed languages
- **Audio Types**: Greetings, weather descriptions, learning phrases
- **Validation**: Transcription accuracy, confidence scores, processing time

### **⚡ Performance Analysis**

- **Purpose**: Measure STT processing performance
- **Metrics**: Processing time, file size handling, throughput
- **Thresholds**: Maximum processing time limits
- **Analysis**: Average performance across multiple files

### **🛡️ Error Handling**

- **Purpose**: Test STT behavior with invalid inputs
- **Scenarios**: Invalid credentials, unsupported languages, malformed requests
- **Validation**: Proper exception handling and error messages

## 📊 Expected Outcomes

### **Successful Test Run**

```
Starting End-to-End Tests for Yandex SpeechKit STT Plugin
======================================================================
Credentials available
API Key: sk-xxxxxxxxxxxxxxx...
Folder ID: b1gxxxxxxxxxxxxxxxxx
Audio fixtures: 8 files available
   english_greeting.wav: 178.9 KB
   russian_greeting.wav: 198.1 KB
   ...

================= test session starts =================
tests/e2e/plugin_e2e/test_real_audio_processing.py::TestRealAudioProcessing::test_english_audio_processing PASSED
tests/e2e/plugin_e2e/test_real_audio_processing.py::TestRealAudioProcessing::test_russian_audio_processing PASSED
tests/e2e/plugin_e2e/test_real_audio_processing.py::TestRealAudioProcessing::test_performance_analysis PASSED
tests/e2e/plugin_e2e/test_real_audio_processing.py::TestRealAudioProcessing::test_error_handling PASSED

================= 4 passed in 15.23s =================
All e2e tests passed - plugin is working correctly with real Yandex Cloud API!
======================================================================
```

### **Test Failure Scenarios**

- **Missing credentials**: Tests will be skipped with a clear message
- **Network issues**: Connection errors with retry suggestions
- **API errors**: Authentication or quota limit messages
- **Audio file issues**: Missing fixtures with generation instructions

## 🔍 Test Infrastructure

### **Fixtures**

- **`real_credentials`**: Loads Yandex Cloud credentials from environment
- **`audio_fixtures`**: Discovers and loads available audio test files
- **Global fixtures**: Uses shared fixtures from `tests/conftest.py`

### **Test Utilities**

- **`AudioProcessingResult`**: Container for test results and metrics
- **`estimate_audio_duration`**: Audio file duration estimation
- **`process_audio_file`**: Core audio processing workflow

### **Session Management**

- **Automatic marking**: Tests marked as `@pytest.mark.e2e` and `@pytest.mark.slow`
- **Session info**: Displays credentials and fixture availability
- **Result summary**: Shows test outcomes and API connectivity status

## 🎯 Scope and Limitations

### **✅ What These Tests Cover**

- STT plugin functionality with real Yandex Cloud API
- Audio file processing and streaming session management
- Multi-language support (English, Russian)
- Error handling and edge cases
- Performance characteristics

### **❌ What These Tests Do NOT Cover**

- LiveKit room management (see `tests/e2e/agent_e2e/`)
- Agent deployment and lifecycle
- Participant simulation and WebSocket connections
- Real-time audio streaming from microphones
- LiveKit infrastructure integration

## ⚠️ Test Failure Behavior

**IMPORTANT**: Plugin E2E tests are designed to FAIL (not skip) when required infrastructure is missing. This provides
clear feedback about missing requirements.

### **Expected Failures**

**Missing Yandex Credentials**

```
OSError: Yandex Cloud credentials required for plugin E2E tests.
Set YANDEX_API_KEY and YANDEX_FOLDER_ID environment variables.
See DEVELOPMENT.md for setup instructions.
```

**Missing Audio Fixtures Directory**

```
FileNotFoundError: Audio fixtures directory not found: tests/fixtures.
Run 'make fixtures' to generate test audio files.
See DEVELOPMENT.md for setup instructions.
```

**Missing Specific Audio Files**

```
FileNotFoundError: No audio fixture files found. Run 'make fixtures' to generate test audio files.
Required files: russian_greeting.wav, english_greeting.wav, etc.
See DEVELOPMENT.md for complete setup instructions.
```

## ⚠️ Test Failure Behavior

**IMPORTANT**: Plugin E2E tests are designed to FAIL (not skip) when required infrastructure is missing.

### **Expected Failures**

**Missing Yandex Credentials**

```
OSError: Yandex Cloud credentials required for plugin E2E tests.
Set YANDEX_API_KEY and YANDEX_FOLDER_ID environment variables.
```

**Missing Audio Fixtures**

```
FileNotFoundError: Audio fixtures directory not found: tests/fixtures.
Run 'make fixtures' to generate test audio files.
```

## 🔧 Troubleshooting

### **Common Issues**

**Missing Credentials**

```bash
# Set environment variables
export YANDEX_API_KEY="your-api-key"
export YANDEX_FOLDER_ID="your-folder-id"
```

**Missing Audio Files**

```bash
# Generate test audio fixtures
make fixtures
```

**Network Connectivity**

- Ensure internet access to `stt.api.cloud.yandex.net`
- Check firewall settings for HTTPS/gRPC traffic
- Verify Yandex Cloud service availability

**Yandex Cloud Account Balance**

⚠️ **CRITICAL**: Tests require a **positive account balance** to function properly.

- **Check balance**: [Yandex Cloud Console](https://console.cloud.yandex.com) → Billing → Account balance

**API Quota Limits**

- Check Yandex Cloud console for usage limits
- Verify the billing account status is active
- Consider rate limiting in test execution

## 📚 Related Documentation

- **Agent E2E Tests**: `tests/e2e/agent_e2e/README.md` - LiveKit integration tests
- **Test Suite Refactoring**: `tests/TEST_SUITE_REFACTORING.md` - Complete test organization
- **Development Guide**: `DEVELOPMENT.md` - Setup and development workflow
- **Main README**: `README.md` - Project overview and quick start

---

**Note**: These tests require real Yandex Cloud credentials and make actual API calls.

They are designed to validate the complete STT plugin functionality in a real-world environment.
