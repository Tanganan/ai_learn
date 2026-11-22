"""问答接口：一次请求完成「落会话 → 调模型 → 存消息」。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..llm import ModelUnavailableError, generate_answer
from ..models import ChatSession, Message, utc_now
from ..schemas import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])
settings = get_settings()


def _make_title(question: str) -> str:
    single_line = " ".join(question.split())
    return single_line if len(single_line) <= 20 else f"{single_line[:20]}…"


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="提交问题并获取回答",
    responses={503: {"description": "模型服务不可用"}},
)
async def chat(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    session: ChatSession | None = None
    if payload.session_id is not None:
        session = db.get(ChatSession, payload.session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="会话不存在，请刷新会话列表")

    created_new = session is None
    if session is None:
        now = utc_now()
        session = ChatSession(title=_make_title(payload.question), created_at=now, updated_at=now)
        db.add(session)
        db.flush()

    history_stmt = (
        select(Message)
        .where(Message.session_id == session.id)
        .order_by(Message.id.desc())
        .limit(settings.llm_max_history)
    )
    rows = list(db.execute(history_stmt).scalars().all())
    history = [{"role": item.role, "content": item.content} for item in reversed(rows)]

    try:
        answer = await generate_answer(history, payload.question)
    except ModelUnavailableError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    now = utc_now()
    user_message = Message(
        session_id=session.id, role="user", content=payload.question, created_at=now
    )
    assistant_message = Message(
        session_id=session.id, role="assistant", content=answer, created_at=now
    )
    db.add_all([user_message, assistant_message])
    session.updated_at = now
    if created_new:
        session.title = _make_title(payload.question)
    db.commit()
    db.refresh(assistant_message)

    return ChatResponse(
        session_id=session.id,
        title=session.title,
        answer=answer,
        message=assistant_message,
        created_at=assistant_message.created_at,
    )
