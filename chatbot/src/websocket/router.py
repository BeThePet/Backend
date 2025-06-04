from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from api.db.models import ChatMessage, ChatRoom  # API 모델 import

from ..database import get_db
from ..services.chatbot_service import vetgpt_chatbot
from .connection import manager

router = APIRouter()


@router.websocket("/ws/{chat_room_id}/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    chat_room_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
):
    await manager.connect(websocket, chat_room_id, user_id)
    try:
        while True:
            data = await websocket.receive_text()

            # 채팅방 존재 여부 확인
            chat_room = (
                db.query(ChatRoom)
                .filter(ChatRoom.id == chat_room_id, ChatRoom.user_id == user_id)
                .first()
            )

            if not chat_room:
                await manager.send_message(
                    "Error: Chat room not found", chat_room_id, user_id
                )
                continue

            # 사용자 메시지 저장
            user_message = ChatMessage(
                chat_room_id=chat_room_id, role="user", content=data
            )
            db.add(user_message)
            db.commit()

            # 이전 대화 내용 가져오기
            previous_messages = (
                db.query(ChatMessage)
                .filter(ChatMessage.chat_room_id == chat_room_id)
                .order_by(ChatMessage.created_at)
                .all()
            )

            # 챗봇 응답 생성
            response = vetgpt_chatbot(
                data, previous_messages=previous_messages, interactive_mode=False
            )

            # 챗봇 응답 저장
            bot_message = ChatMessage(
                chat_room_id=chat_room_id, role="assistant", content=response
            )
            db.add(bot_message)
            db.commit()

            # 응답 전송
            await manager.send_message(response, chat_room_id, user_id)

    except WebSocketDisconnect:
        manager.disconnect(chat_room_id, user_id)
    except Exception as e:
        error_message = f"Error: {str(e)}"
        await manager.send_message(error_message, chat_room_id, user_id)
        manager.disconnect(chat_room_id, user_id)
