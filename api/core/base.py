from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import declared_attr

class TimeStampMixin:
    @declared_attr
    def created_at(cls):
        return Column(DateTime(timezone=True), server_default=func.now())

    @declared_attr
    def updated_at(cls):
        return Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    @declared_attr
    def deleted_at(cls):
        return Column(DateTime(timezone=True), nullable=True)