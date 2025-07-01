"""Agent Deployment Fixtures for LiveKit Agent Testing.

This module provides utilities for deploying and managing LiveKit agents that use the
Yandex STT plugin in real room scenarios.

## Text Stream Warnings

To avoid "ignoring text stream with topic 'lk.transcription'" warnings,
this implementation disables transcription output (transcription_enabled=False)
since we handle transcriptions via agent callbacks, not room text streams.

This is a simpler and more reliable approach than attempting to implement
text stream handlers, which did not eliminate the warnings due to internal
LiveKit SDK processing.

Reference: https://github.com/livekit/python-sdks/issues/391
"""

from __future__ import annotations

import asyncio
import logging
import threading
from typing import Callable, Dict, List

import numpy as np
from livekit.agents import (
    Agent,
    AgentSession,
    RoomOutputOptions,
    StopResponse,
    llm,
)

from livekit import rtc
from livekit.plugins.yandex import STT

logger = logging.getLogger("agent-fixtures")


class RussianSTTAgent(Agent):
    """A LiveKit agent that transcribes Russian speech using Yandex STT.

    Based on the official LiveKit transcriber pattern from:
    https://github.com/livekit/agents/blob/main/examples/other/transcription/transcriber.py
    """

    def __init__(self, transcription_callback: Callable[[str], None] | None = None) -> None:
        super().__init__(
            instructions="Russian speech transcription agent - not needed for STT-only",
            # STT is configured in the AgentSession, not here
        )
        self._transcription_callback = transcription_callback

    async def on_user_turn_completed(
        self, chat_ctx: llm.ChatContext, new_message: llm.ChatMessage
    ) -> None:
        """Called when the user has finished speaking - this is where we get transcriptions.

        This follows the official LiveKit pattern for handling transcriptions.
        """
        user_transcript = new_message.text_content
        logger.info(f"Agent transcribed: '{user_transcript}'")

        # Trigger callback for transcriptions
        if self._transcription_callback and user_transcript and user_transcript.strip():
            logger.info(f"Triggering transcription callback: '{user_transcript}'")
            self._transcription_callback(user_transcript)

        # Stop the response generation since we're only doing transcription
        raise StopResponse()


def resample_audio_simple(
    audio_data: np.ndarray, original_rate: int, target_rate: int
) -> np.ndarray:
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
    resampled_float = np.interp(new_indices, original_indices, audio_data)

    # Convert back to int16 with explicit casting to satisfy mypy
    resampled_int16: np.ndarray = np.array(resampled_float, dtype=np.int16)
    return resampled_int16


