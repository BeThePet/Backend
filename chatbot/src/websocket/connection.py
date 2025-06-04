import json
from typing import Dict, List
from uuid import UUID

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # {chat_room_id: {user_id: WebSocket}}
        self.active_connections: Dict[UUID, Dict[UUID, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, chat_room_id: UUID, user_id: UUID):
        await websocket.accept()
        if chat_room_id not in self.active_connections:
            self.active_connections[chat_room_id] = {}
        self.active_connections[chat_room_id][user_id] = websocket

    def disconnect(self, chat_room_id: UUID, user_id: UUID):
        if chat_room_id in self.active_connections:
            if user_id in self.active_connections[chat_room_id]:
                del self.active_connections[chat_room_id][user_id]
            if not self.active_connections[chat_room_id]:
                del self.active_connections[chat_room_id]

    async def send_message(
        self, message: str, chat_room_id: UUID, user_id: UUID = None
    ):
        if chat_room_id in self.active_connections:
            if user_id:
                # 특정 사용자에게만 메시지 전송
                if user_id in self.active_connections[chat_room_id]:
                    await self.active_connections[chat_room_id][user_id].send_text(
                        message
                    )
            else:
                # 채팅방의 모든 사용자에게 메시지 전송
                for connection in self.active_connections[chat_room_id].values():
                    await connection.send_text(message)

    async def broadcast(self, message: str):
        # 모든 연결된 클라이언트에게 메시지 전송
        for room in self.active_connections.values():
            for connection in room.values():
                await connection.send_text(message)


manager = ConnectionManager()
