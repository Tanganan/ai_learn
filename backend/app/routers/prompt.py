"""系统提示词的读写接口。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AppSetting
from ..prompts import (
    DEFAULT_SYSTEM_PROMPT,
    PROMPT_KEY,
    get_system_prompt,
    reset_system_prompt,
    save_system_prompt,
)
from ..schemas import PromptOut, PromptUpdate

router = APIRouter(tags=["prompt"])


def _payload(db: Session) -> PromptOut:
    row = db.get(AppSetting, PROMPT_KEY)
    custom = row is not None and bool(row.value.strip())
    return PromptOut(
        prompt=get_system_prompt(db),
        default_prompt=DEFAULT_SYSTEM_PROMPT,
        is_default=not custom,
        updated_at=row.updated_at if custom else None,
    )


@router.get("/prompt", response_model=PromptOut, summary="读取当前系统提示词")
def read_prompt(db: Session = Depends(get_db)) -> PromptOut:
    return _payload(db)


@router.put("/prompt", response_model=PromptOut, summary="保存系统提示词")
def update_prompt(payload: PromptUpdate, db: Session = Depends(get_db)) -> PromptOut:
    save_system_prompt(db, payload.prompt)
    return _payload(db)


@router.post("/prompt/reset", response_model=PromptOut, summary="恢复默认提示词")
def reset_prompt(db: Session = Depends(get_db)) -> PromptOut:
    reset_system_prompt(db)
    return _payload(db)
