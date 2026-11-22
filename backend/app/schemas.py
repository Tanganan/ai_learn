"""接口出入参定义（Pydantic v2）。"""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Role = Literal["user", "assistant"]


def _to_utc(value: datetime | None) -> datetime | None:
    """SQLite 读回的时间不带时区，统一按 UTC 处理后再序列化。"""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    role: Role
    content: str
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def _ensure_timezone(cls, value: datetime) -> datetime:
        return _to_utc(value)  # type: ignore[return-value]


class SessionOut(BaseModel):
    id: int
    title: str
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def _ensure_timezone(cls, value: datetime) -> datetime:
        return _to_utc(value)  # type: ignore[return-value]


class SessionDetailOut(SessionOut):
    messages: list[MessageOut] = Field(default_factory=list)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000, description="用户问题")
    session_id: int | None = Field(default=None, description="为空则新建会话")

    @field_validator("question")
    @classmethod
    def _strip_question(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("问题不能为空")
        return stripped


class ChatResponse(BaseModel):
    session_id: int
    title: str
    answer: str
    message: MessageOut
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def _ensure_timezone(cls, value: datetime) -> datetime:
        return _to_utc(value)  # type: ignore[return-value]
