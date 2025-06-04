from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class ChatMessageBase(BaseModel):
    role: str
    content: str


class ChatMessageCreate(ChatMessageBase):
    pass


class ChatMessage(ChatMessageBase):
    id: UUID
    chat_room_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRoomBase(BaseModel):
    title: Optional[str] = None


class ChatRoomCreate(ChatRoomBase):
    user_id: UUID


class ChatRoom(ChatRoomBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessage] = []

    class Config:
        from_attributes = True


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


class NewSymptom(NewSymptomBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SymptomLogBase(BaseModel):
    symptom_name: str
    context: Optional[str] = None


class SymptomLogCreate(SymptomLogBase):
    chat_room_id: UUID


class SymptomLog(SymptomLogBase):
    id: UUID
    chat_room_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
