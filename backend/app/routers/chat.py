"""问答接口：普通请求与流式请求（SSE）两种形态。

流式接口约定的事件：
- meta   会话信息（session_id / title）
- delta  增量文本
- done   完整回答落库后的消息体
- error  模型不可用，detail 为可读文案
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import SessionLocal, get_db
from ..llm import ModelUnavailableError, generate_answer, stream_answer
from ..models import ChatSession, Message, utc_now
from ..schemas import ChatRequest, ChatResponse, MessageOut

router = APIRouter(tags=["chat"])
settings = get_settings()

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    # 关闭 Nginx 等中间层的响应缓冲，否则前端拿不到逐字效果
    "X-Accel-Buffering": "no",
}


def _make_title(question: str) -> str:
    single_line = " ".join(question.split())
    return single_line if len(single_line) <= 20 else f"{single_line[:20]}…"


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _load_history(db: Session, session_id: int) -> list[dict[str, str]]:
    stmt = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.id.desc())
        .limit(settings.llm_max_history)
    )
    rows = list(db.execute(stmt).scalars().all())
    return [{"role": item.role, "content": item.content} for item in reversed(rows)]


def _persist_turn(
    session_id: int,
    question: str,
    answer: str,
    title: str,
    touch_title: bool,
) -> dict:
    """一次问答的两条消息一起落库，返回 done 事件需要的载荷。"""
    with SessionLocal() as store:
        now = utc_now()
        user_message = Message(session_id=session_id, role="user", content=question, created_at=now)
        assistant_message = Message(
            session_id=session_id, role="assistant", content=answer, created_at=now
        )
        store.add_all([user_message, assistant_message])
        target = store.get(ChatSession, session_id)
        if target is not None:
            target.updated_at = now
            if touch_title:
                target.title = _make_title(question)
        store.commit()
        store.refresh(assistant_message)
        return {
            "session_id": session_id,
            "title": target.title if target is not None else title,
            "answer": answer,
            "message": MessageOut.model_validate(assistant_message).model_dump(mode="json"),
            "created_at": MessageOut.model_validate(assistant_message).created_at.isoformat(),
        }


def _drop_session(session_id: int) -> None:
    with SessionLocal() as store:
        target = store.get(ChatSession, session_id)
        if target is not None:
            store.delete(target)
            store.commit()


def _resolve_session(db: Session, payload: ChatRequest) -> tuple[ChatSession, bool]:
    if payload.session_id is not None:
        session = db.get(ChatSession, payload.session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="会话不存在，请刷新会话列表")
        return session, False

    now = utc_now()
    session = ChatSession(title=_make_title(payload.question), created_at=now, updated_at=now)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session, True


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="提交问题并获取回答",
    responses={503: {"description": "模型服务不可用"}},
)
async def chat(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    session, _created = _resolve_session(db, payload)
    history = _load_history(db, session.id)

    try:
        answer = await generate_answer(history, payload.question)
    except ModelUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    payload_out = _persist_turn(
        session_id=session.id,
        question=payload.question,
        answer=answer,
        title=session.title,
        touch_title=False,
    )
    return ChatResponse(**payload_out)


@router.post(
    "/chat/stream",
    summary="流式提交问题并获取回答（SSE）",
    responses={503: {"description": "模型服务不可用"}},
)
async def chat_stream(payload: ChatRequest, db: Session = Depends(get_db)) -> StreamingResponse:
    session, created_new = _resolve_session(db, payload)
    history = _load_history(db, session.id)
    session_id = session.id
    title = session.title

    async def event_stream() -> AsyncIterator[str]:
        chunks: list[str] = []
        persisted = False
        try:
            yield _sse("meta", {"session_id": session_id, "title": title})

            async for piece in stream_answer(history, payload.question):
                chunks.append(piece)
                yield _sse("delta", {"text": piece})

            answer = "".join(chunks).strip()
            if not answer:
                raise ModelUnavailableError("模型返回了空回答")

            done_payload = _persist_turn(
                session_id=session_id,
                question=payload.question,
                answer=answer,
                title=title,
                touch_title=created_new,
            )
            persisted = True
            yield _sse("done", done_payload)
        except ModelUnavailableError as exc:
            if created_new and not chunks:
                _drop_session(session_id)
            yield _sse("error", {"detail": str(exc)})
        except asyncio.CancelledError:
            # 前端点了「停止」或断开连接：没产出内容的新会话直接清掉，有内容的交给 finally 保存
            if created_new and not "".join(chunks).strip():
                _drop_session(session_id)
            raise
        finally:
            if not persisted:
                partial = "".join(chunks).strip()
                if partial:
                    _persist_turn(
                        session_id=session_id,
                        question=payload.question,
                        answer=partial,
                        title=title,
                        touch_title=created_new,
                    )

    return StreamingResponse(event_stream(), media_type="text/event-stream; charset=utf-8", headers=SSE_HEADERS)
