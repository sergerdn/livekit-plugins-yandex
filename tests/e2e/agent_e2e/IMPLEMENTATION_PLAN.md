# Implementation Plan: True End-to-End LiveKit Agent Tests

## 🎯 Objective

**IMPLEMENT REAL FEATURES** to make the existing documentation claims TRUE.
Transform `tests/e2e_agent/` from **direct STT processing tests** to **true end-to-end LiveKit agent tests** that
actually implement the complete LiveKit room scenarios with real participants, agents, and room infrastructure that the
README.md already claims to have.

## 🎯 Core Philosophy: Make Documentation Claims REAL

The README.md already promises:

- ✅ "Real LiveKit Room Simulation"
- ✅ "Real Participant Speech"
- ✅ "Real Agent Processing"
- ✅ "Real Russian Transcriptions"

**Our goal: IMPLEMENT these features so the claims become TRUE, not remove the claims.**

## 📋 Current State Analysis

### ❌ What's Missing (Critical Gaps)

- **No LiveKit room connections** - Tests bypass LiveKit entirely
- **No real participants** - Audio files loaded directly, not published as tracks
- **No real agents** - STT instances created directly, not deployed as LiveKit agents
- **No WebSocket infrastructure** - No actual LiveKit room/participant/agent communication
- **Documentation promises not implemented** - README claims "real LiveKit room simulation" but we need to build it

### ✅ What's Working (Keep These)

- **Excellent Russian audio fixtures** - High-quality test files with expected transcriptions
- **Robust STT validation** - Comprehensive transcription accuracy testing
- **Good test infrastructure** - Fixtures, validation functions, parameterized tests
- **Proper credentials management** - Environment variable handling

## 🏗️ Implementation Strategy

### Phase 1: Infrastructure Setup

1. **Preserve existing STT tests** - Rename current tests to reflect their actual scope
2. **Create true agent test framework** - Build LiveKit room/participant/agent infrastructure
3. **Implement agent deployment patterns** - Use LiveKit agents framework properly

### Phase 2: Core Agent Implementation

1. **Real LiveKit room creation** - WebSocket connections to LiveKit Cloud
2. **Real participant simulation** - Publish audio tracks as live participants would
3. **Real agent deployment** - Deploy actual LiveKit agents that join rooms
4. **End-to-end audio pipeline** - Participant → Room → Agent → STT → Transcription

### Phase 3: Test Scenarios

1. **Single participant scenarios** - Agent processes one participant's Russian speech
2. **Multi-participant scenarios** - Agent handles multiple speakers simultaneously
3. **Language switching scenarios** - Agent adapts to different languages
4. **Error recovery scenarios** - Agent handles network issues, API failures

## 🏗️ **Test Infrastructure Implementation Strategy**

### **Keep Plugin Library Untouched**

- The `livekit.plugins.yandex` library works perfectly as-is
- No changes needed to the actual STT implementation
- All infrastructure goes in the test directory

### **Build Test Framework in `tests/e2e_agent/`**

- Create infrastructure as test utilities - Not part of the main plugin
- Use existing plugin library - Import and use `livekit.plugins.yandex.STT` as-is
- Build test framework - That creates real LiveKit scenarios around the plugin
- Keep separation clean - Test infrastructure stays in tests/, plugin stays pure

## 📁 New File Structure

```
tests/e2e_agent/
├── IMPLEMENTATION_PLAN.md              # This file
├── __init__.py                         # Package initialization
├── conftest.py                         # Enhanced fixtures for real agent testing
├──
├── # RENAMED EXISTING TESTS (preserve current functionality) ✅ COMPLETED
├── test_stt_processing.py              # ✅ Renamed from test_russian_agent_scenarios.py
├── test_stt_basic_functionality.py     # ✅ Renamed from test_basic_agent_functionality.py
├──
├── # NEW TRUE E2E AGENT TESTS
├── test_basic_livekit_integration.py   # VERY basic: agent + participant + transcription
├──
├── # TEST INFRASTRUCTURE (separate from plugin library)
├── infrastructure/                     # New directory for test infrastructure
│   ├── __init__.py                     # Infrastructure package
│   ├── room_manager.py                 # LiveKit room operations
│   ├── participant_simulator.py        # Participant simulation utilities
│   └── agent_fixtures.py               # Agent deployment helpers
└── validation_helpers.py               # Enhanced validation functions
```

## 🔧 Technical Implementation Details

### 1. Real LiveKit Room Infrastructure

- **room_manager.py** - Create actual LiveKit rooms with WebSocket connections
- Generate access tokens for different participants (agents, test participants)
- Manage room lifecycle and cleanup

### 2. Real Participant Simulation

- **participant_simulator.py** - Simulate real participants joining rooms
- Publish audio tracks from test fixture files
- Stream audio data as if participants were speaking live

### 3. Real Agent Implementation

- **agent_fixtures.py** - Deploy actual LiveKit agents to rooms
- Integrate with existing `livekit.plugins.yandex.STT` plugin
- Process participant audio through complete LiveKit pipeline

## 🧪 Test Scenarios Implementation

### VERY Basic LiveKit Integration Test

- Create real LiveKit room
- Deploy agent to room
- Simulate ONE participant joining and speaking `russian_greeting.wav`
- Validate agent receives and transcribes "привет" correctly
- **That's it!** Proves the complete pipeline works.

## 📚 Implementation References

### LiveKit Agent Testing Patterns

Based on LiveKit's official examples and documentation:

**Agent Development Pattern:**

