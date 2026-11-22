"""模型调用层：只允许后端持有密钥，前端不接触模型服务。"""

from __future__ import annotations

import httpx

from .config import get_settings

SYSTEM_PROMPT = (
    "你是 AI Learn 学习助手，回答要准确、简洁，先给结论再给必要的解释。"
    "不确定时明确说明不确定，不要编造事实。"
)


class ModelUnavailableError(Exception):
    """模型服务不可用（未配置密钥、网络异常、限流或上游报错）。"""


def _build_messages(history: list[dict[str, str]], question: str) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": question})
    return messages


async def generate_answer(history: list[dict[str, str]], question: str) -> str:
    settings = get_settings()

    if settings.mock_llm:
        return (
            "（演示模式）这里是后端返回的固定回答。\n\n"
            f"你问的是：{question}\n\n"
            "把 backend/.env 里的 MOCK_LLM 改为 false，并配置 MIMO_API_KEY 后即可调用真实模型。"
        )

    if not settings.mimo_api_key:
        raise ModelUnavailableError("后端未配置模型密钥（MIMO_API_KEY）")
    if not settings.mimo_base_url:
        raise ModelUnavailableError("后端未配置模型服务地址（MIMO_BASE_URL）")
    if not settings.mimo_model:
        raise ModelUnavailableError("后端未配置模型名称（MIMO_MODEL）")

    payload = {
        "model": settings.mimo_model,
        "messages": _build_messages(history, question),
        "temperature": 0.4,
        "stream": False,
    }

    url = f"{settings.mimo_base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.mimo_api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
    except httpx.HTTPError as exc:
        raise ModelUnavailableError(f"无法连接模型服务：{exc}") from exc

    if response.status_code == 429:
        raise ModelUnavailableError("模型服务请求过于频繁，已被限流")
    if response.status_code >= 500:
        raise ModelUnavailableError(f"模型服务返回错误（{response.status_code}）")
    if response.status_code >= 400:
        raise ModelUnavailableError(f"模型请求被拒绝（{response.status_code}），请检查模型配置")
    if not response.content:
        raise ModelUnavailableError("模型服务返回空响应")

    try:
        data = response.json()
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ModelUnavailableError("模型返回格式异常") from exc

    answer = (content or "").strip()
    if not answer:
        raise ModelUnavailableError("模型返回了空回答")
    return answer
