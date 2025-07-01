#!/usr/bin/env python3
"""Basic LiveKit Integration Tests.

These tests implement REAL end-to-end LiveKit agent scenarios with:
1. Real LiveKit room creation and WebSocket connections
2. Real participant simulation publishing audio tracks
3. Real agent deployment processing participant audio through Yandex STT
4. Complete pipeline validation: Participant → Room → Agent → STT → Transcription

This is the TRUE LiveKit integration that the documentation promises.
"""

import asyncio
import logging
from pathlib import Path
from typing import List

import pytest

from tests import FIXTURES_DIR

from .infrastructure import AgentDeployment, ParticipantSimulator, RoomManager
from .validation_utils import validate_russian_transcription

logger = logging.getLogger("basic-livekit-integration")


class TestBasicLiveKitIntegration:
    """Basic tests for true LiveKit room integration with Russian STT agents."""

    @pytest.mark.asyncio
    async def test_basic_room_creation_and_cleanup(self, room_manager: "RoomManager") -> None:
        """Test basic LiveKit room creation and cleanup.

        DASHBOARD EXPECTATION:
        - Room name: 'test-simple-expect-0p-room-XXXXXXXX'
        - Participants: 0 (no participants connect)
        - Duration: ~1-2 seconds
        - Status: Closed (after test completes)
        """
        logger.info("=== Testing Basic Room Creation ===")
        logger.info("DASHBOARD: Expect 0 participants in 'test-simple-expect-0p-room-*'")

        # Create room without participants
        room_name = await room_manager.create_room(expected_participants=0, test_type="test-simple")
        assert room_name is not None
        assert room_name.startswith("test-simple-expect-0p-room-")

        logger.info(f"Room created: {room_name}")
        logger.info(
            f"DASHBOARD: Check https://cloud.livekit.io/projects/*/sessions for room: {room_name}"
        )

        # Cleanup room
        await room_manager.delete_room(room_name)
        logger.info("Room cleanup completed")

    @pytest.mark.asyncio
    async def test_participant_connection_to_room(self, room_manager: "RoomManager") -> None:
        """Test participant connecting to the LiveKit room.

        DASHBOARD EXPECTATION:
        - Room name: 'test-simple-expect-1p-room-XXXXXXXX'
        - Participants: 1 (should show in https://cloud.livekit.io/projects/*/sessions)
        - Duration: ~3-4 seconds
        - Status: Closed (after test completes)
        """
        logger.info("=== Testing Participant Connection ===")
        logger.info("DASHBOARD: Expect 1 participant in 'test-simple-expect-1p-room-*'")

        # Create a room with 1 participant expected
        room_name = await room_manager.create_room(expected_participants=1, test_type="test-simple")
        logger.info(f"Room created: {room_name}")
        logger.info(
            f"DASHBOARD: Check https://cloud.livekit.io/projects/*/sessions for room: {room_name}"
        )

        try:
            # Connect participant to room
            participant_room = await room_manager.connect_to_room(
                room_name=room_name,
                participant_identity="test-participant",
                participant_name="Test Participant",
            )

            assert participant_room is not None
            logger.info("Participant connected to room")

            # Wait a moment to ensure the connection is stable
            await asyncio.sleep(1.0)

            # Disconnect participant
            await room_manager.disconnect_from_room(room_name, "test-participant")
            logger.info("Participant disconnected")

        finally:
            await room_manager.delete_room(room_name)

    @pytest.mark.parametrize(
        "audio_file_name,expected_keywords",
        [
            ("russian_greeting.wav", ["привет", "дела", "меня", "зовут"]),
            # TODO: DO NOT TOUCH!!!
            # ("russian_weather.wav", ["сегодня", "погода", "прогулки"]),
            # ("russian_learning.wav", ["изучаю", "русский", "язык"]),
        ],
    )
    @pytest.mark.asyncio
    async def test_complete_agent_participant_pipeline(
        self,
        room_manager: "RoomManager",
        agent_deployment: "AgentDeployment",
        audio_file_name: str,
        expected_keywords: List[str],
    ) -> None:
        """REAL end-to-end test: Complete LiveKit pipeline with agent and participant.

        This test implements the TRUE LiveKit integration:
        1. Creates real LiveKit room
        2. Deploys real agent with Yandex STT
        3. Connects real participant
        4. Participant publishes Russian audio
        5. Agent processes audio through the complete LiveKit pipeline
        6. Validates Russian transcription results
        """
        logger.info(f"=== REAL E2E Pipeline Test: {audio_file_name} ===")

        # Get an audio file
        audio_file = FIXTURES_DIR / audio_file_name
        assert audio_file.exists(), f"Audio file not found: {audio_file}"

        # Create a room with 2 participants expected (agent and participant)
        room_name = await room_manager.create_room(expected_participants=2, test_type="test-agent")
        logger.info(f"Created LiveKit room: {room_name}")

        try:
            # Deploy agent to room
            logger.info("Deploying Russian STT agent to room...")
            agent_worker = await agent_deployment.deploy_russian_stt_agent(
                room_name=room_name,
                agent_identity="russian-stt-agent",
            )
            assert agent_worker is not None
            logger.info("Agent deployed successfully")

            # Wait for the agent to be ready
            await asyncio.sleep(2.0)

            # Connect participant to room
            logger.info("Connecting participant to room...")
            participant_room = await room_manager.connect_to_room(
                room_name=room_name,
                participant_identity="russian-speaker",
                participant_name="Russian Speaker",
            )
            logger.info("Participant connected")

            # Create participant simulator
            participant = ParticipantSimulator(
                room=participant_room,
                participant_identity="russian-speaker",
            )

            # Wait for agent to detect participant (generous for live tests)
            await asyncio.sleep(3.0)  # Increased for live network conditions

            # Participant starts speaking Russian in a separate thread
            logger.info(f"Participant speaking Russian: {audio_file_name}")
            participant.start_speaking_in_thread(audio_file, loop=False)

            # Wait for audio to complete
            await participant.wait_for_audio_completion(audio_file)

            # Give agent time to process and transcribe (generous for live STT)
            await asyncio.sleep(10.0)  # Much longer for live STT processing

            # Wait for the participant thread to complete (generous timeout)
            participant.wait_for_completion(timeout=30.0)  # Increased for live tests

            # Wait for an agent to collect transcriptions with generous timeout for live tests
            logger.info("Waiting for agent transcriptions...")
            transcriptions = await agent_deployment.wait_for_transcriptions(
                room_name=room_name,
                expected_count=1,
                timeout=60.0,  # Generous timeout for live STT processing
                agent_identity="russian-stt-agent",
            )

            # Give extra time for STT processing to complete
            if len(transcriptions) == 0:
                logger.info("No transcriptions yet, waiting additional time for STT processing...")
                await asyncio.sleep(10.0)  # Longer wait for live tests
                transcriptions = agent_deployment.get_transcriptions(room_name, "russian-stt-agent")

            # Validate transcription results
            assert len(transcriptions) > 0, f"Agent should transcribe {audio_file_name}"

            valid_transcription_found = False
            for transcription in transcriptions:
                if validate_russian_transcription(transcription, expected_keywords):
                    valid_transcription_found = True
                    logger.info(f"REAL E2E transcription: '{transcription}'")
                    break

            assert valid_transcription_found, (
                f"No valid Russian transcription from complete pipeline for {audio_file_name}. "
                f"Got: {transcriptions}"
            )

            logger.info(f"COMPLETE E2E PIPELINE SUCCESS: {audio_file_name}")

            # Cleanup participant
            await participant.cleanup()
            await room_manager.disconnect_from_room(room_name, "russian-speaker")

        finally:
            # Cleanup agent and room
            await agent_deployment.stop_agent(room_name, "russian-stt-agent")
            await room_manager.delete_room(room_name)

    @pytest.mark.asyncio
    async def test_agent_deployment_and_cleanup(
        self,
        room_manager: "RoomManager",
        agent_deployment: "AgentDeployment",
    ) -> None:
        """Test agent deployment and cleanup processes."""
        logger.info("=== Testing Agent Deployment ===")

        # Create room without participants (agent deployment only)
        room_name = await room_manager.create_room(expected_participants=0, test_type="test-agent")
        logger.info(f"Room created: {room_name}")

        try:
            # Deploy agent
            agent_worker = await agent_deployment.deploy_russian_stt_agent(
                room_name=room_name,
                agent_identity="test-agent",
            )

            assert agent_worker is not None
            assert agent_deployment.is_agent_deployed(room_name, "test-agent")
            logger.info("Agent deployed successfully")

            # Wait for the agent to be ready (generous for live tests)
            await asyncio.sleep(10)  # Increased for live deployment

            # Stop agent
            await agent_deployment.stop_agent(room_name, "test-agent")
            assert not agent_deployment.is_agent_deployed(room_name, "test-agent")
            logger.info("Agent stopped successfully")

        finally:
            await room_manager.delete_room(room_name)

    @pytest.mark.asyncio
    async def test_very_basic_integration_russian_greeting(
        self,
        room_manager: "RoomManager",
        agent_deployment: "AgentDeployment",
        russian_greeting_audio: Path,
    ) -> None:
        """VERY basic integration test: Agent + Participant + Russian greeting transcription.

        This is the simplest possible test that proves the complete LiveKit pipeline works.
        """
        logger.info("=== VERY BASIC INTEGRATION TEST ===")

        # Create a room with 2 participants expected (agent and participant)
        room_name = await room_manager.create_room(expected_participants=2, test_type="test-agent")
        logger.info(f"Room: {room_name}")

        try:
            # Deploy agent
            await agent_deployment.deploy_russian_stt_agent(room_name)
            logger.info("Agent deployed")

            # Connect participant
            participant_room = await room_manager.connect_to_room(
                room_name, "speaker", "Russian Speaker"
            )
            participant = ParticipantSimulator(participant_room, "speaker")

            # Wait for connections
            logger.info("Sleeping 2.0s for connections to establish...")
            await asyncio.sleep(2.0)

            # Give agent time to subscribe to audio tracks
            logger.info("Waiting for agent to subscribe to audio tracks...")
            logger.info("Sleeping 2.0s for agent audio track subscription...")
            await asyncio.sleep(2.0)

            # Speak Russian greeting in a separate thread
            logger.info("Speaking Russian greeting...")
            participant.start_speaking_in_thread(russian_greeting_audio, loop=False)

            # Wait for audio to complete
            await participant.wait_for_audio_completion(russian_greeting_audio)

            # Wait for the participant thread to complete
            participant.wait_for_completion(timeout=10.0)

            # Wait for transcription
            transcriptions = await agent_deployment.wait_for_transcriptions(
                room_name, expected_count=1, timeout=60.0
            )

            # Validate
            assert len(transcriptions) > 0, "Should get transcription"

            valid_found = False
            for text in transcriptions:
                if validate_russian_transcription(text, ["привет"]):
                    valid_found = True
                    logger.info(f"SUCCESS: '{text}'")
                    break

            assert valid_found, f"No valid Russian transcription: {transcriptions}"

            # Cleanup
            await participant.cleanup()
            await room_manager.disconnect_from_room(room_name, "speaker")

        finally:
            await agent_deployment.stop_agent(room_name)
            await room_manager.delete_room(room_name)
