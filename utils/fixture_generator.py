#!/usr/bin/env python3
"""
Unified fixture generator for Yandex SpeechKit STT plugin tests.

This script generates both basic audio fixtures (tones, noise, silence) 
and real speech fixtures using the system TTS from Windows.

Requirements:
- FFmpeg (for basic fixtures)
- pywin32 (for Windows TTS)
- Platform-specific TTS (Windows SAPI, macOS say, Linux espeak)

Usage:
    python fixture_generator.py --type basic # Generate basic fixtures
    python fixture_generator.py --type speech # Generate speech fixtures
    python fixture_generator.py --type all # Generate both types
    python fixture_generator.py --list-voices # List available TTS voices
"""

import argparse
import platform
import subprocess
import sys
from pathlib import Path

# Speech content for fixtures
SPEECH_CONTENT = {
    "russian": {
        "greeting": "Привет, как дела? Меня зовут Анна.",
        "weather": "Сегодня хорошая погода для прогулки в парке.",
        "learning": "Я изучаю русский язык уже два года.",
    },
    "english": {
        "greeting": "Hello, how are you? My name is John.",
        "weather": "Today is a beautiful day for a walk in the park.",
        "learning": "I have been learning English for two years.",
    },
    "mixed": "Hello, меня зовут Анна. I work in технологической компании. This is English, а это русский язык in the same sentence."
}


