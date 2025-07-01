"""Test infrastructure for LiveKit Agent end-to-end testing.

This package provides utilities for creating real LiveKit room scenarios with
participants, agents, and audio processing for comprehensive testing.
"""

from .agent_fixtures import AgentDeployment
from .participant_simulator import ParticipantSimulator
from .room_manager import RoomManager

__all__ = ["RoomManager", "ParticipantSimulator", "AgentDeployment"]
