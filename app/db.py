from datetime import datetime, timezone
from enum import Enum

from beanie import Document, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

from app.config import settings

__all__ = ("init_db", "Chat", "Message", "Role")


def utcnow():
    return datetime.now(timezone.utc)


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    id: int
    sender: Role
    content: str
    timestamp: datetime
    metadata: dict | None = None


class Chat(Document):
    id: int
    messages: list[Message] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "chats"


async def init_db():
    client = AsyncIOMotorClient(settings.db_url)
    await init_beanie(database=client.get_database(), document_models=[Chat])
