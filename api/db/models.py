from sqlalchemy import Column, Integer, String
from .base import Base 
from core.base import TimeStampMixin 


class User(Base, TimeStampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    nickname = Column(String(50), unique=True, nullable=False)