class FixtureGenerator:
    """Unified fixture generator for audio test files."""

    def __init__(self, fixtures_dir: Path = None):
        """Initialize the fixture generator."""
        self.fixtures_dir = fixtures_dir or Path("tests/fixtures")
        self.fixtures_dir.mkdir(exist_ok=True)
        self.success_count = 0
        self.total_count = 0

    # noinspection PyMethodMayBeStatic
    def check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"FFmpeg found: {result.stdout.split()[2]}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Error: FFmpeg not found. Please install FFmpeg:")
            print("  Windows: choco install ffmpeg")
            print("  macOS: brew install ffmpeg")
            print("  Ubuntu: apt-get install ffmpeg")
            return False

    # noinspection PyMethodMayBeStatic
    def check_tts_support(self) -> bool:
        """Check if TTS is supported on the current platform."""
        system = platform.system()

        if system == "Windows":
            try:
                import win32com.client
                return True
            except ImportError:
                print("Windows TTS requires pywin32. Install with: pip install pywin32")
                return False
        elif system == "Darwin":  # macOS
            try:
                subprocess.run(["say", "--version"], capture_output=True, check=True)
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("macOS TTS (say command) not available")
                return False
        elif system == "Linux":
            try:
                subprocess.run(["espeak", "--version"], capture_output=True, check=True)
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("Linux TTS requires espeak. Install with: sudo apt-get install espeak")
                return False
        else:
            print(f"TTS not supported on {system}")
            return False

    def generate_basic_fixture(self, filename: str, audio_type: str, **kwargs) -> bool:
        """Generate a basic audio fixture using FFmpeg."""
        output_path = self.fixtures_dir / filename

        if audio_type == "silence":
            duration = kwargs.get("duration", 5)
            cmd = [
                "ffmpeg", "-y", "-f", "lavfi",
                "-i", f"anullsrc=r=16000:cl=mono",
                "-t", str(duration), "-c:a", "pcm_s16le", str(output_path)
            ]
        elif audio_type == "tone":
            frequency = kwargs.get("frequency", 440)
            duration = kwargs.get("duration", 5)
            cmd = [
                "ffmpeg", "-y", "-f", "lavfi",
                "-i", f"sine=frequency={frequency}:sample_rate=16000:duration={duration}",
                "-c:a", "pcm_s16le", str(output_path)
            ]
        elif audio_type == "noise":
            duration = kwargs.get("duration", 5)
            cmd = [
                "ffmpeg", "-y", "-f", "lavfi",
                "-i", f"anoisesrc=d={duration}:c=pink:r=16000:a=0.1",
                "-c:a", "pcm_s16le", str(output_path)
            ]
        else:
            print(f"  Unknown audio type: {audio_type}")
            return False

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"  Created: {filename}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"  Failed to create {filename}: {e}")
            return False

    def generate_speech_fixture(self, filename: str, text: str, language: str = "en") -> bool:
        """Generate a speech fixture using the system TTS."""
        output_path = self.fixtures_dir / filename
        system = platform.system()

        try:
            if system == "Windows":
                return self._generate_windows_tts(text, output_path, language)
            elif system == "Darwin":
                return self._generate_macos_tts(text, output_path, language)
            elif system == "Linux":
                return self._generate_linux_tts(text, output_path)
            else:
                print(f"  TTS not supported on {system}")
                return False
        except Exception as e:
            print(f"  Failed to create {filename}: {e}")
            return False

    def _generate_windows_tts(self, text: str, output_path: Path, language: str) -> bool:
        """Generate TTS on Windows using SAPI."""
        import win32com.client

        voice = win32com.client.Dispatch("SAPI.SpVoice")

        # Try to find appropriate voice
        if language == "ru":
            voices = voice.GetVoices()
            for i in range(voices.Count):
                voice_info = voices.Item(i)
                if "russian" in voice_info.GetDescription().lower():
                    voice.Voice = voice_info
                    break

        file_stream = win32com.client.Dispatch("SAPI.SpFileStream")
        file_stream.Open(str(output_path), 3)
        voice.AudioOutputStream = file_stream
        voice.Speak(text)
        file_stream.Close()

        print(f"  Created: {output_path.name}")
        return True

    def _generate_macos_tts(self, text: str, output_path: Path, language: str) -> bool:
        """Generate TTS on macOS using say command."""
        voice = "Yuri" if language == "ru" else "Alex"
        temp_path = output_path.with_suffix('.aiff')

        cmd = ["say", "-v", voice, "-o", str(temp_path), text]
        subprocess.run(cmd, check=True, capture_output=True)

        # Convert to WAV
        convert_cmd = [
            "ffmpeg", "-y", "-i", str(temp_path),
            "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", str(output_path)
        ]
        subprocess.run(convert_cmd, check=True, capture_output=True)
        temp_path.unlink()

        print(f"  Created: {output_path.name}")
        return True

    def _generate_linux_tts(self, text: str, output_path: Path) -> bool:
        """Generate TTS on Linux using espeak."""
        cmd = ["espeak", "-w", str(output_path), "-s", "150", "-a", "100", text]
        subprocess.run(cmd, check=True, capture_output=True)

        print(f"  Created: {output_path.name}")
        return True

    def generate_basic_fixtures(self) -> bool:
        """Generate all basic fixtures."""
        print("Generating basic audio fixtures...")
        print()

        fixtures = [
            ("silence.wav", "silence", {"duration": 5}),
            ("test_tone_low.wav", "tone", {"frequency": 300, "duration": 8}),
            ("test_tone_mid.wav", "tone", {"frequency": 440, "duration": 8}),
            ("test_tone_high.wav", "tone", {"frequency": 800, "duration": 8}),
            ("test_noise.wav", "noise", {"duration": 10}),
        ]

        for filename, audio_type, kwargs in fixtures:
            if self.generate_basic_fixture(filename, audio_type, **kwargs):
                self.success_count += 1
            self.total_count += 1

        return self.success_count > 0

    def generate_speech_fixtures(self) -> bool:
        """Generate all speech fixtures."""
        print("Generating speech fixtures...")
        print()

        # Russian fixtures
        print("Russian speech samples:")
        for key, text in SPEECH_CONTENT["russian"].items():
            filename = f"russian_{key}.wav"
            if self.generate_speech_fixture(filename, text, "ru"):
                self.success_count += 1
            self.total_count += 1

        print()

        # English fixtures  
        print("English speech samples:")
        for key, text in SPEECH_CONTENT["english"].items():
            filename = f"english_{key}.wav"
            if self.generate_speech_fixture(filename, text, "en"):
                self.success_count += 1
            self.total_count += 1

        print()

        # Mixed language fixture
        print("Mixed language sample:")
        if self.generate_speech_fixture("mixed_languages.wav", SPEECH_CONTENT["mixed"], "en"):
            self.success_count += 1
        self.total_count += 1

        # Silence fixture
        print()
        print("Silence fixture:")
        if self.generate_basic_fixture("silence.wav", "silence", duration=5):
            self.success_count += 1
        self.total_count += 1

        return self.success_count > 0

    def list_voices(self):
        """List available TTS voices."""
        system = platform.system()
        print(f"Available TTS voices on {system}:")
        print()

        if system == "Windows":
            try:
                import win32com.client
                voice = win32com.client.Dispatch("SAPI.SpVoice")
                voices = voice.GetVoices()
                for i in range(voices.Count):
                    voice_info = voices.Item(i)
                    print(f"  {i}: {voice_info.GetDescription()}")
            except Exception as e:
                print(f"  Error listing voices: {e}")

        elif system == "Darwin":
            try:
                result = subprocess.run(["say", "-v", "?"], capture_output=True, text=True)
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        print(f"  {line}")
            except Exception as e:
                print(f"  Error listing voices: {e}")

        elif system == "Linux":
            try:
                result = subprocess.run(["espeak", "--voices"], capture_output=True, text=True)
                for line in result.stdout.strip().split('\n')[1:]:
                    if line.strip():
                        print(f"  {line}")
            except Exception as e:
                print(f"  Error listing voices: {e}")

    def validate_fixtures(self) -> bool:
        """Validate created fixtures."""
        audio_files = list(self.fixtures_dir.glob("*.wav"))

        if not audio_files:
            print("No audio fixtures found.")
            return False

        print(f"Found {len(audio_files)} audio fixtures:")
        total_size = 0

        for audio_file in sorted(audio_files):
            size = audio_file.stat().st_size
            total_size += size
            size_kb = round(size / 1024, 1)
            print(f"  {audio_file.name}: {size_kb} KB")

        total_mb = round(total_size / 1024 / 1024, 1)
        print(f"Total size: {total_mb} MB")

        if total_size > 50 * 1024 * 1024:
            print("Warning: Total fixture size is large (>50MB)")

        return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate audio fixtures for testing")
    parser.add_argument("--type", choices=["basic", "speech", "all"], default="all",
                        help="Type of fixtures to generate")
    parser.add_argument("--list-voices", action="store_true",
                        help="List available TTS voices")
    parser.add_argument("--output-dir", type=Path, default=Path("tests/fixtures"),
                        help="Output directory for fixtures")

    args = parser.parse_args()

    print("Yandex SpeechKit STT Plugin - Unified Fixture Generator")
    print("=" * 60)
    print()

    generator = FixtureGenerator(args.output_dir)

    if args.list_voices:
        generator.list_voices()
        return

    try:
        if args.type in ["basic", "all"]:
            if not generator.check_ffmpeg():
                print("FFmpeg required for basic fixtures")
                if args.type == "basic":
                    sys.exit(1)
            else:
                generator.generate_basic_fixtures()
                print()

        if args.type in ["speech", "all"]:
            if not generator.check_tts_support():
                print("TTS not available for speech fixtures")
                if args.type == "speech":
                    sys.exit(1)
            else:
                generator.generate_speech_fixtures()
                print()

        print(f"Fixture generation complete: {generator.success_count}/{generator.total_count} successful")
        print()
        generator.validate_fixtures()

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
