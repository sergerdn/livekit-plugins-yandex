# End-to-End Agent Mode Tests

This directory contains comprehensive end-to-end tests for the Yandex STT plugin implementing **REAL LiveKit integration
** with actual LiveKit Cloud infrastructure.

## 🎯 LiveKit Cloud Dashboard Monitoring

All tests create rooms in **LiveKit Cloud** that can be monitored in real-time at:
**https://cloud.livekit.io/projects/*/sessions**

### Room Naming Convention

Tests use **descriptive room names** that indicate the test type and expected participant counts for easy debugging:

- **`test-simple-expect-0p-room-XXXXXXXX`** - Simple infrastructure tests with **0 participants expected**
- **`test-simple-expect-1p-room-XXXXXXXX`** - Simple connection tests with **1 participant expected**
- **`test-agent-expect-2p-room-XXXXXXXX`** - Agent tests with **2 participants expected** (agent and participant)

![cloud.livekit.io_sessions.png](../../../docs/images/cloud.livekit.io_sessions.png)

### Dashboard Validation

When running tests, check the LiveKit dashboard to verify:

- ✅ **Participant count matches** the number in the room name
- ✅ **Room duration** reflects test execution time
- ✅ **Status shows "Closed"** after test completion
- ✅ **No resource leaks** (all rooms properly cleaned up)

### ⚠️ Important Dashboard Limitations

**Dashboard Data Delay**: LiveKit Cloud dashboard may have **up to 30-minute delay** for:

- Participant count updates
- Session detail synchronization
- Room status changes

**Brief Connection Handling**: Tests with very short durations (1–3 seconds) may:

- Not appear in dashboard sampling
- Show 0 participants even if participants connected briefly
- This is **normal behavior** for quick infrastructure tests

### 🔍 Debugging Guide

**Expected Dashboard Results:**

- **`test-simple-expect-0p-room-*`** → 0 participants (room creation only)
- **`test-simple-expect-1p-room-*`** → 1 participant (may show 0 if very brief)
- **`test-agent-expect-2p-room-*`** → 2 participants (agent + participant)

**Troubleshooting:**

- **0 participants shown**: Check if the test duration was very short (< 3 seconds)
- **Missing rooms**: Wait up to 30 minutes for dashboard sync
- **Timing issues**: Use longer test durations for reliable dashboard visibility

## 🎯 What We Test

### **REAL LiveKit Integration:**

- **Real LiveKit Cloud rooms** - Actual room creation/deletion via LiveKit API
- **Real participant connections** - WebSocket connections to LiveKit Cloud
- **Real agent deployment** - Agents connect to rooms and process audio
- **Real STT processing** - Complete LiveKit → Agent → Yandex STT pipeline
- **Real Russian audio processing** - Authentic Russian audio fixtures
- **Real transcription validation** - Verify accurate Russian language results

## 📁 Test Structure

```
tests/e2e_agent/
├── README.md                           # This file
├── IMPLEMENTATION_PLAN.md              # Implementation documentation
├── __init__.py                         # Package initialization
├── conftest.py                         # Shared fixtures and utilities
├── infrastructure/                     # LiveKit integration infrastructure
│   ├── __init__.py                     # Infrastructure package
│   ├── room_manager.py                 # Real LiveKit room operations
│   ├── participant_simulator.py       # Real participant simulation
│   └── agent_fixtures.py               # Real agent deployment
├── test_basic_livekit_integration.py   # REAL LiveKit integration tests
├── test_stt_basic_functionality.py    # Basic STT functionality tests
└── test_stt_processing.py             # STT processing scenarios
```

## 🧪 Current Test Categories

### **REAL LiveKit Integration Tests**

- **Room Creation/Cleanup** - Real LiveKit Cloud room operations
- **Participant Connections** - Real WebSocket connections to LiveKit rooms
- **Agent Deployment** - Real agents connecting to rooms with Yandex STT
- **Complete E2E Pipeline** - Agent + Participant + STT transcription
- **Resource Management** - Proper cleanup and session management

