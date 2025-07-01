# Utilities for Yandex SpeechKit STT Plugin

This directory contains utility scripts for the Yandex SpeechKit STT plugin development and testing.

## Scripts

### `fixture_generator.py` - Unified Audio Fixture Generator

A comprehensive script that can generate both basic audio fixtures and real speech fixtures for testing.

**Features:**

- Generate basic audio fixtures (tones, noise, silence) using FFmpeg
- Generate real speech fixtures using the system TTS (Windows)
- Cross-platform support (Windows, macOS, Linux)
- Proper file naming with descriptive content
- Validation and reporting

**Usage:**

```bash
# Generate all fixtures (basic + speech)
python utils/fixture_generator.py --type all

# Generate only speech fixtures
python utils/fixture_generator.py --type speech

# Generate only basic fixtures
python utils/fixture_generator.py --type basic

# List available TTS voices
python utils/fixture_generator.py --list-voices

# Generate to custom directory
python utils/fixture_generator.py --output-dir custom/path
```

**Requirements:**

- FFmpeg (for basic fixtures)
- pywin32 (for Windows TTS - already in dev dependencies)
- Platform TTS: Windows SAPI, macOS say, Linux espeak

## Generated Audio Files

The fixture generator creates the following audio files in `tests/fixtures/`:

### Russian Audio Samples

- `russian_greeting.wav` - Russian greeting: "Привет, как дела? Меня зовут Анна."
- `russian_weather.wav` - Russian weather talk: "Сегодня хорошая погода для прогулки в парке."
- `russian_learning.wav` - Russian learning phrase: "Я изучаю русский язык уже два года."

### English Audio Samples

- `english_greeting.wav` - English greeting: "Hello, how are you? My name is John."
- `english_weather.wav` - English weather talk: "Today is a beautiful day for a walk in the park."
- `english_learning.wav` - English learning phrase: "I have been learning English for two years."

### Special Test Files

- `mixed_languages.wav` - Mixed Russian and English speech
- `silence.wav` - Silent audio for testing edge cases

## Audio Format Specifications

All test audio files should meet these specifications:

- **Format**: WAV (uncompressed PCM)
- **Sample Rate**: 16kHz (16000 Hz)
- **Channels**: Mono (1 channel)
- **Bit Depth**: 16-bit
- **Duration**: 5–30 seconds for short samples, 1–5 minutes for long samples

## Creating Test Audio Files

You can create test audio files using:

### Using FFmpeg

```bash
# Convert any audio file to the required format
ffmpeg -i input.mp3 -ar 16000 -ac 1 -sample_fmt s16 output.wav

# Create a silent audio file (5 seconds)
ffmpeg -f lavfi -i anullsrc=channel_layout=mono:sample_rate=16000 -t 5 silence.wav
```

### Using Python (for programmatic generation)

```python
import numpy as np
import wave


def create_test_tone(filename, duration=5, frequency=440, sample_rate=16000):
    """Create a test tone audio file."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave_data = np.sin(frequency * 2 * np.pi * t)

    # Convert to 16-bit integers
    wave_data = (wave_data * 32767).astype(np.int16)

    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(wave_data.tobytes())


# Create a test tone
create_test_tone('test_tone.wav')
```

## Sample Content Suggestions

### Russian Text Samples

- "Привет, как дела? Меня зовут Анна".
- "Сегодня хорошая погода для прогулки в парке".
- "Я изучаю русский язык уже два года".

### English Text Samples

- "Hello, how are you? My name is John."
- "Today is a beautiful day for a walk in the park."
- "I have been learning English for two years."

## Usage in Tests

The test suite uses these audio files in `tests/test_stt.py`:

```python
import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.mark.asyncio
async def test_russian_recognition():
    audio_file = FIXTURES_DIR / "russian_sample.wav"
    if audio_file.exists():
        # Test with a real audio file
        pass
    else:
        pytest.skip("Russian audio fixture not available")
```

## Note on File Sizes

Audio files are stored using Git LFS (see `.gitattributes`) due to their size.
Contributors should create or obtain their own test audio files following the specifications above.

## Legal Considerations

- Only use audio files you have the right to use
- Avoid copyrighted material
- Consider using Creative Commons licensed audio
- Record your own voice samples for testing
