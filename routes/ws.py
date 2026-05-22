"""WebSocket routes — v1.0.0 locked template.

Provides:
  - ws_status: GET /ws/status — server health check endpoint
  - websocket_endpoint: WS /ws — real-time WebSocket handler
  - ws_router / router: APIRouter exported for main.py include_router()

Locked because AI consistently generates:
  - `global _handler_instance: WebSocketManager` — SyntaxError in Python
  - phantom imports (handle_message, WebSocketConnection, close_connection)
  - async def ws_status with no await → blocks event loop
"""
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

ws_router = APIRouter()
router = ws_router  # alias for compatibility


@ws_router.get("/ws/status")
def ws_status():
    """Return WebSocket server status."""
    return {"status": "ok", "websocket": "available"}


@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Accept and handle a WebSocket connection with echo loop."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        logger.info("[WebSocket] Client disconnected")
    except Exception as _ws_err:
        logger.error("[WebSocket] Error: %s", _ws_err)