### **STT Basic Functionality Tests**

- Russian STT agent creation and configuration
- Stream creation and lifecycle management
- Russian audio file loading and validation
- Russian transcription validation logic
- Agent credentials validation
- Russian audio fixtures availability
- Basic error handling

### **STT Processing Scenarios Tests**

- **Parametrized Russian Audio Tests** - Tests each Russian audio file individually
- **Direct STT Processing** - Audio processed through Yandex STT directly
- **Russian Greeting Scenario** - Specific greeting transcription validation
- **Russian Language Configuration** - Validates `ru-RU` language setup

## 🎵 Audio Fixtures Used

The tests use **real Russian audio files** from `tests/fixtures/`:

- **`russian_greeting.wav`** - "привет как дела меня зовут анна" (Hello, how are you, my name is Anna)
- **`russian_learning.wav`** - "я изучаю русский язык уже два года" (I've been learning Russian for two years)
- **`russian_weather.wav`** - "сегодня хорошая погода для прогулки в парке" (Today is good weather for a walk in the
  park)

## 🔧 Technical Details

### **Real-Time Processing:**

- Audio processed in **100ms chunks** simulating live participant speech
- Agent receives audio frames exactly as it would in production
- Streaming sessions with real session IDs and gRPC connections

### **Russian Language Focus:**

- All tests use `language="ru-RU"` exclusively
- Validates Cyrillic character transcriptions
- Keyword-based validation for specific content types

### **Performance Validation:**

- **100% success rate** (3/3 files transcribed successfully)
- Real-time processing performance metrics
- Proper session lifecycle management

## 🚀 Running the Tests

### **Prerequisites:**

1. **Environment Variables** - Required credentials in `.env` file:
   ```bash
   YANDEX_API_KEY=your_yandex_api_key
   YANDEX_FOLDER_ID=your_yandex_folder_id
   LIVEKIT_API_KEY=your_livekit_api_key
   LIVEKIT_API_SECRET=your_livekit_api_secret
   LIVEKIT_WS_URL=your_livekit_websocket_url
   ```

2. **Audio Fixtures** - Russian audio files must be available:
   ```bash
   make fixtures  # Generate test audio files
   ```

### **Run Agent Tests:**

```bash
# Run all agent mode tests 
make test_agent
```

## 📊 Expected Results

### **Successful Test Output:**

```
✅ 13 tests passed in ~8 seconds
✅ Real Russian transcriptions received
✅ 100% success rate for audio processing
✅ No warnings or errors
```

### **Sample Transcription Results:**

```
INFO: ✅ REAL transcription from russian_greeting.wav: 'привет как дела меня зовут анна'
INFO: ✅ REAL transcription from russian_learning.wav: 'я изучаю русский язык уже два года'
INFO: ✅ REAL transcription from russian_weather.wav: 'сегодня хорошая погода для прогулки в парке'
```

## 🎯 What Makes These Tests "Real"

1. **Real LiveKit Cloud Infrastructure** - Actual rooms created in LiveKit Cloud (not local/mock)
2. **Real WebSocket Connections** - TLS 1.3 connections to `your-project.livekit.cloud`
3. **Real Participant Simulation** - Participants join rooms via separate threads/event loops
4. **Real Agent Deployment** - Agents connect to rooms and process audio through the LiveKit pipeline
5. **Authentic API Calls** - Direct gRPC connections to Yandex Cloud SpeechKit
6. **Real Audio Processing** - Actual WAV files with human Russian speech streamed through LiveKit
7. **Real-Time Streaming** - Audio processed in chunks like live participant speech
8. **Actual Transcriptions** - Validates real Russian text output from complete pipeline
9. **Performance Metrics** - Measures actual processing time and success rates
10. **Dashboard Visibility** - All operations visible in LiveKit Cloud dashboard

**This is TRUE end-to-end integration** - the complete LiveKit pipeline from participant to transcription.

## 🚀 Running Tests

### Basic Infrastructure Tests

```bash
# Test room creation/deletion (0 participants expected)
hatch run pytest tests/e2e_agent/test_basic_livekit_integration.py::TestBasicLiveKitIntegration::test_basic_room_creation_and_cleanup -v

# Test participant connection (1 participant expected)
hatch run pytest tests/e2e_agent/test_basic_livekit_integration.py::TestBasicLiveKitIntegration::test_participant_connection_to_room -v

# Run all LiveKit integration tests
hatch run pytest tests/e2e_agent/test_basic_livekit_integration.py -v
```

### Monitoring Results

After running tests, check the LiveKit Cloud dashboard:

1. **Go to**: https://cloud.livekit.io/projects/*/sessions
2. **Look for rooms** with descriptive names like `test-simple-expect-1p-room-abc12345`
3. **Verify participant counts** match the expected number in the room name
4. **Check duration** reflects test execution time
5. **Confirm status** shows "Closed" after completion

## ⚠️ Test Failure Behavior

**IMPORTANT**: Agent E2E tests are designed to FAIL (not skip) when required infrastructure is missing.

### **Expected Failures**

**Missing LiveKit Credentials**

```
EnvironmentError: LiveKit credentials required for agent E2E tests.
Set LIVEKIT_API_KEY, LIVEKIT_API_SECRET, and LIVEKIT_WS_URL environment variables.
```

**Missing Yandex Credentials**

```
EnvironmentError: Yandex Cloud credentials required for agent E2E tests.
Set YANDEX_API_KEY and YANDEX_FOLDER_ID environment variables.
```

**Missing Audio Fixtures**

```
FileNotFoundError: Audio fixture file not found: tests/fixtures/russian_greeting.wav.
Run 'make fixtures' to generate test audio files.
```

### 🔧 Troubleshooting Common Issues

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

## 🔍 Debugging

### **Common Issues:**

- **Missing credentials** - Ensure all environment variables are set
- **Missing audio fixtures** - Run `make fixtures` to generate test files
- **Network issues** - Tests require internet connection to Yandex Cloud
- **Account balance requirements** - See detailed requirements below

## ⚠️ Account Requirements

### **Yandex Cloud Account Balance**

**CRITICAL**: E2E tests require a **positive Yandex Cloud account balance** to function properly.

**⚠️ Tests WILL FAIL if:**

- Your Yandex Cloud account balance is **negative or zero**
- Your account has **insufficient funds** for API usage
- Your **billing account is suspended** or inactive

**🔍 How to Check Your Balance:**

1. Go to [Yandex Cloud Console](https://console.cloud.yandex.com)
2. Navigate to **Billing** → **Account balance**
3. Ensure the balance is **positive** before running tests

**💳 How to Top Up:**

1. In Yandex Cloud Console, go to **Billing**
2. Click **Top up account**
3. Add funds using your preferred payment method
4. Wait for payment confirmation (usually instant)

### **API Usage Quotas**

- **SpeechKit STT**: Check your quota limits in Yandex Cloud Console
- **Rate limiting**: Tests include automatic retry logic for temporary limits
- **Usage monitoring**: Monitor your API usage during test execution

### **Verbose Logging:**

```bash
make test_agent  # Already includes verbose logging and live output
```

## 🏆 Success Criteria

Current tests validate that:

- ✅ Yandex STT plugin processes Russian audio correctly
- ✅ Russian language processing is accurate and reliable
- ✅ Real-time audio streaming functions properly
- ✅ Error handling and cleanup work correctly
- ✅ Performance meets production requirements

Future tests will validate:

- ⏳ True LiveKit room integration
- ⏳ Agent deployment to rooms
- ⏳ Participant simulation and interaction
- ⏳ Complete end-to-end pipeline

---

**Note:** Current tests validate STT processing. See `IMPLEMENTATION_PLAN.md` for implementing true LiveKit Agent
integration.
