#!/usr/bin/env python3
"""
Real-time streaming demonstration for Yandex SpeechKit STT plugin.

This script demonstrates proper real-time streaming audio processing patterns
with the Yandex SpeechKit STT plugin, showing the difference between:
- Real-time streaming (recommended)
- Emulated streaming from files (for testing)
- Batch processing (discouraged for real-time applications)

Prerequisites:
1. Set up the .env file with your Yandex Cloud credentials:
   YANDEX_API_KEY=your_api_key_here
   YANDEX_FOLDER_ID=your_folder_id_here
2. Generate audio fixtures: make fixtures
3. Run this example: python example_plugin_usage.py
"""

import asyncio
import logging
import os
import sys
import time
import wave
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

from livekit.plugins.yandex import STT
from livekit.plugins.yandex._utils import YandexCredentials
from livekit.agents import stt
from livekit import rtc
import numpy as np


def resample_audio_simple(audio_data: np.ndarray, original_rate: int, target_rate: int) -> np.ndarray:
    """Simple audio resampling using linear interpolation."""
    if original_rate == target_rate:
        return audio_data

    # Calculate the resampling ratio
    ratio = target_rate / original_rate

    # Calculate the new length
    new_length = int(len(audio_data) * ratio)

    # Create indices for interpolation
    original_indices = np.arange(len(audio_data))
    new_indices = np.linspace(0, len(audio_data) - 1, new_length)

    # Perform linear interpolation
    resampled = np.interp(new_indices, original_indices, audio_data)

    # Convert back to int16
    return resampled.astype(np.int16)

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def check_environment():
    """Check if required environment variables are set."""
    logger.info("Checking environment variables...")

    api_key = os.environ.get("YANDEX_API_KEY")
    folder_id = os.environ.get("YANDEX_FOLDER_ID")

    if not api_key:
        logger.error("YANDEX_API_KEY not found in environment")
        logger.error("Please add it to your .env file")
        return False

    if not folder_id:
        logger.error("YANDEX_FOLDER_ID not found in environment")
        logger.error("Please add it to your .env file")
        return False

    logger.info(f"API Key: {api_key[:15]}...")
    logger.info(f"Folder ID: {folder_id}")
    logger.info("Environment validation successful")
    return True


def find_audio_fixtures():
    """Find available audio fixture files."""
    print("Looking for audio fixtures...")

    fixtures_dir = Path("tests/fixtures")
    if not fixtures_dir.exists():
        print("ERROR: tests/fixtures/ directory not found")
        print("Run 'make fixtures' to generate test audio files")
        return []

    audio_files = list(fixtures_dir.glob("*.wav"))
    if not audio_files:
        print("ERROR: No audio files found in tests/fixtures/")
        print("Run 'make fixtures' to generate test audio files")
        return []

    print(f"Found {len(audio_files)} audio files:")
    for audio_file in sorted(audio_files):
        size_kb = round(audio_file.stat().st_size / 1024, 1)
        print(f"{audio_file.name}: {size_kb} KB")

    return audio_files


