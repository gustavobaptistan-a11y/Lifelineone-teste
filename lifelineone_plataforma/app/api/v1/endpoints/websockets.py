from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.websocket_manager import ws_manager

router = APIRouter()

@router.websocket("/dashboard")
async def websocket_dashboard_endpoint(websocket: WebSocket):
    """
    Canal WebSocket para transmissão de atualizações do painel em tempo real.
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            # Mantém a conexão ativa ouvindo pings/mensagens do cliente
            data = await websocket.receive_text()
            await websocket.send_json({"type": "pong", "received": data})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
