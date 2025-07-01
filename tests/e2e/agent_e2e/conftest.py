#!/usr/bin/env python3
"""Shared fixtures and utilities for agent end-to-end tests.

This module provides a common setup for testing LiveKit Agents with Yandex STT,
including room management, participant simulation, and Russian audio processing.
"""

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, AsyncGenerator, Dict, List

if TYPE_CHECKING:
    from .infrastructure import AgentDeployment, RoomManager
    from .validation_utils import AudioSimulator

import pytest
import pytest_asyncio

from livekit.plugins.yandex import STT
from tests import FIXTURES_DIR

# Configure logging for tests
logger = logging.getLogger("agent-e2e-tests")


@pytest.fixture(scope="session")
def agent_credentials() -> Dict[str, str]:
    """Get required credentials for agent mode testing."""
    yandex_api_key = os.environ.get("YANDEX_API_KEY")
    yandex_folder_id = os.environ.get("YANDEX_FOLDER_ID")
    livekit_api_key = os.environ.get("LIVEKIT_API_KEY")
    livekit_api_secret = os.environ.get("LIVEKIT_API_SECRET")
    livekit_ws_url = os.environ.get("LIVEKIT_WS_URL")

    if not all(
        [yandex_api_key, yandex_folder_id, livekit_api_key, livekit_api_secret, livekit_ws_url]
    ):
        pytest.skip("Required credentials not available for agent mode testing")

    # Type assertions since we've checked all values are not None
    assert (
        yandex_api_key
        and yandex_folder_id
        and livekit_api_key
        and livekit_api_secret
        and livekit_ws_url
    )

    return {
        "yandex_api_key": yandex_api_key,
        "yandex_folder_id": yandex_folder_id,
        "livekit_api_key": livekit_api_key,
        "livekit_api_secret": livekit_api_secret,
        "livekit_ws_url": livekit_ws_url,
    }


@pytest.fixture
def russian_audio_files() -> List[Path]:
    """Get available Russian audio test files."""

    if not FIXTURES_DIR.exists():
        pytest.skip("Audio fixtures directory not found - run 'make fixtures'")

    # Find Russian audio files
    russian_files = list(FIXTURES_DIR.glob("russian_*.wav"))
    if not russian_files:
        pytest.skip("No Russian audio files found - run 'make fixtures'")

    logger.info(f"Found {len(russian_files)} Russian audio files")
    for file in russian_files:
        logger.info(f"  - {file.name}")

    return russian_files


@pytest.fixture
def russian_greeting_audio() -> Path:
    """Get the Russian greeting audio file specifically."""

    greeting_file = FIXTURES_DIR / "russian_greeting.wav"

    assert greeting_file.exists()
    assert greeting_file.is_file()

    return greeting_file


@pytest.fixture
def russian_weather_audio() -> Path:
    """Get the Russian weather audio file specifically."""
    weather_file = FIXTURES_DIR / "russian_weather.wav"

    if not weather_file.exists():
        pytest.skip("Russian weather audio file not found - run 'make fixtures'")

    return weather_file


@pytest.fixture
def russian_stt_agent(agent_credentials: Dict[str, str]) -> STT:
    """Create a Yandex STT instance configured for the Russian language."""
    return STT(
        api_key=agent_credentials["yandex_api_key"],
        folder_id=agent_credentials["yandex_folder_id"],
        language="ru-RU",  # Russian language for all agent tests
        interim_results=True,  # Essential for real-time agent experience
        sample_rate=16000,
    )


@pytest.fixture
def audio_simulator() -> "AudioSimulator":
    """Create an audio simulator for participant speech simulation."""
    from .validation_utils import AudioSimulator

    return AudioSimulator()


# LiveKit Infrastructure Fixtures


@pytest_asyncio.fixture
async def room_manager(agent_credentials: Dict[str, str]) -> AsyncGenerator["RoomManager", None]:
    """Create a room manager for LiveKit operations."""
    from .infrastructure import RoomManager

    manager = RoomManager(
        api_key=agent_credentials["livekit_api_key"],
        api_secret=agent_credentials["livekit_api_secret"],
        ws_url=agent_credentials["livekit_ws_url"],
    )

    yield manager

    # Clean up all rooms
    await manager.cleanup_all_rooms()


@pytest_asyncio.fixture
async def agent_deployment(
    agent_credentials: Dict[str, str],
) -> AsyncGenerator["AgentDeployment", None]:
    """Create an agent deployment manager."""
    from .infrastructure import AgentDeployment

    deployment = AgentDeployment(
        yandex_api_key=agent_credentials["yandex_api_key"],
        yandex_folder_id=agent_credentials["yandex_folder_id"],
        livekit_api_key=agent_credentials["livekit_api_key"],
        livekit_api_secret=agent_credentials["livekit_api_secret"],
        livekit_ws_url=agent_credentials["livekit_ws_url"],
    )

    yield deployment

    # Clean up all agents
    await deployment.cleanup_all_agents()