async def stream_audio_file_realtime(stt_instance: STT, audio_file: Path):
    """
    Demonstrate REAL-TIME STREAMING by processing audio file in chunks.

    This is the RECOMMENDED approach for real-time applications.
    Audio is processed frame-by-frame as it would arrive in a live scenario.
    """
    logger.info(f"=== REAL-TIME STREAMING: {audio_file.name} ===")

    try:
        # Open a WAV file to read audio properties
        with wave.open(str(audio_file), 'rb') as wav_file:
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            total_frames = wav_file.getnframes()

            logger.info(f"Audio properties:")
            logger.info(f"Sample rate: {sample_rate} Hz")
            logger.info(f"Channels: {channels}")
            logger.info(f"Total frames: {total_frames}")
            logger.info(f"Duration: {total_frames / sample_rate:.2f}s")

            # Calculate chunk size for 20 ms frames (typical for real-time)
            chunk_duration_ms = 20  # 20ms chunks
            chunk_size = int(sample_rate * chunk_duration_ms / 1000)

            logger.info(f"Streaming in {chunk_duration_ms}ms chunks ({chunk_size} samples each at {sample_rate}Hz)")

            # Always use 16000 Hz for the plugin (standard for speech recognition)
            target_sample_rate = 16000
            if sample_rate != target_sample_rate:
                logger.info(f"Audio sample rate is {sample_rate}Hz, will convert to {target_sample_rate}Hz for plugin")

            # Create streaming session with standard 16000 Hz
            stream = stt_instance.stream()
            logger.info("Streaming session created")

            # Track results
            interim_count = 0
            final_count = 0
            start_time = time.time()

            async def stream_audio_chunks():
                """Stream audio data in real-time chunks."""
                nonlocal interim_count, final_count

                chunk_number = 0
                while True:
                    # Read audio chunk
                    frames = wav_file.readframes(chunk_size)
                    if not frames:
                        logger.info("Reached end of audio file")
                        break

                    chunk_number += 1

                    # Convert to a numpy array for AudioFrame
                    audio_array = np.frombuffer(frames, dtype=np.int16)

                    # Resample audio if necessary to match plugin expectations
                    if sample_rate != target_sample_rate:
                        audio_array = resample_audio_simple(audio_array, sample_rate, target_sample_rate)
                        # Recalculate samples per channel after resampling
                        samples_per_channel = len(audio_array) // channels
                        frame_sample_rate = target_sample_rate
                    else:
                        samples_per_channel = len(audio_array) // channels
                        frame_sample_rate = sample_rate

                    # Create LiveKit AudioFrame with converted audio
                    # Always use target_sample_rate (16000) for the plugin
                    frame = rtc.AudioFrame(
                        data=audio_array,
                        sample_rate=target_sample_rate,  # Always 16000 Hz for the plugin
                        num_channels=channels,
                        samples_per_channel=samples_per_channel,
                    )

                    # Push frame to streaming session (REAL-TIME PROCESSING)
                    push_result = stream.push_frame(frame)
                    if push_result is not None:
                        await push_result

                    if chunk_number % 50 == 0:  # Log every 1 second (50 * 20ms)
                        logger.info(f"Streamed {chunk_number} chunks ({chunk_number * chunk_duration_ms}ms)")

                    # Wait to simulate real-time (20ms between chunks)
                    await asyncio.sleep(chunk_duration_ms / 1000.0)

                # Signal end of audio stream
                flush_result = stream.flush()
                if flush_result is not None:
                    await flush_result
                logger.info(f"Finished streaming {chunk_number} audio chunks")

            # Start streaming task
            stream_task = asyncio.create_task(stream_audio_chunks())

            # Process recognition events in real-time
            logger.info("Processing recognition events...")
            async for event in stream:
                if event.type == stt.SpeechEventType.INTERIM_TRANSCRIPT:
                    interim_count += 1
                    text = event.alternatives[0].text if event.alternatives else ""
                    logger.info(f"INTERIM #{interim_count}: '{text}'")

                elif event.type == stt.SpeechEventType.FINAL_TRANSCRIPT:
                    final_count += 1
                    text = event.alternatives[0].text if event.alternatives else ""
                    confidence = event.alternatives[0].confidence if event.alternatives else 0.0
                    logger.info(f"FINAL #{final_count}: '{text}' (confidence: {confidence:.2f})")

                elif event.type == stt.SpeechEventType.END_OF_SPEECH:
                    logger.info("END_OF_SPEECH detected")

            # Wait for streaming to complete
            await stream_task
            await stream.aclose()

            # Summary
            end_time = time.time()
            processing_time = end_time - start_time
            logger.info("=== STREAMING COMPLETE ===")
            logger.info(f"Total processing time: {processing_time:.2f}s")
            logger.info(f"Interim results: {interim_count}")
            logger.info(f"Final results: {final_count}")
            logger.info(f"Real-time factor: {(total_frames / sample_rate) / processing_time:.2f}x")

            return True

    except Exception as e:
        logger.error(f"Real-time streaming failed: {e}")
        logger.exception("Full error details:")
        return False


async def process_audio_file_batch(stt_instance: STT, audio_file: Path):
    """
    Demonstrate BATCH PROCESSING (DISCOURAGED for real-time applications).

    This loads the entire file at once - NOT recommended for real-time streaming.
    Shown here only for comparison purposes.
    """
    logger.info(f"=== BATCH PROCESSING (DISCOURAGED): {audio_file.name} ===")

    try:
        # Read an entire file at once (NOT RECOMMENDED for real-time)
        with open(audio_file, 'rb') as f:
            audio_data = f.read()

        size_kb = len(audio_data) / 1024
        logger.warning(f"Loading entire file at once: {size_kb:.1f} KB")
        logger.warning("This approach defeats the purpose of real-time streaming!")

        # This would typically use the batch recognition API
        # For demonstration, we'll just simulate processing time
        start_time = time.time()
        await asyncio.sleep(1.0)  # Simulate processing delay
        end_time = time.time()

        logger.info(f"Batch processing time: {end_time - start_time:.2f}s")
        logger.warning("Batch processing provides no interim results!")
        logger.warning("User has to wait for complete processing before getting any results!")

        return True

    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        return False