```python
# From: https://docs.livekit.io/agents/start/voice-ai/
from livekit.agents import JobContext, WorkerOptions
from livekit.plugins.yandex import STT


async def entrypoint(ctx: JobContext):
    stt = STT(api_key="...", folder_id="...", language="ru-RU")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    # Process participant audio through STT
```

**Participant Simulation Pattern:**

```python
# Based on: https://docs.livekit.io/home/self-hosting/benchmark/
# LiveKit CLI load testing approach adapted for our tests
from livekit import rtc

room = rtc.Room()
await room.connect(ws_url, token)
# Publish audio track with test fixture data
```

**Testing Infrastructure Examples:**

- LiveKit CLI load testing: `lk load-test --audio-publishers 1 --subscribers 1`
- Agent console mode: `python agent.py console`
- Agent dev mode: `python agent.py dev`

## 🔄 Migration Strategy

### Step 1: Preserve Existing Functionality ✅ COMPLETED

- ✅ Renamed `test_russian_agent_scenarios.py` → `test_stt_processing.py`
- ✅ Renamed `test_basic_agent_functionality.py` → `test_stt_basic_functionality.py`

### Step 2: Implement Real LiveKit Room Simulation

- **IMPLEMENT** the real LiveKit room simulation that README.md claims to have
- Make the documentation claims TRUE by building the actual functionality
- Ensure tests actually create real LiveKit rooms, participants, and agents as documented

### Step 3: Implement Test Infrastructure (REQUIRED BEFORE TESTS)

**These are the foundation components needed to enable real LiveKit room scenarios:**

**Create `tests/e2e_agent/infrastructure/` directory with:**

- **room_manager.py** - LiveKit room creation, connection management, token generation
- **participant_simulator.py** - Real participant simulation, audio track publishing, room joining
- **agent_fixtures.py** - Real LiveKit agent deployment, STT integration, room joining

**Implementation Principles:**

- ✅ Keep plugin library (`livekit.plugins.yandex`) completely untouched
- ✅ Build test infrastructure as separate utilities in `tests/` directory
- ✅ Use existing plugin via imports: `from livekit.plugins.yandex import STT`
- ✅ Test infrastructure creates real LiveKit scenarios around the plugin

**LiveKit Infrastructure:**

**LiveKit Cloud** (Required for testing):

- Free account: https://cloud.livekit.io/
- Get API keys from the project dashboard
- No local setup required

**Reference Documentation:**

- LiveKit Agent Development: https://docs.livekit.io/agents/start/voice-ai/
- LiveKit Cloud Setup: https://cloud.livekit.io/
- Load Testing Examples: https://docs.livekit.io/home/self-hosting/benchmark/
- CLI Tools: https://github.com/livekit/livekit-cli

**Without these infrastructure components, we cannot create any real e2e tests. They must be implemented first.**

### Step 4: Implement VERY Basic Test

- Create `test_basic_livekit_integration.py` with ONE simple test
- Test: agent + participant + transcription in real LiveKit room
- **Keep it simple!** Prove the pipeline works end-to-end

### Step 5: Integration

- Update Makefile targets
- Update documentation

## 📊 Success Criteria

### ✅ Technical Validation

- [ ] Tests create real LiveKit WebSocket connections
- [ ] Tests deploy actual LiveKit agents that join rooms
- [ ] Tests simulate real participants publishing audio tracks
- [ ] Audio flows through complete LiveKit pipeline: Participant → Room → Agent → STT
- [ ] Tests validate end-to-end transcription accuracy
- [ ] Tests handle multiple participants simultaneously
- [ ] Tests recover from network/API failures

### ✅ Quality Assurance

- [ ] All existing STT processing functionality preserved
- [ ] Russian language testing maintains 100% coverage
- [ ] Test execution time remains reasonable (<2 minutes per test)
- [ ] Tests are reliable and don't have flaky failures
- [ ] Documentation claims are implemented and accurate

### ✅ User Experience

- [ ] Tests implement the REAL features that documentation promises
- [ ] Easy to run tests with `make test_agent`
- [ ] Clear error messages when credentials/fixtures missing
- [ ] Comprehensive logging for debugging issues

## 🚀 Implementation Timeline

### Week 1: Infrastructure

- [x] Rename existing tests ✅ COMPLETED
- [ ] Create room_manager.py
- [ ] Create participant_simulator.py
- [ ] Create agent_fixtures.py

### Week 2: Basic Test

- [ ] Implement ONE very basic test: `test_basic_livekit_integration.py`
- [ ] Update conftest.py with infrastructure fixtures
- [ ] Test: room + agent + participant + transcription

### Week 4: Integration & Documentation

- [ ] Update README.md
- [ ] Update Makefile
- [ ] Final testing and validation
- [ ] Documentation review

## 🔍 Risk Mitigation

### Risk: Breaking Existing Functionality

**Mitigation**: Rename existing tests instead of modifying them, ensuring all current STT validation continues to work.

### Risk: Complex LiveKit Infrastructure

**Mitigation**: Start with simple scenarios and build complexity gradually. Use existing agent examples as reference.

### Risk: Test Reliability

**Mitigation**: Implement proper cleanup, timeout handling, and retry logic. Use unique room names to avoid conflicts.

### Risk: Performance Issues

**Mitigation**: Implement parallel test execution where possible, optimize fixture creation, and add performance
monitoring.

---

This plan **IMPLEMENTS REAL FEATURES** to make the documentation claims TRUE - transforming the current direct STT
processing tests into the actual true end-to-end LiveKit agent tests that the README.md promises, while preserving all
existing functionality and maintaining the excellent Russian language testing coverage.
