import json
from typing import Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy.orm import Session

from api.core.config import settings
from api.core.security import get_current_websocket_user

from ..database import get_db
from ..schemas.chat import ChatMessageCreate, ChatRoomCreate
from ..services.chatbot_service import ChatbotService
from .connection import manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    # API의 인증 시스템 사용
    try:
        user = await get_current_websocket_user(websocket, db)
        user_id = user.id
    except HTTPException:
        await websocket.close(code=4001, reason="Authentication failed")
        return

    await websocket.accept()
    service = ChatbotService(db)

    try:
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
            except json.JSONDecodeError:
                continue
            except WebSocketDisconnect:
                break

            message_type = message_data.get("type")
            payload = message_data.get("payload", {})

            if message_type == "create_room":
                # 새 대화방 생성
                chat_room = service.create_chat_room(
                    ChatRoomCreate(user_id=user_id, title="")
                )
                # 대화 상태 초기화
                service.chat_states[str(chat_room.id)] = {"state": "initial"}

                await websocket.send_json(
                    {
                        "type": "room_created",
                        "payload": {
                            "id": str(chat_room.id),
                            "title": chat_room.title,
                            "created_at": chat_room.created_at.isoformat(),
                            "updated_at": chat_room.updated_at.isoformat(),
                            "deleted_at": (
                                chat_room.deleted_at.isoformat()
                                if chat_room.deleted_at
                                else None
                            ),
                        },
                    }
                )

            elif message_type in ["send_first_message", "send_message"]:
                # 메시지 처리 (첫 메시지와 일반 메시지 동일하게 처리)
                chat_room_id = UUID(payload["room_id"])
                content = payload["content"]

                # 메시지 처리 및 응답 생성
                message = await service.process_message(
                    chat_room_id, ChatMessageCreate(user_id=user_id, content=content)
                )

                # 현재 대화 상태 확인
                current_state = service.chat_states.get(
                    str(chat_room_id), {"state": "initial"}
                )

                # 메시지 응답 포맷팅
                message_data = {
                    "id": str(message.id),
                    "content": message.content,
                    "role": message.role,
                    "created_at": (
                        message.created_at.isoformat() if message.created_at else None
                    ),
                    "updated_at": (
                        message.updated_at.isoformat() if message.updated_at else None
                    ),
                    "deleted_at": (
                        message.deleted_at.isoformat() if message.deleted_at else None
                    ),
                }

                # 첫 메시지인 경우 대화방 제목 업데이트
                if message_type == "send_first_message":
                    service.update_room_title(chat_room_id, content[:50])
                    await websocket.send_json(
                        {
                            "type": "message_response",
                            "payload": {
                                "message": message_data,
                                "title": content[:50],
                                "chat_state": current_state["state"],
                            },
                        }
                    )
                else:
                    await websocket.send_json(
                        {
                            "type": "message_response",
                            "payload": {
                                "message": message_data,
                                "chat_state": current_state["state"],
                            },
                        }
                    )

            elif message_type == "get_rooms":
                # 대화방 목록 조회
                chat_rooms = service.get_chat_rooms_with_last_message(user_id)
                rooms_data = [
                    {
                        "id": str(room.id),
                        "title": room.title,
                        "created_at": (
                            room.created_at.isoformat() if room.created_at else None
                        ),
                        "updated_at": (
                            room.updated_at.isoformat() if room.updated_at else None
                        ),
                        "deleted_at": (
                            room.deleted_at.isoformat() if room.deleted_at else None
                        ),
                        "last_message": room.last_message,
                    }
                    for room in chat_rooms
                ]
                await websocket.send_json({"type": "room_list", "payload": rooms_data})

            elif message_type == "get_history":
                # 대화 내역 조회
                chat_room_id = UUID(payload["room_id"])
                chat_history = service.get_chat_history_with_dog_info(
                    chat_room_id, user_id
                )

                if not chat_history.messages:
                    await websocket.send_json(
                        {"type": "error", "payload": {"message": "Chat room not found"}}
                    )
                    continue

                # 메시지 포맷팅
                messages_data = [
                    {
                        "id": str(msg.id),
                        "content": msg.content,
                        "role": msg.role,
                        "created_at": (
                            msg.created_at.isoformat() if msg.created_at else None
                        ),
                        "updated_at": (
                            msg.updated_at.isoformat() if msg.updated_at else None
                        ),
                        "deleted_at": (
                            msg.deleted_at.isoformat() if msg.deleted_at else None
                        ),
                    }
                    for msg in chat_history.messages
                ]

                await websocket.send_json(
                    {
                        "type": "chat_history",
                        "payload": {
                            "messages": messages_data,
                            "dog_info": chat_history.dog_info,
                        },
                    }
                )

            elif message_type == "delete_room":
                # 대화방 삭제 시 상태도 함께 삭제
                chat_room_id = UUID(payload["room_id"])
                if str(chat_room_id) in service.chat_states:
                    del service.chat_states[str(chat_room_id)]
                service.delete_chat_room(chat_room_id)
                await websocket.send_json(
                    {"type": "room_deleted", "payload": {"room_id": str(chat_room_id)}}
                )

            else:
                await websocket.send_json(
                    {"type": "error", "payload": {"message": "Unknown message type"}}
                )

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "payload": {"message": str(e)}})