async def demonstrate_live_audio_simulation(stt_instance: STT):
    """
    Demonstrate processing of simulated live audio (like from a microphone).

    This shows how the plugin would work with actual live audio input.
    """
    logger.info("=== SIMULATED LIVE AUDIO PROCESSING ===")

    try:
        # Create a streaming session
        stream = stt_instance.stream()
        logger.info("Live audio streaming session created")

        # Simulate live audio frames (like from microphone)
        sample_rate = 16000
        channels = 1
        chunk_duration_ms = 20  # 20ms chunks
        samples_per_chunk = int(sample_rate * chunk_duration_ms / 1000)

        logger.info(f"Simulating live audio: {sample_rate}Hz, {channels} channel, {chunk_duration_ms}ms chunks")

        async def generate_live_audio():
            """Generate simulated live audio frames."""
            for i in range(150):  # 3 seconds of audio (150 * 20ms)
                # Generate some audio data (silence with occasional noise)
                if i % 25 == 0:  # Add some "speech" every 500ms
                    # Simulate speech with random noise
                    audio_data = np.random.randint(-1000, 1000, samples_per_chunk, dtype=np.int16)
                else:
                    # Silence
                    audio_data = np.zeros(samples_per_chunk, dtype=np.int16)

                # Create AudioFrame
                frame = rtc.AudioFrame(
                    data=audio_data,
                    sample_rate=sample_rate,
                    num_channels=channels,
                    samples_per_channel=samples_per_chunk,
                )

                # Push frame to streaming session
                push_result = stream.push_frame(frame)
                if push_result is not None:
                    await push_result

                # Real-time delay
                await asyncio.sleep(chunk_duration_ms / 1000.0)

            flush_result = stream.flush()
            if flush_result is not None:
                await flush_result
            logger.info("Finished generating simulated live audio")

        # Start audio generation
        audio_task = asyncio.create_task(generate_live_audio())

        # Process results
        result_count = 0
        async for event in stream:
            result_count += 1
            if event.type == stt.SpeechEventType.INTERIM_TRANSCRIPT:
                text = event.alternatives[0].text if event.alternatives else ""
                logger.info(f"Live interim: '{text}'")
            elif event.type == stt.SpeechEventType.FINAL_TRANSCRIPT:
                text = event.alternatives[0].text if event.alternatives else ""
                logger.info(f"Live final: '{text}'")

        await audio_task
        await stream.aclose()

        logger.info(f"Live audio simulation complete. Processed {result_count} events.")
        return True

    except Exception as e:
        logger.error(f"Live audio simulation failed: {e}")
        logger.exception("Full error details:")
        return False


async def demonstrate_stt_configurations():
    """Demonstrate different STT configurations optimized for streaming."""
    print("\n" + "=" * 70)
    print("DEMONSTRATING STREAMING STT CONFIGURATIONS")
    print("=" * 70)

    # Get credentials
    creds = YandexCredentials.from_env()

    # Test streaming-optimized configurations
    configurations = [
        {
            "language": "ru-RU",
            "interim_results": True,
            "description": "Russian STT with interim results (RECOMMENDED)"
        },
        {
            "language": "en-US",
            "interim_results": True,
            "description": "English STT with interim results (RECOMMENDED)"
        },
        {
            "detect_language": True,
            "interim_results": True,
            "description": "Auto-detect language with interim results"
        },
        {
            "language": "ru-RU",
            "interim_results": False,
            "description": "Russian STT without interim results (NOT RECOMMENDED for real-time)"
        },
    ]

    for config in configurations:
        print(f"\n--- {config['description']} ---")
        try:
            stt_instance = STT(
                api_key=creds.api_key,
                folder_id=creds.folder_id,
                **{k: v for k, v in config.items() if k != "description"}
            )
            print(f"[OK] Configuration created successfully")
            print(f"Language: {stt_instance._opts.language}")
            print(f"Interim results: {stt_instance._opts.interim_results}")
            print(f"Sample rate: {stt_instance._opts.sample_rate} Hz")
            print(f"Audio encoding: {stt_instance._opts.audio_encoding}")

            if not stt_instance._opts.interim_results:
                print("[WARNING] No interim results - poor real-time experience!")

        except Exception as e:
            print(f"[ERROR] Failed to create STT instance: {e}")


