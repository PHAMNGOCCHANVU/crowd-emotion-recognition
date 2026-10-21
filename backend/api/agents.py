import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend import models

from ..database import get_db
from ..schemas import (
    AgentChatRequest,
    AgentChatResponse,
    AgentConversationResponse,
    AgentMessageItem,
)
from ..services.chatbot_service import ChatbotService

router = APIRouter(prefix="/api/agents", tags=["agents"])

_chatbot_service = ChatbotService()


@router.post("/chat", response_model=AgentChatResponse)
async def chat_with_agent(
    req: AgentChatRequest,
    user_id: str | None = Query("user_123"),
    db: Session = Depends(get_db),
):
    """
    Gửi câu hỏi tới AI Advisor để nhận lời khuyên dựa trên dữ liệu phỏng vấn của user.
    Hỗ trợ LLM Function Calling với cả dữ liệu toàn cục (hành trình ứng viên) và cục bộ (phiên phỏng vấn cụ thể).
    """
    # 1. Quản lý Conversation trong DB
    conv_id = req.conversation_id
    history_list = []

    if not conv_id:
        conv = models.AgentConversation(
            id=f"conv_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            title=req.message[:50] if req.message else "Cuộc trò chuyện mới",
        )
        db.add(conv)
        conv_id = conv.id
    else:
        conv = db.query(models.AgentConversation).filter_by(id=conv_id).first()
        if not conv:
            conv = models.AgentConversation(
                id=conv_id,
                user_id=user_id,
                title=req.message[:50] if req.message else "Cuộc trò chuyện mới",
            )
            db.add(conv)
        else:
            # Lấy 6 tin nhắn gần nhất làm lịch sử ngữ cảnh
            past_messages = (
                db.query(models.AgentMessage)
                .filter_by(conversation_id=conv_id)
                .order_by(models.AgentMessage.created_at.asc())
                .all()
            )
            history_list = [{"role": m.role, "content": m.content} for m in past_messages[-6:]]

    # Nếu request gửi kèm history dạng object thì bổ sung thêm
    if req.history:
        for h in req.history:
            history_list.append({"role": h.role, "content": h.content})

    # 2. Gọi Chatbot Service Unified Advisor
    reply_text, suggestions, tools_used = await _chatbot_service.chat_advisor(
        user_message=req.message,
        db=db,
        user_id=user_id or "user_123",
        session_id=req.session_id,
        conversation_history=history_list,
    )

    # 3. Lưu tin nhắn user và agent vào DB
    msg_user = models.AgentMessage(
        id=f"msg_{uuid.uuid4().hex[:12]}",
        conversation_id=conv_id,
        role="user",
        content=req.message,
    )
    msg_agent = models.AgentMessage(
        id=f"msg_{uuid.uuid4().hex[:12]}",
        conversation_id=conv_id,
        role="agent",
        content=reply_text,
    )
    db.add(msg_user)
    db.add(msg_agent)
    db.commit()

    return AgentChatResponse(
        reply=reply_text,
        suggestions=suggestions,
        conversation_id=conv_id,
        tools_used=tools_used,
    )


@router.get("/conversations", response_model=list[AgentConversationResponse])
def list_conversations(
    user_id: str | None = Query("user_123"),
    db: Session = Depends(get_db),
):
    """
    Lấy danh sách các cuộc hội thoại cố vấn AI của user.
    """
    convs = (
        db.query(models.AgentConversation)
        .filter(models.AgentConversation.user_id == user_id)
        .order_by(models.AgentConversation.updated_at.desc())
        .all()
    )

    results = []
    for c in convs:
        msgs = (
            db.query(models.AgentMessage)
            .filter(models.AgentMessage.conversation_id == c.id)
            .order_by(models.AgentMessage.created_at.asc())
            .all()
        )
        results.append(
            AgentConversationResponse(
                id=c.id,
                title=c.title or "Cuộc trò chuyện",
                created_at=c.created_at,
                updated_at=c.updated_at,
                messages=[AgentMessageItem(role=m.role, content=m.content) for m in msgs],
            )
        )
    return results


@router.put("/conversations/{conv_id}")
def save_conversation(
    conv_id: str,
    payload: dict,
    user_id: str | None = Query("user_123"),
    db: Session = Depends(get_db),
):
    """
    Lưu hoặc đồng bộ toàn bộ cuộc hội thoại từ Frontend.
    """
    conv = db.query(models.AgentConversation).filter_by(id=conv_id).first()
    title = payload.get("title") or "Cuộc trò chuyện"
    if not conv:
        conv = models.AgentConversation(
            id=conv_id,
            user_id=user_id,
            title=title,
        )
        db.add(conv)
    else:
        conv.title = title

    # Nếu gửi messages lên, cập nhật danh sách
    messages_data = payload.get("messages", [])
    if messages_data:
        # Xóa các message cũ để sync
        db.query(models.AgentMessage).filter_by(conversation_id=conv_id).delete()
        for m in messages_data:
            db.add(
                models.AgentMessage(
                    id=f"msg_{uuid.uuid4().hex[:12]}",
                    conversation_id=conv_id,
                    role=m.get("role", "user"),
                    content=m.get("content", ""),
                )
            )

    db.commit()
    return {"status": "success", "conversation_id": conv_id}


@router.delete("/conversations/{conv_id}")
def delete_conversation(
    conv_id: str,
    db: Session = Depends(get_db),
):
    """
    Xóa một cuộc trò chuyện cố vấn AI.
    """
    conv = db.query(models.AgentConversation).filter_by(id=conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Không tìm thấy cuộc trò chuyện")

    db.delete(conv)
    db.commit()
    return {"status": "success", "message": "Đã xóa cuộc trò chuyện"}
