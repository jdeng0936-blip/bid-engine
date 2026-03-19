"""
AI 路由 API 测试 — Mock LLM（铁律：严禁测试中发真实 LLM API）

Mock 策略：
  patch AsyncOpenAI.chat.completions.create → 模拟非流式/流式响应
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


AI_URL = "/api/v1/ai/chat"


def _make_mock_response(content: str, tool_calls=None):
    """构造模拟的 OpenAI ChatCompletion 响应"""
    msg = MagicMock()
    msg.content = content
    msg.tool_calls = tool_calls
    msg.model_dump = MagicMock(return_value={
        "role": "assistant",
        "content": content,
        "tool_calls": None,
    })
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


async def _make_mock_stream(chunks: list[str]):
    """构造模拟的异步流式响应"""
    for text in chunks:
        delta = MagicMock()
        delta.content = text
        choice = MagicMock()
        choice.delta = delta
        chunk = MagicMock()
        chunk.choices = [choice]
        yield chunk


@pytest.mark.asyncio
@patch("app.services.ai_router.AsyncOpenAI")
async def test_ai_chat_non_stream(mock_openai_cls, async_client, auth_headers):
    """非流式对话 — Mock LLM 直接返回文本"""
    # 构造 Mock
    mock_instance = MagicMock()
    mock_create = AsyncMock(return_value=_make_mock_response(
        "IV 类围岩推荐采用锚杆间距 800×800mm。"
    ))
    mock_instance.chat.completions.create = mock_create
    mock_openai_cls.return_value = mock_instance

    resp = await async_client.post(AI_URL, json={
        "message": "IV类围岩推荐什么支护参数？",
        "stream": False,
    }, headers=auth_headers)

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "reply" in data
    assert "锚杆" in data["reply"]


@pytest.mark.asyncio
@patch("app.services.ai_router.AsyncOpenAI")
async def test_ai_chat_stream(mock_openai_cls, async_client, auth_headers):
    """流式对话 — Mock LLM 流式输出 SSE"""
    # 第一轮：无 tool_calls，直接流式输出
    first_call = _make_mock_response(None, tool_calls=None)
    # 类型标记让 chat_stream 进入无工具分支
    first_call.choices[0].message.content = None
    first_call.choices[0].message.tool_calls = None

    mock_instance = MagicMock()
    # create 要被调用两次：第一次非流式检测工具，第二次流式输出
    # 但无工具分支只调两次（第一次非流式 + 第二次流式）
    mock_create = AsyncMock(side_effect=[
        first_call,  # 第一轮非流式检测
        _make_mock_stream(["支护", "参数", "建议"])  # 第二轮流式
    ])
    mock_instance.chat.completions.create = mock_create
    mock_openai_cls.return_value = mock_instance

    resp = await async_client.post(AI_URL, json={
        "message": "帮我计算支护参数",
        "stream": True,
    }, headers=auth_headers)

    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("text/event-stream")


@pytest.mark.asyncio
async def test_ai_chat_missing_message(async_client, auth_headers):
    """缺少 message 字段 → 422"""
    resp = await async_client.post(AI_URL, json={
        "stream": False,
    }, headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_ai_chat_empty_message(async_client, auth_headers):
    """空 message → 422"""
    resp = await async_client.post(AI_URL, json={
        "message": "",
        "stream": False,
    }, headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_ai_chat_no_auth(async_client):
    """无认证 → 401"""
    resp = await async_client.post(AI_URL, json={
        "message": "测试",
        "stream": False,
    })
    assert resp.status_code == 401
