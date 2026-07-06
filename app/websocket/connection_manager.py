from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, survey_id: int):
        await websocket.accept()
        if survey_id not in self.active_connections:
            self.active_connections[survey_id] = []
        self.active_connections[survey_id].append(websocket)

    def disconnect(self, websocket: WebSocket, survey_id: int):
        if survey_id in self.active_connections:
            self.active_connections[survey_id].remove(websocket)
            if not self.active_connections[survey_id]:
                del self.active_connections[survey_id]

    async def broadcast(self, survey_id: int, message: dict):
        if survey_id not in self.active_connections:
            return
        connections = self.active_connections[survey_id].copy()
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection, survey_id)


manager = ConnectionManager()