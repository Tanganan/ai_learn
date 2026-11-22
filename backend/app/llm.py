"""模型调用层：只允许后端持有密钥，前端不接触模型服务。

同时提供非流式（generate_answer）与流式（stream_answer）两种调用方式。
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

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


def _check_settings() -> None:
    settings = get_settings()
    if not settings.mimo_api_key:
        raise ModelUnavailableError("后端未配置模型密钥（MIMO_API_KEY）")
    if not settings.mimo_base_url:
        raise ModelUnavailableError("后端未配置模型服务地址（MIMO_BASE_URL）")
    if not settings.mimo_model:
        raise ModelUnavailableError("后端未配置模型名称（MIMO_MODEL）")


def _endpoint() -> tuple[str, dict[str, str]]:
    settings = get_settings()
    url = f"{settings.mimo_base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.mimo_api_key}",
        "Content-Type": "application/json",
    }
    return url, headers


def _http_error(status_code: int) -> ModelUnavailableError:
    if status_code == 429:
        return ModelUnavailableError("模型服务请求过于频繁，已被限流")
    if status_code >= 500:
        return ModelUnavailableError(f"模型服务返回错误（{status_code}）")
    if status_code >= 400:
        return ModelUnavailableError(f"模型请求被拒绝（{status_code}），请检查模型配置")
    return ModelUnavailableError(f"模型服务异常（{status_code}）")


def _demo_answer(question: str) -> str:
    return (
        "（演示模式）这里是后端返回的固定回答。\n\n"
        f"你问的是：{question}\n\n"
        "把 backend/.env 里的 MOCK_LLM 改为 false，并配置 MIMO_API_KEY 后即可调用真实模型。"
    )


async def generate_answer(history: list[dict[str, str]], question: str) -> str:
    settings = get_settings()

    if settings.mock_llm:
        return _demo_answer(question)

    _check_settings()
    payload = {
        "model": settings.mimo_model,
        "messages": _build_messages(history, question),
        "temperature": 0.4,
        "stream": False,
    }
    url, headers = _endpoint()

    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
    except httpx.HTTPError as exc:
        raise ModelUnavailableError(f"无法连接模型服务：{exc}") from exc

    if response.status_code >= 400:
        raise _http_error(response.status_code)
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


async def stream_answer(
    history: list[dict[str, str]], question: str
) -> AsyncIterator[str]:
    """按片段产出回答文本；上游 SSE 解析失败时跳过该行，不中断整条流。"""
    settings = get_settings()

    if settings.mock_llm:
        text = _demo_answer(question)
        step = 4
        for index in range(0, len(text), step):
            yield text[index : index + step]
            await asyncio.sleep(0.02)
        return

    _check_settings()
    payload = {
        "model": settings.mimo_model,
        "messages": _build_messages(history, question),
        "temperature": 0.4,
        "stream": True,
    }
    url, headers = _endpoint()

    timeout = httpx.Timeout(settings.llm_timeout, connect=10.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                if response.status_code >= 400:
                    await response.aread()
                    raise _http_error(response.status_code)

                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    raw = line[5:].strip()
                    if not raw or raw == "[DONE]":
                        if raw == "[DONE]":
                            break
                        continue
                    try:
                        chunk = json.loads(raw)
                    except ValueError:
                        continue
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    piece = delta.get("content")
                    if piece:
                        yield piece
    except httpx.HTTPError as exc:
        raise ModelUnavailableError(f"无法连接模型服务：{exc}") from exc
