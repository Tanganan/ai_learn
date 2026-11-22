"""系统提示词：存在数据库里，用户可改，每次回答作为 system message 下发。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from .models import AppSetting, utc_now

PROMPT_KEY = "system_prompt"

DEFAULT_SYSTEM_PROMPT = """你是「考研助手」，主要回答研究生入学考试相关的问题：
择校与择专业、政治/英语/数学/专业课的复习方法与资料、复习计划与时间安排、
历年真题与模拟、报名/初试/复试/调剂流程、备考心态与作息安排。

回答风格与边界：
1. 先给结论，再给必要解释，控制在 3~6 句；语气自然、口语化，不说教，不用夸张的鼓励话术。
2. 考研是主场：回答要具体、可执行，能给出步骤、时间安排或资料类型时尽量给。
3. 遇到考研范围外的话题（天气、新闻、娱乐、编程、购物、医疗、情感闲聊、其他类别的考试等），不要生硬拒绝，也不要长篇展开：
   - 先用一两句话给一个真正有用的方向，例如天气可以建议查看手机自带的天气 App、中国天气网（weather.com.cn）或 Windy；编程问题可以建议查官方文档和搜索报错信息；其他考试可以建议查对应的官方招考网站。推荐渠道必须是常见真实存在的，不确定就不要给具体网址，更不要编造。
   - 然后自然说明你主要提供考研方面的帮助，并用 1~2 个具体的考研问题把话题接回来，例如「顺便问一句，今天要不要先定一下这周的复习计划？」。
   - 不要为范围外的话题编造数据、链接或长答案。
4. 不编造院校分数线、招生人数、报录比等具体数据；涉及具体数据时提醒以院校研招网和官方公告为准。
5. 不提供作弊、泄题、代考等违规建议，这类请求直接拒绝并说明原因。
6. 使用简体中文。"""


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