async def main():
    """The main demonstration function showing different streaming approaches."""
    print("Yandex SpeechKit STT Plugin - Real-Time Streaming Demonstration")
    print("=" * 70)
    print("This demo shows the difference between:")
    print("1. [OK] Real-time streaming (RECOMMENDED)")
    print("2. [OK] Emulated streaming from files (for testing)")
    print("3. [OK] Simulated live audio (like microphone)")
    print("4. [NO] Batch processing (DISCOURAGED for real-time)")
    print("=" * 70)

    # Check environment
    if not check_environment():
        print("\nEnvironment check failed. Please check your .env file.")
        return False

    # Find audio fixtures
    audio_files = find_audio_fixtures()
    if not audio_files:
        print("No audio files available for demonstration.")
        print("Run 'make fixtures' to generate test audio files.")
        return False

    # Demonstrate STT configurations
    await demonstrate_stt_configurations()

    # Get credentials
    creds = YandexCredentials.from_env()

    # Demo 1: Real-time streaming with audio files
    print("\n" + "=" * 70)
    print("DEMO 1: REAL-TIME STREAMING FROM FILES (RECOMMENDED)")
    print("=" * 70)
    print("This demonstrates proper streaming by processing audio in small chunks")
    print("as they would arrive in a real-time scenario.")

    # Process a few files with real-time streaming using correct languages
    demo_files = audio_files[:2]  # Process first 2 files

    for audio_file in demo_files:
        # Determine language based on filename
        if "english" in audio_file.name.lower():
            language = "en-US"
        elif "russian" in audio_file.name.lower():
            language = "ru-RU"
        else:
            language = "ru-RU"  # Default to Russian

        # Create STT instance for the specific language
        stt_for_file = STT(
            api_key=creds.api_key,
            folder_id=creds.folder_id,
            language=language,
            interim_results=True,  # Enable real-time interim results
        )

        success = await stream_audio_file_realtime(stt_for_file, audio_file)
        if success:
            print(f"[OK] Successfully streamed {audio_file.name} ({language})")
        else:
            print(f"[FAIL] Failed to stream {audio_file.name} ({language})")
        print("-" * 50)

    # Demo 2: Simulated live audio
    print("\n" + "=" * 70)
    print("DEMO 2: SIMULATED LIVE AUDIO PROCESSING")
    print("=" * 70)
    print("This simulates processing live audio as it would come from a microphone.")

    # Create an STT instance for live simulation (use English for demo)
    stt_live = STT(
        api_key=creds.api_key,
        folder_id=creds.folder_id,
        language="en-US",  # Use English for live simulation
        interim_results=True,
    )

    success = await demonstrate_live_audio_simulation(stt_live)
    if success:
        print("[OK] Live audio simulation completed")
    else:
        print("[FAIL] Live audio simulation failed")

    # Demo 3: Batch processing (for comparison)
    print("\n" + "=" * 70)
    print("DEMO 3: BATCH PROCESSING (DISCOURAGED)")
    print("=" * 70)
    print("This shows why batch processing is NOT suitable for real-time applications.")

    if demo_files:
        # Use the first file with its appropriate language
        first_file = demo_files[0]
        if "english" in first_file.name.lower():
            batch_language = "en-US"
        else:
            batch_language = "ru-RU"

        stt_batch = STT(
            api_key=creds.api_key,
            folder_id=creds.folder_id,
            language=batch_language,
        )
        await process_audio_file_batch(stt_batch, first_file)

    # Summary
    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("Key Takeaways:")
    print("[DO] Use real-time streaming with push_frame() for live applications")
    print("[DO] Process audio in small chunks (20ms typical)")
    print("[DO] Handle interim and final results asynchronously")
    print("[DO] Enable interim_results=True for responsive UX")
    print("[DONT] Avoid loading entire audio files for real-time processing")
    print("[DONT] Batch processing eliminates real-time benefits")
    print()
    print("For more examples, see:")
    print("- tests/e2e/test_real_audio_processing.py (complete working examples)")
    print("- LiveKit Agents documentation for integration patterns")
    print()
    print("The Yandex SpeechKit STT plugin is ready for real-time streaming!")

    return True


if __name__ == "__main__":
    try:
        print("Loading environment variables from .env file...")

        # Check if .env file exists
        env_file = Path(".env")
        if env_file.exists():
            print("Found .env file")
        else:
            print("WARNING: .env file not found - using system environment variables")

        # Run the demonstration
        success = asyncio.run(main())

        print(f"\nDemonstration {'completed successfully' if success else 'completed with issues'}!")
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\nDemonstration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
