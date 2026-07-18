"""Wake-on-LAN client for waking the build server."""

import socket
import struct
import logging

from app.config import settings

logger = logging.getLogger(__name__)


def send_magic_packet(mac_address: str, broadcast: str | None = None) -> bool:
    """
    Send a Wake-on-LAN magic packet to wake the build server.

    The magic packet is 6 bytes of 0xFF followed by the target MAC address
    repeated 16 times, sent as a UDP broadcast.
    """
    broadcast = broadcast or settings.build_server_broadcast

    # Parse MAC address
    mac_bytes = bytes.fromhex(mac_address.replace(":", "").replace("-", ""))
    if len(mac_bytes) != 6:
        logger.error(f"Invalid MAC address: {mac_address}")
        return False

    # Build magic packet: 6x 0xFF + 16x MAC
    magic = b"\xff" * 6 + mac_bytes * 16

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic, (broadcast, 9))
        sock.close()
        logger.info(f"WoL magic packet sent to {mac_address} via {broadcast}")
        return True
    except OSError as e:
        logger.error(f"Failed to send WoL packet: {e}")
        return False


async def wake_build_server() -> bool:
    """Wake the Mini PC build server via Wake-on-LAN."""
    logger.info(f"Waking build server (MAC: {settings.build_server_mac})")
    return send_magic_packet(settings.build_server_mac)


async def check_build_server_health() -> bool:
    """
    Check if the build server is reachable.

    TODO: Replace with actual SSH or HTTP health check when hardware is available.
    For now, this is a stub that always returns True (simulating local builds).
    """
    logger.info("Build server health check (stub: always returns True)")
    return True
