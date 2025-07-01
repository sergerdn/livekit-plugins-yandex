# Yandex SpeechKit STT Plugin for LiveKit Agents

> **⚠️ IMPORTANT DISCLAIMER**
> This is an **independent, community-developed plugin** and is
> **NOT officially affiliated with or endorsed by LiveKit or Yandex**.
>
> This project is **NOT part of either the official LiveKit or Yandex ecosystems**.          
> For issues, support, or contributions related to this plugin, please use this project's repository directly.         
> Do not use LiveKit's or Yandex's official support channels for plugin-specific matters.

This plugin provides Yandex SpeechKit Speech-to-Text (STT) integration for LiveKit Agents, enabling real-time Russian
and English speech recognition.

## Features

- **Real-time streaming STT** using Yandex SpeechKit v3 API
- **Multi-language support** with a primary focus on Russian and English
- **Automatic language detection** capabilities
- **Interim results** for responsive user experience
- **Profanity filtering** and text normalization options
- **Seamless LiveKit integration** following established plugin patterns

## 🧪 End-to-End Testing

> **🎉 BONUS FEATURE!**
>
> This plugin goes **WAY BEYOND** basic STT functionality by including a **COMPREHENSIVE E2E TESTING INFRASTRUCTURE**
> with **REAL LiveKit Cloud integration**!
>
> **This is NOT your typical plugin** - you're getting testing capabilities that most plugins simply don't offer.
>
> This exceptional testing infrastructure validates the **COMPLETE PIPELINE** from audio input to LiveKit
> room management, giving you confidence that everything works together seamlessly.

**What makes this special:**

- ✨ **Real LiveKit Cloud rooms** - Not mocked, not simulated - **ACTUAL** cloud infrastructure testing
- ✨ **Complete agent lifecycle testing** - Full room creation, participant management, and cleanup
- ✨ **Production-ready validation** - Test the exact same pipeline your users will experience
- ✨ **Professional debugging tools** - Descriptive room naming and dashboard monitoring
- ✨ **Zero setup complexity** - Provide your LiveKit credentials and run the tests

### Room Naming Convention

Tests use **descriptive room names** that indicate the test type and expected participant counts for easy debugging:

- **`test-simple-expect-0p-room-XXXXXXXX`** - Simple infrastructure tests with **0 participants expected**
- **`test-simple-expect-1p-room-XXXXXXXX`** - Simple connection tests with **1 participant expected**
- **`test-agent-expect-2p-room-XXXXXXXX`** - Agent tests with **2 participants expected** (agent and participant)

![cloud.livekit.io_sessions.png](docs/images/cloud.livekit.io_sessions.png)

### ⚠️ Important: Account Balance Requirements

**Before running E2E tests**, ensure your **Yandex Cloud account has a positive balance**. Tests will fail with
authentication errors if your account balance is negative or insufficient.

**🚀 Ready to test like a pro?** See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed testing information and LiveKit Cloud
dashboard monitoring.

## Installation

### Prerequisites

Ensure your system meets the following requirements:

- **Git**: [Download Git](https://git-scm.com/downloads) if not already installed.
- **Python 3.9+**: Ensure Python is installed and configured correctly (matches LiveKit Agents requirement)
- **Hatch**: Install modern, extensible Python project manager [Hatch](https://hatch.pypa.io/latest/).

### Official Yandex Cloud SDK Integration

This plugin uses the **official Yandex Cloud SDK** - which provides:

- **Official protobuf definitions** for Yandex SpeechKit API v3
- **Proper gRPC stubs** maintained by Yandex Cloud team
- **Full API compatibility** with the latest Yandex Cloud features
- **Automatic updates** when new API versions are released

**No custom stub generation required** - the plugin automatically uses the official API definitions.

### Install the Plugin

**Clone this repository:**

```bash
git clone git@github.com:sergerdn/livekit-plugins-yandex.git
cd livekit-plugins-yandex
```

**Install using Hatch:**

To install the plugin, it's recommended to build the wheel using Hatch and then install it.

This is the standard way to distribute and install Hatch-managed Python projects.

```bash
# Ensure Hatch is installed (pipx install hatch)
hatch build
# The wheel will be in the dist/ folder
# You can then install it using pip (globally or in a virtual environment)
# For example:
pip install dist/livekit_plugins_yandex-*.whl
```

For development, you would typically set up a Hatch environment:

```bash
# This creates or updates a virtual environment managed by Hatch
# and installs dependencies, including the plugin in editable mode.
hatch env create
# To run commands within this environment:
hatch shell
# Or prefix commands with `hatch run`:
# hatch run python your_script.py
```

Refer to [`DEVELOPMENT.md`](DEVELOPMENT.md) for more detailed development setup instructions.

## Configuration

### Environment Variables Setup

The plugin requires Yandex Cloud credentials to function. You can configure these using environment variables.

#### Method 1: Using .env File (Recommended)

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file** with your credentials:
   ```bash
   # Required - Yandex Cloud credentials
   YANDEX_API_KEY=your_service_account_api_key_here
   YANDEX_FOLDER_ID=your_folder_id_here

   # Optional - Yandex STT configuration (uncomment to customize)
   # YANDEX_STT_ENDPOINT=stt.api.cloud.yandex.net:443
   # YANDEX_STT_LANGUAGE=ru-RU
   # YANDEX_STT_MODEL=general
   # YANDEX_STT_DEBUG=false

   # Required for E2E agent testing only
   # LIVEKIT_WS_URL=wss://your-project.livekit.cloud
   # LIVEKIT_API_KEY=your_livekit_api_key
   # LIVEKIT_API_SECRET=your_livekit_api_secret
   ```

#### Method 2: Direct Environment Variables

You can also set environment variables directly in your shell:

```bash
# Required - Yandex Cloud credentials
export YANDEX_API_KEY="your_service_account_api_key_here"
export YANDEX_FOLDER_ID="your_folder_id_here"

# Optional - STT configuration
export YANDEX_STT_ENDPOINT="stt.api.cloud.yandex.net:443"
export YANDEX_STT_LANGUAGE="ru-RU"
export YANDEX_STT_MODEL="general"
export YANDEX_STT_DEBUG="false"

# For E2E agent testing only
export LIVEKIT_WS_URL="wss://your-project.livekit.cloud"
export LIVEKIT_API_KEY="your_livekit_api_key"
export LIVEKIT_API_SECRET="your_livekit_api_secret"
```

#### Environment Variables Reference

**Yandex Cloud Configuration:**

| Variable              | Required | Default                        | Description                                  |
|-----------------------|----------|--------------------------------|----------------------------------------------|
| `YANDEX_API_KEY`      | ✅ Yes    | None                           | Service account API key (**not IAM token**)  |
| `YANDEX_FOLDER_ID`    | ✅ Yes    | None                           | Yandex Cloud folder ID                       |
| `YANDEX_STT_ENDPOINT` | ❌ No     | `stt.api.cloud.yandex.net:443` | gRPC endpoint for SpeechKit API              |
| `YANDEX_STT_LANGUAGE` | ❌ No     | `ru-RU`                        | Default language (ru-RU, en-US, tr-TR, etc.) |
| `YANDEX_STT_MODEL`    | ❌ No     | `general`                      | Recognition model (general, premium)         |
| `YANDEX_STT_DEBUG`    | ❌ No     | `false`                        | Enable debug logging for STT operations      |

**LiveKit Cloud Configuration (for E2E testing):**

| Variable             | Required | Default | Description                                              |
|----------------------|----------|---------|----------------------------------------------------------|
| `LIVEKIT_WS_URL`     | 🧪 E2E   | None    | LiveKit WebSocket URL (wss://your-project.livekit.cloud) |
| `LIVEKIT_API_KEY`    | 🧪 E2E   | None    | LiveKit Cloud API key for agent testing                  |
| `LIVEKIT_API_SECRET` | 🧪 E2E   | None    | LiveKit Cloud API secret for agent testing               |

**Development Configuration:**

| Variable    | Required | Default | Description                                 |
|-------------|----------|---------|---------------------------------------------|
| `LOG_LEVEL` | ❌ No     | `INFO`  | Logging level (DEBUG, INFO, WARNING, ERROR) |

**Legend:**

- ✅ **Required**: Must be set for basic plugin functionality
- 🧪 **E2E**: Required only for end-to-end agent testing (`make test_e2e_agent`)
- ❌ **Optional**: Has sensible defaults, can be customized if needed

#### Authentication Notes

- **✅ Supported**: API Key authentication only
- **❌ Not Supported**: IAM token authentication
- **Security**: Never commit `.env` files to version control

### Yandex Cloud Setup

Before using this plugin, you need to set up a Yandex Cloud account and obtain API credentials:

#### Prerequisites

1. **Create a Yandex Cloud account** at [yandex.cloud](https://yandex.cloud)
2. **Create a folder** in your Yandex Cloud console
3. **Set up API authentication** (API key method only - IAM authentication is not supported)

#### Step-by-Step Setup

**📖 Quick Start Guide**: Follow the
official [Yandex Cloud SpeechKit Quick Start](https://yandex.cloud/en/docs/speechkit/quickstart/) for complete setup
instructions, including API key creation.

#### Required Steps:

1. **Create Yandex Cloud Account**
    - Go to [yandex.cloud](https://yandex.cloud)
    - Sign up or log in to your account

2. **Create a Cloud Folder**
    - In the Yandex Cloud console, create a new folder
    - Note the folder ID (you'll need this for configuration)

3. **Create Service Account**
    - Create a service account with SpeechKit permissions
    - Assign the `speechkit.stt` role to the service account

4. **Generate API Key**
    - Create an API key for your service account
    - **Important**: Only API key authentication is supported (**IAM tokens are not supported**)
    - Save the API key securely

#### Authentication Method

**✅ Supported**: API Key authentication
**❌ Not Supported**: IAM token authentication

Make sure to use the API key method when following Yandex Cloud documentation.

### Security Note

⚠️ **Important**: Never commit your `.env` file to version control. The `.env` file is already included in `.gitignore`
to prevent accidental commits of sensitive credentials.

## Usage

### Basic Usage

```python
from livekit.agents import AgentSession
from livekit.plugins import yandex

# Create an STT instance optimized for real-time streaming
stt = yandex.STT(
    language="ru-RU",  # Russian
    interim_results=True,  # Enable real-time partial results (recommended)
)

# Use in LiveKit Agent for real-time streaming
agent = AgentSession(
    stt=stt,
    # ... other configuration
)
```

### Manual Credentials

```python
from livekit.plugins import yandex

# Explicitly provide credentials
stt = yandex.STT(
    language="ru-RU",
    api_key="your_api_key",
    folder_id="your_folder_id"
)
```

### Advanced Configuration

```python
from livekit.plugins import yandex

# Optimized for real-time streaming with language detection
stt = yandex.STT(
    detect_language=True,
    interim_results=True,  # Essential for real-time UX
    profanity_filter=True,
    model="general"
)

# English-only real-time recognition
stt = yandex.STT(
    language="en-US",
    interim_results=True,  # Always enable for streaming
    model="general",
    sample_rate=16000
)

# High-performance streaming configuration
stt = yandex.STT(
    language="ru-RU",
    interim_results=True,  # Real-time partial results
    profanity_filter=False,  # Disable for lower latency
    sample_rate=16000,  # Standard for real-time audio
)
```

### Real-Time Streaming Recognition

**Primary Use Case**: This plugin is designed for **real-time streaming audio processing**, not batch file processing.

#### Working Examples

For complete, working examples of proper streaming implementation, see:

- **[`example_plugin_usage.py`](example_plugin_usage.py)** - Comprehensive demonstration script showing:
    - ✅ Real-time streaming with `push_frame()` method
    - ✅ Emulated streaming from audio files (for testing)
    - ✅ Simulated live audio processing (like microphone input)
    - ❌ Batch processing comparison (shows why it's discouraged)

- **[`tests/e2e/plugin_e2e/test_real_audio_processing.py`](tests/e2e/plugin_e2e/test_real_audio_processing.py)** -
  Plugin-level E2E tests with real Yandex Cloud API calls
- **[`tests/e2e/agent_e2e/`](tests/e2e/agent_e2e/)** - Agent-level E2E tests with LiveKit integration

#### Key Streaming Patterns

The examples demonstrate the correct patterns for:

- Creating streaming sessions with `stt.stream()`
- Processing audio frames with `stream.push_frame(frame)`
- Handling interim and final results asynchronously
- Proper session management and cleanup

#### Streaming vs. Batch Processing

**✅ Recommended: Real-Time Streaming**

- Process audio frames as they arrive using `push_frame()`
- Get immediate interim results for responsive UX
- Handle long audio streams efficiently

**❌ Discouraged: Batch File Processing**

- Loading entire audio files defeats real-time benefits
- No interim results = poor user experience
- Higher memory usage and latency

**Run the examples:**

```bash
# See all streaming patterns in action
python example_plugin_usage.py

# Run plugin-level E2E tests (STT functionality)
make test_e2e_plugin

# Run agent-level E2E tests (LiveKit integration)
make test_e2e_agent

# Run all E2E tests
make test_e2e
```

## Supported Languages

Primary languages with full support:

- **Russian** (`ru-RU`)
- **English** (`en-US`)

Additional supported languages:

- Turkish (`tr-TR`)
- Kazakh (`kk-KK`)
- Uzbek (`uz-UZ`)
- Armenian (`hy-AM`)
- Hebrew (`he-IL`)
- Arabic (`ar`)
- And many more...

## Configuration Options

| Parameter          | Type   | Default                          | Description                            |
|--------------------|--------|----------------------------------|----------------------------------------|
| `model`            | `str`  | `"general"`                      | Recognition model (general, premium)   |
| `language`         | `str`  | `"ru-RU"`                        | Language code (ru-RU, en-US, etc.)     |
| `detect_language`  | `bool` | `False`                          | Auto language detection                |
| `interim_results`  | `bool` | `True`                           | Enable interim results                 |
| `profanity_filter` | `bool` | `False`                          | Filter profanity                       |
| `sample_rate`      | `int`  | `16000`                          | Audio sample rate (8000, 16000, 48000) |
| `api_key`          | `str`  | `None`                           | Yandex Cloud API key                   |
| `folder_id`        | `str`  | `None`                           | Yandex Cloud folder ID                 |
| `grpc_endpoint`    | `str`  | `"stt.api.cloud.yandex.net:443"` | gRPC endpoint for SpeechKit API        |

## Error Handling

The plugin includes comprehensive error handling for:

- **Authentication failures** (invalid API keys/tokens)
- **Network connectivity issues** (timeouts, connection drops)
- **Rate limiting** (quota exceeded)
- **Audio format validation** (unsupported formats)
- **gRPC communication errors** (service unavailable)

## Development Setup

### For Contributors

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development setup instructions.

## Development

For detailed development information, see [DEVELOPMENT.md](DEVELOPMENT.md).

**Quick Start:**

```bash
# Install development dependencies
make install

# Run tests
make test_unit

# Generate test fixtures
make fixtures

# Check code quality
make lint
```

## Development Status

**This plugin is ready for development and testing.**

**Completed Features:**

- Complete project structure and configuration
- Authentication system with API key support
- Full STT interface implementation
- gRPC streaming implementation using official Yandex Cloud SDK
- Comprehensive test suite (unit, integration, functional, e2e)
- Audio fixture generation tools
- Code quality tools and linting
- Development documentation and workflows
- Cross-platform support (Windows, macOS, Linux)

**Ready for:**

- Real audio processing and testing
- Integration with LiveKit applications
- Production deployment (with proper credentials)

**Development Tools:**

- Unified fixture generator for test audio
- Comprehensive test suite with proper isolation
- Code quality enforcement (linting, formatting, type checking)
- Cross-platform development support

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork this repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

For development setup, see [DEVELOPMENT.md](DEVELOPMENT.md).

## License

This plugin is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/sergerdn/livekit-plugins-yandex/issues) - Report bugs or request
  features for this plugin
- **LiveKit Documentation**: [LiveKit Docs](https://docs.livekit.io) - For general LiveKit Agents documentation
- **LiveKit Community**: [LiveKit Discord](https://livekit.io/discord) - For general LiveKit support (not
  plugin-specific issues)
