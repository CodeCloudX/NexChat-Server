from typing import Dict, List
from fastapi import WebSocket
from app.infrastructure.database import async_session_maker


class ConnectionManager:
    def __init__(self):
        # active_connections: { user_id: [WebSocket, ...] }
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
            
            # If this is the FIRST connection for this user, mark them as ONLINE
            from app.services import presence_service
            await presence_service.set_user_online(user_id)
            
        self.active_connections[user_id].append(websocket)

    async def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            
            if not self.active_connections[user_id]:
                # If this was the LAST connection, mark them as OFFLINE
                del self.active_connections[user_id]
                
                from app.services import presence_service
                # We need a DB session to update 'last_seen' in the database
                async with async_session_maker() as db:
                    await presence_service.set_user_offline(db, user_id)

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass

    async def broadcast(self, message: dict, user_ids: List[str]):
        for user_id in user_ids:
            await self.send_personal_message(message, user_id)


manager = ConnectionManager()
