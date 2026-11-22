"""会话相关接口：列表、详情、新建、删除。"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import ChatSession, Message, utc_now
from ..schemas import SessionDetailOut, SessionOut

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionOut], summary="按时间倒序返回会话列表")
def list_sessions(db: Session = Depends(get_db)) -> list[SessionOut]:
    stmt = (
        select(ChatSession, func.count(Message.id).label("message_count"))
        .outerjoin(Message, Message.session_id == ChatSession.id)
        .group_by(ChatSession.id)
        .order_by(ChatSession.updated_at.desc())
    )
    rows = db.execute(stmt).all()
    return [
        SessionOut(
            id=session.id,
            title=session.title,
            message_count=count,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )
        for session, count in rows
    ]


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED, summary="新建空会话")
def create_session(db: Session = Depends(get_db)) -> SessionOut:
    now = utc_now()
    session = ChatSession(title="新会话", created_at=now, updated_at=now)
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionOut(
        id=session.id,
        title=session.title,
        message_count=0,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.get("/{session_id}", response_model=SessionDetailOut, summary="会话详情与全部消息")
def get_session(session_id: int, db: Session = Depends(get_db)) -> SessionDetailOut:
    session = db.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(ChatSession.id == session_id)
    ).scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return SessionDetailOut(
        id=session.id,
        title=session.title,
        message_count=len(session.messages),
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=session.messages,
    )


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除会话及其消息",
)
def delete_session(session_id: int, db: Session = Depends(get_db)) -> Response:
    session = db.get(ChatSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    db.delete(session)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
