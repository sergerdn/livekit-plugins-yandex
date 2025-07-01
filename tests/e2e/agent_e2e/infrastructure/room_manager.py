"""LiveKit Room Management for End-to-End Testing.

This module provides utilities for creating and managing real LiveKit rooms for testing
agent scenarios with actual WebSocket connections.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Awaitable, Callable, Dict, Optional

from livekit import api, rtc

logger = logging.getLogger("room-manager")


class RoomManager:
    """Manages LiveKit rooms for end-to-end testing."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        ws_url: str,
    ) -> None:
        """Initialize the room manager with LiveKit credentials.

        Args:
            api_key: LiveKit API key
            api_secret: LiveKit API secret
            ws_url: LiveKit WebSocket URL
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.ws_url = ws_url
        self._rooms: Dict[str, rtc.Room] = {}

        # Initialize LiveKit API client
        self._api_client = api.LiveKitAPI(
            url=ws_url,
            api_key=api_key,
            api_secret=api_secret,
        )

    async def create_room(
        self,
        room_name: Optional[str] = None,
        expected_participants: int = 1,
        test_type: str = "test-simple",
    ) -> str:
        """Create a new LiveKit room.

        Args:
            room_name: Optional room name. If not provided, it generates a unique name.
            expected_participants: Number of participants expected in this room
            test_type: Type of test (e.g., 'test-simple', 'test-agent')

        Returns:
            The created room name
        """
        if room_name is None:
            room_id = uuid.uuid4().hex[:8]
            room_name = f"{test_type}-expect-{expected_participants}p-room-{room_id}"

        logger.info(f"Creating LiveKit room: {room_name}")

        try:
            # Create room via API
            room_info = await self._api_client.room.create_room(
                api.CreateRoomRequest(name=room_name)
            )
            logger.info(f"Room created successfully: {room_info.name}")
            return room_info.name

        except Exception as e:
            logger.error(f"Failed to create room {room_name}: {e}")
            raise

    async def delete_room(self, room_name: str) -> None:
        """Delete a LiveKit room.

        Args:
            room_name: Name of room to delete
        """
        logger.info(f"Deleting LiveKit room: {room_name}")

        # Disconnect any connected rooms first
        if room_name in self._rooms:
            room = self._rooms[room_name]
            await room.disconnect()
            del self._rooms[room_name]

        # Delete room via API
        await self._api_client.room.delete_room(api.DeleteRoomRequest(room=room_name))
        logger.info(f"Room deleted successfully: {room_name}")

    def generate_access_token(
        self,
        room_name: str,
        participant_identity: str,
        participant_name: Optional[str] = None,
        permissions: Optional[Dict[str, bool]] = None,
    ) -> str:
        """Generate access token for participant to join room.

        Args:
            room_name: Name of the room
            participant_identity: Unique identity for participant
            participant_name: Display name for participant
            permissions: Optional permissions dict

        Returns:
            JWT access token
        """
        if permissions is None:
            permissions = {
                "canPublish": True,
                "canSubscribe": True,
                "canPublishData": True,
            }

        token = (
            api.AccessToken(self.api_key, self.api_secret)
            .with_identity(participant_identity)
            .with_name(participant_name or participant_identity)
            .with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=room_name,
                    can_publish=permissions.get("canPublish", True),
                    can_subscribe=permissions.get("canSubscribe", True),
                    can_publish_data=permissions.get("canPublishData", True),
                )
            )
        )

        return token.to_jwt()

    async def connect_to_room(
        self,
        room_name: str,
        participant_identity: str,
        participant_name: Optional[str] = None,
    ) -> rtc.Room:
        """Connect to a LiveKit room as a participant.

        Args:
            room_name: Name of room to connect to
            participant_identity: Unique identity for this connection
            participant_name: Display name for participant

        Returns:
            Connected Room instance
        """
        logger.info(f"Connecting to room {room_name} as {participant_identity}")

        # Generate an access token
        token = self.generate_access_token(
            room_name=room_name,
            participant_identity=participant_identity,
            participant_name=participant_name,
        )

        # Create and connect a room
        room = rtc.Room()

        try:
            await room.connect(self.ws_url, token)

            # Store room reference for cleanup
            room_key = f"{room_name}:{participant_identity}"
            self._rooms[room_key] = room

            logger.info(f"Successfully connected to room {room_name}")
            return room

        except Exception as e:
            logger.error(f"Failed to connect to room {room_name}: {e}")
            await room.disconnect()
            raise

    async def disconnect_from_room(self, room_name: str, participant_identity: str) -> None:
        """Disconnect from a LiveKit room.

        Args:
            room_name: Name of room to disconnect from
            participant_identity: Identity of participant to disconnect
        """
        room_key = f"{room_name}:{participant_identity}"

        if room_key in self._rooms:
            room = self._rooms[room_key]
            logger.info(f"Disconnecting {participant_identity} from room {room_name}")

            try:
                await room.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting from room: {e}")
            finally:
                del self._rooms[room_key]

    async def cleanup_all_rooms(self) -> None:
        """Disconnect from all rooms and clean up resources."""
        logger.info("Cleaning up all room connections...")

        # Disconnect from all rooms
        for room_key, room in list(self._rooms.items()):
            try:
                await room.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting from {room_key}: {e}")

        self._rooms.clear()

        # Close the API client to prevent unclosed session warnings
        try:
            aclose_method: Callable[[], Awaitable[None]] = self._api_client.aclose
            await aclose_method()
            logger.debug("API client closed successfully")
        except Exception as e:
            logger.warning(f"Error closing API client: {e}")

        logger.info("All room connections cleaned up")

    # noinspection PyMethodMayBeStatic
    async def wait_for_participants(
        self,
        room: rtc.Room,
        expected_count: int,
        timeout: float = 30.0,
    ) -> bool:
        """Wait for the expected number of participants to join the room.

        Args:
            room: Room to monitor
            expected_count: Expected number of participants
            timeout: Maximum time to wait in seconds

        Returns:
            True if expected participants joined, False if timeout
        """
        logger.info(f"Waiting for {expected_count} participants to join room...")

        start_time = asyncio.get_event_loop().time()

        while True:
            current_count = len(room.remote_participants) + 1  # +1 for local participant

            if current_count >= expected_count:
                logger.info(f"Expected participants joined: {current_count}/{expected_count}")
                return True

            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout:
                logger.warning(
                    f"Timeout waiting for participants: {current_count}/{expected_count} after {elapsed:.1f}s"
                )
                return False

            # Wait a bit before checking again
            await asyncio.sleep(0.5)
