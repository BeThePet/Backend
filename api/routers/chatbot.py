from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.core.security import get_current_user
from api.db.models import User
from api.db.session import get_db
from api.schemas.chat import (
    ChatHistoryResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatRoom,
    ChatRoomCreate,
    ChatRoomResponse,
)
from api.services.chatbot.chatbot_service import ChatbotService

router = APIRouter()


@router.post("/rooms", response_model=ChatRoom)
async def create_chat_room(
    title: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """새 대화방 생성"""
    service = ChatbotService(db)
    chat_room_data = ChatRoomCreate(user_id=current_user.id, title=title)
    return service.create_chat_room(chat_room_data)


@router.get("/rooms", response_model=List[ChatRoomResponse])
async def get_chat_rooms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """대화방 목록 조회"""
    service = ChatbotService(db)
    return service.get_chat_rooms_with_last_message(current_user.id)


@router.get("/rooms/{room_id}/messages", response_model=ChatHistoryResponse)
async def get_chat_history(
    room_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """대화 히스토리 조회"""
    service = ChatbotService(db)
    chat_history = service.get_chat_history_with_dog_info(room_id, current_user.id)

    if not chat_history.messages:
        raise HTTPException(status_code=404, detail="Chat room not found")

    return chat_history


@router.post("/rooms/{room_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    room_id: UUID,
    message: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """메시지 전송 및 AI 응답 받기"""
    service = ChatbotService(db)

    # 사용자 메시지에 user_id 추가
    message_data = ChatMessageCreate(content=message.content, user_id=current_user.id)

    # 메시지 처리 및 AI 응답 생성
    response_message = await service.process_message(room_id, message_data)

    return ChatMessageResponse(
        id=response_message.id,
        content=response_message.content,
        role=response_message.role,
        created_at=response_message.created_at,
        updated_at=response_message.updated_at,
        deleted_at=response_message.deleted_at,
    )


@router.post("/rooms/{room_id}/messages/first")
async def send_first_message(
    room_id: UUID,
    message: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """첫 메시지 전송 및 대화방 제목 업데이트"""
    service = ChatbotService(db)

    # 사용자 메시지에 user_id 추가
    message_data = ChatMessageCreate(content=message.content, user_id=current_user.id)

    # 메시지 처리 및 AI 응답 생성
    response_message = await service.process_message(room_id, message_data)

    # 대화방 제목 업데이트
    title = message.content[:50]
    service.update_room_title(room_id, title)

    return {
        "message": ChatMessageResponse(
            id=response_message.id,
            content=response_message.content,
            role=response_message.role,
            created_at=response_message.created_at,
            updated_at=response_message.updated_at,
            deleted_at=response_message.deleted_at,
        ),
        "title": title,
    }


@router.delete("/rooms/{room_id}")
async def delete_chat_room(
    room_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """대화방 삭제"""
    service = ChatbotService(db)
    service.delete_chat_room(room_id)
    return {"message": "Chat room deleted successfully", "room_id": str(room_id)}


@router.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "service": "chatbot"}
