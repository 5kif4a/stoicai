from datetime import datetime, timezone
from enum import Enum

from beanie import Document, init_beanie, Indexed
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import Field

from app.config import settings

__all__ = ("init_db", "Chat", "Message", "Role")


def utcnow():
    return datetime.now(timezone.utc)


class Role(str, Enum):
    USER = "user"
    SYSTEM = "system"


class Message(Document):
    chat_id: int = Indexed()
    sender: Role
    content: str
    timestamp: datetime = Indexed()
    metadata: dict | None = None

    class Settings:
        name = "messages"


class Chat(Document):
    id: int = Indexed()
    timestamp: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "chats"


async def init_db():
    client = AsyncIOMotorClient(settings.db_url)
    await init_beanie(database=client.get_database(), document_models=[Chat])
