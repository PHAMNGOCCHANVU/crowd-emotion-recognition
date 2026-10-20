import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
import backend.models as models
from ..schemas import (
    AgentChatRequest,
    AgentChatResponse,
    AgentConversationResponse,
    AgentMessageItem,
)

router = APIRouter(prefix="/api/agents", tags=["agents"])


def generate_advisor_response(user_message: str, sessions: List[models.InterviewSession]) -> tuple[str, List[str]]:
    """
    Sinh phản hồi tư vấn thông minh dựa trên dữ liệu phỏng vấn thực tế của ứng viên.
    """
    msg_lower = user_message.lower()

    # Thống kê nhanh dữ liệu của ứng viên
    total_sessions = len(sessions)
    if total_sessions > 0:
        avg_score = sum(s.overall_score or 0.0 for s in sessions) / total_sessions
        latest_role = sessions[0].role_name
    else:
        avg_score = 0.0
        latest_role = "vị trí của bạn"

    if any(k in msg_lower for k in ["từ đệm", "run", "lo lắng", "căng thẳng", "stress"]):
        reply = (
            f"Dựa trên các phiên phỏng vấn gần đây cho vị trí {latest_role}, điểm phong thái của bạn đang ở mức khá ({int(avg_score)}/100). "
            "Để khắc phục việc dùng từ đệm và giảm hồi hộp, tôi khuyên bạn:\n"
            "1. **Tạm dừng 2 giây trước khi trả lời:** Não bộ cần thời gian sắp xếp ý, hãy hít thở sâu thay vì phát ra từ 'ừm', 'à'.\n"
            "2. **Phương pháp STAR:** Khi trả lời câu hỏi tình huống, bám sát Situation - Task - Action - Result để không bị lạc đề.\n"
            "3. **Tập trung vào hơi thở bụng:** Giúp nhịp tim ổn định và giọng nói trầm ấm hơn."
        )
        suggestions = [
            "Cách giảm từ đệm hiệu quả",
            "Luyện tập kỹ thuật hít thở 4-4-4",
            "Xem lại câu trả lời có nhiều từ đệm nhất",
        ]
    elif any(k in msg_lower for k in ["điểm mạnh", "cải thiện", "đánh giá", "tiến độ", "kết quả"]):
        reply = (
            f"Tổng quan quá trình luyện tập của bạn qua {total_sessions} buổi phỏng vấn:\n"
            f"- **Điểm trung bình:** {avg_score:.1f}/100.\n"
            "- **Điểm mạnh:** Bạn nắm vững kiến thức chuyên môn cốt lõi và có sự chuẩn bị kỹ càng.\n"
            "- **Cần cải thiện:** Cần tăng tính mạch lạc khi trả lời các câu hỏi tình huống và biểu cảm tự tin hơn trước ống kính camera."
        )
        suggestions = [
            "Làm sao để biểu cảm tự tin hơn trước webcam?",
            "Luyện câu hỏi tình huống theo mô hình STAR",
            "Đăng ký phỏng vấn thử vị trí mới",
        ]
    else:
        reply = (
            f"Chào bạn! Tôi là Trợ lý Cố vấn AI của InterviewLab. Tôi đã nắm được dữ liệu {total_sessions} phiên luyện tập của bạn "
            f"với vị trí gần nhất là {latest_role}.\n"
            "Tôi có thể hỗ trợ bạn phân tích chi tiết điểm số, cách tối ưu câu trả lời chuyên môn, hoặc kỹ thuật giảm căng thẳng khi đối diện nhà tuyển dụng."
        )
        suggestions = [
            "Làm sao để trả lời câu hỏi giới thiệu bản thân ấn tượng?",
            "Các lỗi thường gặp khiến ứng viên bị mất điểm",
            "Chiến lược đàm phán lương hiệu quả",
        ]

    return reply, suggestions


@router.post("/chat", response_model=AgentChatResponse)
def chat_with_agent(
    req: AgentChatRequest,
    user_id: Optional[str] = Query("user_123"),
    db: Session = Depends(get_db),
):
    """
    Gửi câu hỏi tới AI Advisor để nhận lời khuyên dựa trên dữ liệu phỏng vấn của user.
    """
    # Lấy lịch sử phỏng vấn của ứng viên để cá nhân hóa
    user_sessions = (
        db.query(models.InterviewSession)
        .filter(models.InterviewSession.user_id == user_id)
        .order_by(models.InterviewSession.created_at.desc())
        .all()
    )

    reply_text, suggestions = generate_advisor_response(req.message, user_sessions)

    # Quản lý Conversation trong DB
    conv_id = req.conversation_id
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

    # Lưu tin nhắn user và agent
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
    )


@router.get("/conversations", response_model=List[AgentConversationResponse])
def list_conversations(
    user_id: Optional[str] = Query("user_123"),
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
    user_id: Optional[str] = Query("user_123"),
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
