"""
websocket/manager.py - Deterministic locked template v1.0.0
JARVIS Locked File Library — DO NOT MODIFY WITHOUT UPDATING VERSION

Provides the WebSocketManager class and get_manager() singleton factory.

REQUIRED METHOD SIGNATURES (per plan_quality.py websocket rules):
  connect(self, ws: WebSocket) -> None          SYNC — appends to active_connections only
  disconnect(self, ws: WebSocket) -> None        SYNC — removes from active_connections only
  broadcast(self, message: str) -> None         ASYNC — sends to all connections
  handle_message(self, ws: WebSocket, data: str) -> None  ASYNC — processes incoming data

CRITICAL RULES ENFORCED:
  - connect() and disconnect() MUST BE SYNC (not async) — the AI makes them async,
    causing coroutine-never-awaited errors. These methods only mutate a list.
  - broadcast() MUST use `await connection.send_text()` — NOT asyncio.ensure_future().
    ensure_future fires and forgets; broken connections silently accumulate.
  - handle_message() is async because it calls await broadcast().
  - get_manager() returns the singleton directly — NEVER .instance or ._instance.
  - NEVER call get_manager() at module level — only inside route/handler function bodies.

CHANGE LOG:
  v1.0.0 - Initial locked template. Addresses ARCH DEBT #4: MPB hardcoded WebSocketManager
           class string. Template now lives in template library — keeps MPB clean.
"""
import logging
from typing import List

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages active WebSocket connections.

    Thread-safe list of active connections. connect/disconnect are sync (list ops only).
    broadcast and handle_message are async (they send over the wire).
    """

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    # ------------------------------------------------------------------
    # connect — SYNC (list append only, no I/O)
    # ------------------------------------------------------------------
    def connect(self, ws: WebSocket) -> None:
        """
        Register a WebSocket connection. Appends ws to active_connections.
        SYNC — no I/O, no await. Does not call ws.accept() — caller's responsibility.
        """
        self.active_connections.append(ws)
        logger.debug(
            f"[WS] connect: {len(self.active_connections)} active connection(s)"
        )

    # ------------------------------------------------------------------
    # disconnect — SYNC (list remove only, no I/O)
    # ------------------------------------------------------------------
    def disconnect(self, ws: WebSocket) -> None:
        """
        Deregister a WebSocket connection. Removes ws from active_connections.
        SYNC — no I/O, no await. Safe to call even if ws is not in the list.
        """
        try:
            self.active_connections.remove(ws)
        except ValueError:
            pass  # already removed or never connected — not an error
        logger.debug(
            f"[WS] disconnect: {len(self.active_connections)} active connection(s)"
        )

    # ------------------------------------------------------------------
    # broadcast — ASYNC (sends over the wire)
    # ------------------------------------------------------------------
    async def broadcast(self, message: str) -> None:
        """
        Send a text message to every active WebSocket connection. Async — uses
        await connection.send_text(). Dead connections are removed on send failure.
        """
        dead: List[WebSocket] = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception as exc:
                logger.warning(f"[WS] broadcast: send failed, removing connection: {exc}")
                dead.append(connection)
        for d in dead:
            self.disconnect(d)

    # ------------------------------------------------------------------
    # handle_message — ASYNC (calls broadcast)
    # ------------------------------------------------------------------
    async def handle_message(self, ws: WebSocket, data: str) -> None:
        """
        Process an incoming message from a WebSocket client. Async because it
        calls await broadcast(). Default behaviour: echo to all connected clients.
        Override or extend per gig requirements.
        """
        try:
            logger.debug(f"[WS] handle_message: {data[:100]!r}")
            await self.broadcast(data)
        except Exception as exc:
            logger.error(f"[WS] handle_message error: {exc}")


# ---------------------------------------------------------------------------
# Singleton factory — call INSIDE route/handler functions only, never at module level
# ---------------------------------------------------------------------------
_manager: WebSocketManager = WebSocketManager()


def get_manager() -> WebSocketManager:
    """
    Return the application-level WebSocketManager singleton.
    MUST be called inside a route handler function body — never at module level.
    WRONG: manager = get_manager()  # at module level — possibly unbound at import time
    RIGHT: async def ws_endpoint(ws: WebSocket): manager = get_manager(); ...
    """
    return _manager


# Aliases for builds that import different names
WSManager = WebSocketManager
ConnectionManager = WebSocketManager
