"""
AI 对话历史管理 + 带持久化的多轮对话 API

功能说明：
  1. 会话管理 — 创建/列出/删除/归档会话
  2. 消息查询 — 获取指定会话的全部消息历史
  3. 带持久化的多轮对话 — 自动保存每轮 user/assistant 消息到数据库
  4. SSE 流式输出仍然通过原有 AIRouter 实现

所有接口强制 JWT 鉴权 + tenant_id 隔离。
"""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, and_, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.deps import get_current_user_payload
from app.schemas.common import ApiResponse
from app.schemas.chat import (
    ChatSessionItem,
    ChatSessionCreate,
    ChatMessageItem,
    ChatWithSessionRequest,
)
from app.schemas.ai import ChatResponse
from app.models.chat import ChatSession, ChatMessageRecord
from app.services.ai_router import AIRouter

router = APIRouter(prefix="/chat", tags=["AI 对话历史"])


# ===================== 会话管理 =====================

@router.get("/sessions", response_model=ApiResponse[list[ChatSessionItem]])
async def list_sessions(
    project_id: Optional[int] = Query(None, description="按项目筛选"),
    archived: bool = Query(False, description="是否查看归档会话"),
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """获取当前用户的对话会话列表"""
    tenant_id = int(payload.get("tenant_id", 0))
    user_id = int(payload.get("user_id", 0))

    query = (
        select(ChatSession)
        .where(
            and_(
                ChatSession.tenant_id == tenant_id,
                ChatSession.user_id == user_id,
                ChatSession.is_archived == (1 if archived else 0),
            )
        )
        .order_by(ChatSession.updated_at.desc())
    )
    if project_id:
        query = query.where(ChatSession.project_id == project_id)

    result = await session.execute(query)
    sessions = result.scalars().all()

    items = []
    for s in sessions:
        # 消息计数
        count_q = select(func.count()).where(ChatMessageRecord.session_id == s.id)
        count_result = await session.execute(count_q)
        msg_count = count_result.scalar() or 0

        items.append(ChatSessionItem(
            id=s.id,
            title=s.title,
            project_id=s.project_id,
            industry_type=s.industry_type,
            is_archived=bool(s.is_archived),
            created_at=s.created_at,
            updated_at=s.updated_at,
            message_count=msg_count,
        ))

    return ApiResponse(data=items)


@router.post("/sessions", response_model=ApiResponse[ChatSessionItem])
async def create_session(
    body: ChatSessionCreate,
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """创建新对话会话"""
    tenant_id = int(payload.get("tenant_id", 0))
    user_id = int(payload.get("user_id", 0))

    db_session = ChatSession(
        user_id=user_id,
        title=body.title or "新对话",
        project_id=body.project_id,
        industry_type=body.industry_type,
        tenant_id=tenant_id,
        created_by=user_id,
    )
    session.add(db_session)
    await session.commit()
    await session.refresh(db_session)

    return ApiResponse(data=ChatSessionItem(
        id=db_session.id,
        title=db_session.title,
        project_id=db_session.project_id,
        industry_type=db_session.industry_type,
        created_at=db_session.created_at,
        updated_at=db_session.updated_at,
        message_count=0,
    ))


@router.delete("/sessions/{session_id}", response_model=ApiResponse)
async def delete_session(
    session_id: int,
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """删除对话会话及其所有消息"""
    tenant_id = int(payload.get("tenant_id", 0))
    user_id = int(payload.get("user_id", 0))

    # 验证归属
    result = await session.execute(
        select(ChatSession).where(
            and_(
                ChatSession.id == session_id,
                ChatSession.tenant_id == tenant_id,
                ChatSession.user_id == user_id,
            )
        )
    )
    db_sess = result.scalar_one_or_none()
    if not db_sess:
        raise HTTPException(404, "会话不存在或无权访问")

    await session.delete(db_sess)
    await session.commit()
    return ApiResponse(data={"deleted": True})


@router.patch("/sessions/{session_id}/archive", response_model=ApiResponse)
async def archive_session(
    session_id: int,
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """归档/取消归档对话会话"""
    tenant_id = int(payload.get("tenant_id", 0))
    user_id = int(payload.get("user_id", 0))

    result = await session.execute(
        select(ChatSession).where(
            and_(
                ChatSession.id == session_id,
                ChatSession.tenant_id == tenant_id,
                ChatSession.user_id == user_id,
            )
        )
    )
    db_sess = result.scalar_one_or_none()
    if not db_sess:
        raise HTTPException(404, "会话不存在或无权访问")

    # 切换归档状态
    db_sess.is_archived = 0 if db_sess.is_archived else 1
    await session.commit()
    return ApiResponse(data={"archived": bool(db_sess.is_archived)})


# ===================== 消息查询 =====================

@router.get("/sessions/{session_id}/messages", response_model=ApiResponse[list[ChatMessageItem]])
async def get_session_messages(
    session_id: int,
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """获取指定会话的全部消息历史"""
    tenant_id = int(payload.get("tenant_id", 0))
    user_id = int(payload.get("user_id", 0))

    # 验证会话归属
    sess_result = await session.execute(
        select(ChatSession).where(
            and_(
                ChatSession.id == session_id,
                ChatSession.tenant_id == tenant_id,
                ChatSession.user_id == user_id,
            )
        )
    )
    if not sess_result.scalar_one_or_none():
        raise HTTPException(404, "会话不存在或无权访问")

    # 按时序获取消息
    result = await session.execute(
        select(ChatMessageRecord)
        .where(ChatMessageRecord.session_id == session_id)
        .order_by(ChatMessageRecord.created_at.asc())
    )
    messages = result.scalars().all()
    return ApiResponse(data=[ChatMessageItem.model_validate(m) for m in messages])


# ===================== 带持久化的多轮对话 =====================

@router.post("/send")
async def chat_with_history(
    body: ChatWithSessionRequest,
    payload: dict = Depends(get_current_user_payload),
    session: AsyncSession = Depends(get_async_session),
):
    """
    带持久化的多轮对话

    流程：
      1. 获取或创建会话
      2. 从数据库加载历史消息
      3. 保存用户消息到数据库
      4. 调用 AIRouter 生成回复（流式/非流式）
      5. 保存 assistant 回复到数据库
    """
    tenant_id = int(payload.get("tenant_id", 0))
    user_id = int(payload.get("user_id", 0))

    # --- 1. 获取或创建会话 ---
    chat_session = None
    if body.session_id:
        result = await session.execute(
            select(ChatSession).where(
                and_(
                    ChatSession.id == body.session_id,
                    ChatSession.tenant_id == tenant_id,
                    ChatSession.user_id == user_id,
                )
            )
        )
        chat_session = result.scalar_one_or_none()
        if not chat_session:
            raise HTTPException(404, "会话不存在或无权访问")

    if not chat_session:
        # 自动创建新会话，标题取用户消息前50字
        chat_session = ChatSession(
            user_id=user_id,
            title=body.message[:50],
            project_id=body.project_id,
            industry_type=body.industry_type,
            tenant_id=tenant_id,
            created_by=user_id,
        )
        session.add(chat_session)
        await session.flush()  # 获取 ID

    # --- 2. 从数据库加载历史消息 ---
    history_result = await session.execute(
        select(ChatMessageRecord)
        .where(ChatMessageRecord.session_id == chat_session.id)
        .order_by(ChatMessageRecord.created_at.asc())
    )
    history_records = history_result.scalars().all()

    # 构建 AIRouter 需要的 history 格式
    history = []
    for msg in history_records:
        history_item = {"role": msg.role, "content": msg.content}
        if msg.tool_call_id:
            history_item["tool_call_id"] = msg.tool_call_id
        if msg.tool_name:
            history_item["name"] = msg.tool_name
        history.append(history_item)

    # --- 3. 保存用户消息到数据库 ---
    user_msg = ChatMessageRecord(
        session_id=chat_session.id,
        role="user",
        content=body.message,
        tenant_id=tenant_id,
        created_by=user_id,
    )
    session.add(user_msg)
    await session.commit()

    # --- 4. 调用 AIRouter ---
    ai = AIRouter(
        session=session, tenant_id=tenant_id,
        industry_type=body.industry_type or chat_session.industry_type,
    )

    if body.stream:
        # SSE 流式输出 — 回复在流结束后通过回调保存
        async def _stream_with_save():
            full_reply = ""
            async for chunk in ai.chat_stream(body.message, history):
                yield chunk
                # 从 SSE 数据中提取文本内容
                if chunk.startswith("data: ") and chunk.strip() != "data: [DONE]":
                    try:
                        data = json.loads(chunk[6:])
                        if data.get("type") == "text":
                            full_reply += data.get("content", "")
                    except (json.JSONDecodeError, TypeError):
                        pass

            # 流结束后保存 assistant 回复
            if full_reply:
                assistant_msg = ChatMessageRecord(
                    session_id=chat_session.id,
                    role="assistant",
                    content=full_reply,
                    tenant_id=tenant_id,
                    created_by=0,
                )
                session.add(assistant_msg)
                await session.commit()

        return StreamingResponse(
            _stream_with_save(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "X-Session-Id": str(chat_session.id),
            },
        )
    else:
        # 非流式
        reply = await ai.chat(body.message, history)

        # 保存 assistant 回复
        assistant_msg = ChatMessageRecord(
            session_id=chat_session.id,
            role="assistant",
            content=reply,
            tenant_id=tenant_id,
            created_by=0,
        )
        session.add(assistant_msg)
        await session.commit()

        return ApiResponse(data={
            "session_id": chat_session.id,
            "reply": reply,
        })
