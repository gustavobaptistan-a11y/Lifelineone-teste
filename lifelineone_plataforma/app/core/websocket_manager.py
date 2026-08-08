from typing import List, Dict, Any
from fastapi import WebSocket

class ConnectionManager:
    """
    Gerenciador de conexões WebSocket para atualização ao vivo do Painel Frontend.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message_data: Dict[str, Any]):
        """Notifica todos os clientes conectados ao vivo no painel."""
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message_data)
            except Exception:
                self.disconnect(connection)

ws_manager = ConnectionManager()