class LiveKitAgentSession:
    """A proper LiveKit agent session using the official agent framework pattern."""

    def __init__(
        self,
        room_name: str,
        agent_identity: str,
        yandex_api_key: str,
        yandex_folder_id: str,
        livekit_api_key: str,
        livekit_api_secret: str,
        livekit_ws_url: str,
    ) -> None:
        """Initialize LiveKit agent session."""
        self.room_name = room_name
        self.agent_identity = agent_identity
        self.yandex_api_key = yandex_api_key
        self.yandex_folder_id = yandex_folder_id
        self.livekit_api_key = livekit_api_key
        self.livekit_api_secret = livekit_api_secret
        self.livekit_ws_url = livekit_ws_url

        self._transcription_callback: Callable[[str], None] | None = None
        self._is_running = False
        self._agent_thread: threading.Thread | None = None
        self._agent_loop: asyncio.AbstractEventLoop | None = None

    def set_transcription_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for transcription results."""
        self._transcription_callback = callback

    async def start(self) -> None:
        """Start the LiveKit agent using a simplified but working approach."""
        if self._is_running:
            return

        logger.info(f"Starting LiveKit agent {self.agent_identity} for room {self.room_name}")

        # Run the agent in a separate thread
        def run_agent() -> None:
            """Run the agent in its own event loop."""
            self._agent_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._agent_loop)

            try:
                logger.info(f"Agent {self.agent_identity} starting in separate thread")
                self._agent_loop.run_until_complete(self._run_agent_session())

            except Exception as e:
                logger.error(f"Error in agent thread: {e}", exc_info=True)
            finally:
                self._agent_loop.close()

        # Start the agent thread
        self._agent_thread = threading.Thread(target=run_agent, daemon=True)
        self._agent_thread.start()

        self._is_running = True
        logger.info(f"LiveKit agent {self.agent_identity} started")

    async def _run_agent_session(self) -> None:
        """Run the actual agent session."""
        # Create room and connect
        room = rtc.Room()

        # Generate access token for agent
        from livekit import api

        token = (
            api.AccessToken(self.livekit_api_key, self.livekit_api_secret)
            .with_identity(self.agent_identity)
            .with_name(f"Agent {self.agent_identity}")
            .with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=self.room_name,
                    can_subscribe=True,
                    can_publish=False,  # Agent only listens
                )
            )
        )

        # Connect to a room
        logger.info(f"Agent {self.agent_identity} connecting to room {self.room_name}")
        await room.connect(self.livekit_ws_url, token.to_jwt())

        logger.info(f"Agent {self.agent_identity} connected to room")

        logger.info(f"Agent {self.agent_identity} connected to room")

        # Create an agent session with Yandex STT (following an official pattern)
        session = AgentSession(  # type: ignore[var-annotated]
            stt=STT(
                api_key=self.yandex_api_key,
                folder_id=self.yandex_folder_id,
                language="ru-RU",
                interim_results=True,
                sample_rate=16000,  # Yandex STT requires 16000Hz
            ),
            # TODO: investigate, base we are TTS agent
            # No LLM or TTS needed for a transcription-only agent(
        )

        # Create agent with transcription callback
        agent = RussianSTTAgent(transcription_callback=self._transcription_callback)

        # Start the agent session with transcription disabled to avoid text stream warnings
        logger.info(f"Agent {self.agent_identity} starting session")
        await session.start(
            agent=agent,
            room=room,
            room_output_options=RoomOutputOptions(
                # Disable transcription output to prevent "ignoring text stream with the topic
                # 'lk.transcription'" warnings
                # We handle transcriptions via agent callbacks, not via room text streams
                transcription_enabled=False,
                # Disable audio output since we're only doing transcription
                audio_enabled=False,
            ),
        )
        logger.info(f"Agent {self.agent_identity} session started successfully")

        # Keep the agent running
        try:
            while self._is_running:
                await asyncio.sleep(1.0)
        finally:
            logger.info(f"Agent {self.agent_identity} disconnecting")
            await room.disconnect()

    async def stop(self) -> None:
        """Stop the LiveKit agent session."""
        if not self._is_running:
            return

        logger.info(f"Stopping LiveKit agent {self.agent_identity}")

        self._is_running = False

        # Wait for the thread to complete
        if self._agent_thread:
            self._agent_thread.join(timeout=5.0)


class AgentDeployment:
    """Manages deployment of LiveKit agents with Yandex STT for testing."""

    def __init__(
        self,
        yandex_api_key: str,
        yandex_folder_id: str,
        livekit_api_key: str,
        livekit_api_secret: str,
        livekit_ws_url: str,
    ) -> None:
        """Initialize agent deployment manager.

        Args:
            yandex_api_key: Yandex Cloud API key
            yandex_folder_id: Yandex Cloud folder ID
            livekit_api_key: LiveKit API key
            livekit_api_secret: LiveKit API secret
            livekit_ws_url: LiveKit WebSocket URL
        """
        self.yandex_api_key = yandex_api_key
        self.yandex_folder_id = yandex_folder_id
        self.livekit_api_key = livekit_api_key
        self.livekit_api_secret = livekit_api_secret
        self.livekit_ws_url = livekit_ws_url

        self._agent_sessions: Dict[str, "LiveKitAgentSession"] = {}
        self._transcriptions: Dict[str, List[str]] = {}

    async def deploy_russian_stt_agent(
        self,
        room_name: str,
        agent_identity: str = "stt-agent",
    ) -> "LiveKitAgentSession":
        """Deploy a LiveKit agent with Russian STT to a room.

        Args:
            room_name: Name of room to deploy agent to
            agent_identity: Identity for the agent

        Returns:
            Deployed agent session
        """
        logger.info(f"Deploying Russian STT agent '{agent_identity}' to room '{room_name}'")

        # Create an agent session
        agent_session = LiveKitAgentSession(
            room_name=room_name,
            agent_identity=agent_identity,
            yandex_api_key=self.yandex_api_key,
            yandex_folder_id=self.yandex_folder_id,
            livekit_api_key=self.livekit_api_key,
            livekit_api_secret=self.livekit_api_secret,
            livekit_ws_url=self.livekit_ws_url,
        )

        # Initialize transcription storage for this agent
        agent_key = f"{room_name}:{agent_identity}"
        self._transcriptions[agent_key] = []

        def transcription_callback(text: str) -> None:
            logger.info(f"Callback received transcription: '{text}' for agent {agent_key}")

            # Avoid duplicate transcriptions
            if text not in self._transcriptions[agent_key]:
                self._transcriptions[agent_key].append(text)
                logger.info(f"Added new transcription for {agent_key}: '{text}'")
            else:
                logger.info(f"Duplicate transcription ignored for {agent_key}: '{text}'")

            logger.info(
                f"Total transcriptions for {agent_key}: {len(self._transcriptions[agent_key])}"
            )

        agent_session.set_transcription_callback(transcription_callback)

        # Start the agent session
        await agent_session.start()

        # Store session reference
        self._agent_sessions[agent_key] = agent_session

        logger.info(f"Agent {agent_identity} deployed successfully to room {room_name}")
        return agent_session

    async def stop_agent(self, room_name: str, agent_identity: str = "stt-agent") -> None:
        """Stop a deployed agent.

        Args:
            room_name: Name of the room containing the agent
            agent_identity: Identity of agent to stop
        """
        agent_key = f"{room_name}:{agent_identity}"

        if agent_key in self._agent_sessions:
            logger.info(f"Stopping agent {agent_identity} in room {room_name}")

            session = self._agent_sessions[agent_key]
            await session.stop()

            del self._agent_sessions[agent_key]
            logger.info(f"Agent {agent_identity} stopped")

    def get_transcriptions(self, room_name: str, agent_identity: str = "stt-agent") -> List[str]:
        """Get transcriptions collected by an agent.

        Args:
            room_name: Name of the room containing the agent
            agent_identity: Identity of agent

        Returns:
            List of transcriptions collected by the agent
        """
        agent_key = f"{room_name}:{agent_identity}"
        return self._transcriptions.get(agent_key, [])

    async def wait_for_transcriptions(
        self,
        room_name: str,
        expected_count: int = 1,
        timeout: float = 60.0,  # Increased default timeout for live tests
        agent_identity: str = "stt-agent",
    ) -> List[str]:
        """Wait for agent to collect expected number of transcriptions.

        Args:
            room_name: Name of room containing the agent
            expected_count: Expected number of transcriptions
            timeout: Maximum time to wait in seconds
            agent_identity: Identity of agent

        Returns:
            List of transcriptions collected
        """
        agent_key = f"{room_name}:{agent_identity}"
        logger.info(f"Waiting for {expected_count} transcriptions from agent {agent_identity}")

        start_time = asyncio.get_event_loop().time()

        while True:
            transcriptions = self._transcriptions.get(agent_key, [])

            # Debug: Log current transcriptions
            if len(transcriptions) > 0:
                logger.info(f"Current transcriptions for {agent_key}: {transcriptions}")

            if len(transcriptions) >= expected_count:
                logger.info(
                    f"Agent collected {len(transcriptions)} transcriptions: {transcriptions}"
                )
                return transcriptions

            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout:
                logger.warning(
                    f"Timeout waiting for transcriptions: {len(transcriptions)}/{expected_count} "
                    f"after {elapsed:.1f}s"
                )
                return transcriptions

            # Wait before checking again
            logger.debug("Sleeping 0.5s before checking transcriptions again...")
            await asyncio.sleep(0.5)

    async def cleanup_all_agents(self) -> None:
        """Stop all deployed agents and clean up resources."""
        logger.info("Cleaning up all deployed agents...")

        # Stop all agents
        for agent_key, session in list(self._agent_sessions.items()):
            try:
                await session.stop()
            except Exception as e:
                logger.warning(f"Error stopping agent {agent_key}: {e}")

        self._agent_sessions.clear()
        self._transcriptions.clear()
        logger.info("All agents cleaned up")

    @property
    def active_agents(self) -> Dict[str, "LiveKitAgentSession"]:
        """Currently get active agents."""
        return self._agent_sessions.copy()

    def is_agent_deployed(self, room_name: str, agent_identity: str = "stt-agent") -> bool:
        """Check if an agent is deployed to a room.

        Args:
            room_name: Name of room to check
            agent_identity: Identity of agent to check

        Returns:
            True if the agent is deployed, False otherwise
        """
        agent_key = f"{room_name}:{agent_identity}"
        return agent_key in self._agent_sessions
