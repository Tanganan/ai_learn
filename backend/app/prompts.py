"""系统提示词：存在数据库里，用户可改，每次回答作为 system message 下发。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from .models import AppSetting, utc_now

PROMPT_KEY = "system_prompt"

DEFAULT_SYSTEM_PROMPT = """你是「考研助手」，只回答与研究生入学考试直接相关的问题：
择校与择专业、政治/英语/数学/专业课的复习方法与资料、复习计划与时间安排、
历年真题与模拟、报名/初试/复试/调剂流程、备考心态与作息安排。

回答规则（必须遵守）：
1. 先给结论，再给必要解释，控制在 3~6 句，不堆砌与问题无关的信息。
2. 超出考研范围的话题（天气、新闻、娱乐、编程、购物、医疗、情感闲聊、其他类别的考试等）一律不展开：先用一句话说明「我只能提供考研相关的帮助」，再给出 1~2 个具体的考研问题把用户拉回来，例如「你想先聊择校方向、复习规划，还是某一科的备考方法？」。
3. 不编造院校分数线、招生人数、报录比等具体数据；涉及具体数据时提醒以院校研招网和官方公告为准。
4. 不提供作弊、泄题、代考等违规建议，遇到这类请求直接拒绝并说明原因。
5. 使用简体中文，语气平和，不说教，不使用夸张的鼓励话术。"""


def get_system_prompt(db: Session) -> str:
    row = db.get(AppSetting, PROMPT_KEY)
    if row is None or not row.value.strip():
        return DEFAULT_SYSTEM_PROMPT
    return row.value


def save_system_prompt(db: Session, value: str) -> AppSetting:
    text = value.strip()
    row = db.get(AppSetting, PROMPT_KEY)
    if row is None:
        row = AppSetting(key=PROMPT_KEY, value=text, updated_at=utc_now())
        db.add(row)
    else:
        row.value = text
        row.updated_at = utc_now()
    db.commit()
    db.refresh(row)
    return row


def reset_system_prompt(db: Session) -> None:
    row = db.get(AppSetting, PROMPT_KEY)
    if row is not None:
        db.delete(row)
        db.commit()
