from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class TimeStampSchema(BaseModel):
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class ChatMessage(TimeStampSchema):
    id: UUID
    chat_room_id: UUID
    user_id: int
    content: str
    role: str  # "user" or "assistant"

    class Config:
        from_attributes = True


class ChatRoom(TimeStampSchema):
    id: UUID
    user_id: int
    title: str

    class Config:
        from_attributes = True


class ChatRoomCreate(BaseModel):
    user_id: int
    title: str


class ChatRoomResponse(TimeStampSchema):
    id: UUID
    title: str
    last_message: Optional[str] = None


class ChatMessageCreate(BaseModel):
    content: str
    user_id: int


class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessage]
    dog_info: Optional[dict] = None  # 반려견 정보


class NewSymptomBase(BaseModel):
    symptom_name: str
    normalized_name: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[int] = None
    description: Optional[str] = None
    related_symptoms: List[str] = []
    possible_causes: List[str] = []


class NewSymptomCreate(NewSymptomBase):
    pass


class NewSymptom(NewSymptomBase, TimeStampSchema):
    id: UUID

    class Config:
        from_attributes = True


class SymptomLogBase(BaseModel):
    symptom_name: str
    context: Optional[str] = None


class SymptomLogCreate(SymptomLogBase):
    chat_room_id: UUID
    user_id: int


class SymptomLog(SymptomLogBase, TimeStampSchema):
    id: UUID
    chat_room_id: UUID
    user_id: int

    class Config:
        from_attributes = True
