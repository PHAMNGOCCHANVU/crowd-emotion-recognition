"""
chatbot.py — REST API endpoints for Chatbot Phân tích Cảm xúc & Phong thái
==========================================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import InterviewSession
from ..schemas import ChatRequest, ChatResponse
from ..services.chatbot_service import ChatbotService

router = APIRouter(prefix="/api/sessions", tags=["chatbot"])

# Singleton chatbot service instance
_chatbot_service = ChatbotService()


@router.post(
    "/{session_id}/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
)
async def chat_with_session_coach(
    session_id: str,
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    """
    Tiếp nhận câu hỏi từ ứng viên về phiên phỏng vấn:
    - AI tự động trích xuất diễn biến cảm xúc trong khoảng thời gian bất kỳ
    - Tự động gọi tool (Gemini Function Calling hoặc Mock Engine)
    - Trả lời chi tiết và kèm lời khuyên cải thiện
    """
    session = (
        db.query(InterviewSession)
        .filter(InterviewSession.id == session_id)
        .first()
    )
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Không tìm thấy phiên phỏng vấn với ID '{session_id}'",
        )

    result = await _chatbot_service.chat(
        session_id=session_id,
        user_message=request.message,
        db=db,
    )

    return ChatResponse(
        session_id=result["session_id"],
        response=result["response"],
        tools_used=result.get("tools_used", []),
        is_mock=result.get("is_mock", False),
        timestamp=result["timestamp"],
    )


@router.get("/{session_id}/chat/history")
def get_session_chat_history(session_id: str, db: Session = Depends(get_db)):
    """Lấy danh sách các lượt hội thoại trước đó của phiên."""
    session = (
        db.query(InterviewSession)
        .filter(InterviewSession.id == session_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên phỏng vấn")

    history = _chatbot_service.get_history(session_id)
    return {"session_id": session_id, "history": history}


@router.delete("/{session_id}/chat/history")
def clear_session_chat_history(session_id: str):
    """Xóa lịch sử hội thoại của phiên."""
    _chatbot_service.clear_history(session_id)
    return {"session_id": session_id, "message": "Đã làm mới lịch sử hội thoại."}
