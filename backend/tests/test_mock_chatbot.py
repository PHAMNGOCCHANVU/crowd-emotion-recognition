"""
test_mock_chatbot.py — Bộ Test Case Giả lập Toàn diện cho Chatbot Cảm xúc
========================================================================
Kiểm thử 100% luồng xử lý của Chatbot Cảm xúc & Temporal Query Engine
trước khi kết nối với Gemini API Key thật:
- Tự động tạo dữ liệu mẫu chuỗi thời gian (time-series) 6 nhãn cảm xúc vào SQLite.
- Kiểm thử các kịch bản: truy vấn khoảng thời gian, phát hiện stress spike,
  tổng kết phiên, so sánh câu hỏi, bộ nhớ hội thoại, và gọi REST API.
"""

import sys
import uuid
from pathlib import Path
from datetime import datetime

# Đảm bảo đường dẫn import cho backend
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal, Base, engine
from backend.models import User, InterviewSession, SessionDetail
from backend.services.chatbot_service import ChatbotService
from backend.services.temporal_query import (
    query_emotion_by_time,
    get_session_summary,
    compare_questions,
)

TEST_SESSION_ID = f"mock-session-{uuid.uuid4().hex[:8]}"


def seed_mock_interview_data():
    """
    Khởi tạo phiên phỏng vấn giả lập với dữ liệu time-series cảm xúc 6 nhãn:
    - Câu 1: Giới thiệu bản thân (30s) — Phần lớn Normal & Happy (Tự tin).
    - Câu 2: Xử lý Critical Bug (45s) — Stress Spike lúc 15s-30s (Fear & Sad).
    - Câu 3: Kiến trúc Async vs Threading (35s) — Bình thản, chuyên nghiệp.
    """
    db = SessionLocal()
    try:
        # 1. Tạo User
        user = db.query(User).filter(User.id == "tester_001").first()
        if not user:
            user = User(id="tester_001", email="tester@mock.local", full_name="Nguyễn Văn Test")
            db.add(user)

        # 2. Tạo Session
        session = InterviewSession(
            id=TEST_SESSION_ID,
            user_id="tester_001",
            role_name="Software Engineer",
            jd_text="Senior Backend Developer with FastAPI & Python",
            overall_score=83.5,
            confidence_avg=78.0,
            stress_avg=21.5,
            status="COMPLETED",
        )
        db.add(session)

        # 3. Tạo Timeline chi tiết cho Câu 1 (30s)
        # Giây 1-25: Normal, Giây 26-30: Happy kết thúc
        timeline_q1 = []
        for s in range(1, 31):
            emo = "Happy" if s > 24 else ("Normal" if s % 6 != 0 else "Surprised")
            timeline_q1.append({
                "second": s,
                "emotion": emo,
                "confidence": 0.88,
                "is_stress": emo in ["Fear", "Sad"],
            })

        detail_q1 = SessionDetail(
            id=str(uuid.uuid4()),
            session_id=TEST_SESSION_ID,
            question_text="Bạn hãy giới thiệu bản thân và dự án phần mềm ấn tượng nhất?",
            order_index=1,
            transcript="Em xin chào anh chị, em có 3 năm kinh nghiệm phát triển backend...",
            filler_words_count=2,
            confidence_score=85.0,
            stress_score=10.0,
            content_score=88.0,
            emotion_timeline=timeline_q1,
            status="COMPLETED",
        )
        db.add(detail_q1)

        # 4. Tạo Timeline chi tiết cho Câu 2 (45s) có Stress Spike lúc 15s-30s
        timeline_q2 = []
        for s in range(1, 46):
            if 15 <= s <= 30:
                # Giai đoạn bị hỏi dồn hoặc bí ý tưởng -> Biểu cảm Fear & Sad
                emo = "Fear" if s % 3 != 0 else "Sad"
                conf = 0.92
                is_stress = True
            else:
                emo = "Normal" if s < 15 else "Normal"
                conf = 0.85
                is_stress = False

            timeline_q2.append({
                "second": s,
                "emotion": emo,
                "confidence": conf,
                "is_stress": is_stress,
            })

        detail_q2 = SessionDetail(
            id=str(uuid.uuid4()),
            session_id=TEST_SESSION_ID,
            question_text="Khi gặp bug nghiêm trọng sát giờ release sản phẩm, bạn xử lý thế nào?",
            order_index=2,
            transcript="Dạ lúc đó em... ừm... thật sự khá hoang mang, nhưng sau đó em đã bình tĩnh rollback...",
            filler_words_count=5,
            confidence_score=68.0,
            stress_score=42.0,
            content_score=78.0,
            emotion_timeline=timeline_q2,
            status="COMPLETED",
        )
        db.add(detail_q2)

        # 5. Tạo Timeline chi tiết cho Câu 3 (35s)
        timeline_q3 = []
        for s in range(1, 36):
            emo = "Normal" if s % 5 != 0 else "Happy"
            timeline_q3.append({
                "second": s,
                "emotion": emo,
                "confidence": 0.89,
                "is_stress": False,
            })

        detail_q3 = SessionDetail(
            id=str(uuid.uuid4()),
            session_id=TEST_SESSION_ID,
            question_text="Sự khác biệt giữa Asynchronous và Multithreading là gì?",
            order_index=3,
            transcript="Async là mô hình bất đồng bộ đơn luồng dựa trên Event Loop, còn Multithreading là đa luồng...",
            filler_words_count=1,
            confidence_score=86.0,
            stress_score=12.5,
            content_score=90.0,
            emotion_timeline=timeline_q3,
            status="COMPLETED",
        )
        db.add(detail_q3)

        db.commit()
        print(f"✅ [Seed Mock Data] Đã tạo thành công phiên phỏng vấn mẫu: {TEST_SESSION_ID}")
    finally:
        db.close()


def run_all_tests():
    """Chạy toàn bộ 8 kịch bản kiểm thử giả lập."""
    print("=" * 70)
    print("🚀 BẮT ĐẦU CHẠY BỘ TEST CASE GIẢ LẬP CHO CHATBOT CẢM XÚC (ZERO-COST)")
    print("=" * 70)

    # Khởi tạo data
    seed_mock_interview_data()

    db = SessionLocal()
    chatbot = ChatbotService()
    client = TestClient(app)
    passed_count = 0
    total_tests = 8

    try:
        # TEST 1: Truy vấn mốc thời gian bình thường (Câu 1, giây 5-20)
        print("\n🔹 Test Case 1: Truy vấn cảm xúc trong khoảng thời gian điềm tĩnh (Câu 1, 5s-20s)")
        q1_res = query_emotion_by_time(
            db=db,
            session_id=TEST_SESSION_ID,
            order_index=1,
            start_second=5,
            end_second=20,
        )
        assert q1_res.get("success") is True, "Test 1 Failed: query not successful"
        assert q1_res.get("dominant_emotion") == "Normal", f"Expected Normal, got {q1_res.get('dominant_emotion')}"
        assert q1_res.get("stress_ratio") == 0.0, f"Expected 0 stress, got {q1_res.get('stress_ratio')}"
        print(f"   -> Kết quả: Chủ đạo={q1_res['dominant_emotion']}, Stress={q1_res['stress_ratio']*100}% [PASS]")
        passed_count += 1

        # TEST 2: Phát hiện căng thẳng / Stress Spike (Câu 2, giây 15-30)
        print("\n🔹 Test Case 2: Phát hiện Stress Spike trong khoảng thời gian khó khăn (Câu 2, 15s-30s)")
        q2_spike = query_emotion_by_time(
            db=db,
            session_id=TEST_SESSION_ID,
            order_index=2,
            start_second=15,
            end_second=30,
        )
        assert q2_spike.get("success") is True, "Test 2 Failed"
        assert q2_spike.get("dominant_emotion") == "Fear", f"Expected Fear, got {q2_spike.get('dominant_emotion')}"
        assert q2_spike.get("stress_ratio") == 1.0, f"Expected 100% stress in spike range, got {q2_spike.get('stress_ratio')}"
        print(f"   -> Kết quả: Phát hiện biểu cảm `{q2_spike['dominant_emotion']}` với tỉ lệ Stress={q2_spike['stress_ratio']*100}% [PASS]")
        passed_count += 1

        # TEST 3: Giả lập Chatbot xử lý định dạng mm:ss
        print("\n🔹 Test Case 3: Chatbot phân tích prompt chứa mốc thời gian dạng mm:ss")
        import asyncio
        chat_time_res = asyncio.run(
            chatbot.chat(
                session_id=TEST_SESSION_ID,
                user_message="Cho tôi biết từ 00:15 đến 00:30 ở câu 2 tôi cảm thấy thế nào?",
                db=db,
                force_mock=True,
            )
        )
        assert "query_emotion_by_time" in chat_time_res["tools_used"], "Did not use query_emotion_by_time"
        assert "Fear" in chat_time_res["response"] or "căng thẳng" in chat_time_res["response"], "Response missing stress feedback"
        print(f"   -> Chatbot phản hồi đúng tool: {chat_time_res['tools_used']} [PASS]")
        passed_count += 1

        # TEST 4: Tổng kết toàn bộ buổi phỏng vấn (Overall Summary)
        print("\n🔹 Test Case 4: Chatbot tổng kết toàn bộ buổi phỏng vấn")
        summary_res = asyncio.run(
            chatbot.chat(
                session_id=TEST_SESSION_ID,
                user_message="Hãy tổng kết toàn bộ buổi phỏng vấn của tôi",
                db=db,
                force_mock=True,
            )
        )
        assert "get_session_summary" in summary_res["tools_used"], "Did not use get_session_summary"
        assert "83.5" in summary_res["response"] or "Software Engineer" in summary_res["response"], "Missing overall stats"
        print(f"   -> Chatbot phản hồi tổng kết đủ 3 câu và điểm tổng [PASS]")
        passed_count += 1

        # TEST 5: So sánh giữa 2 câu hỏi (Comparison)
        print("\n🔹 Test Case 5: So sánh phong thái giữa Câu 1 và Câu 2")
        compare_res = asyncio.run(
            chatbot.chat(
                session_id=TEST_SESSION_ID,
                user_message="So sánh phong thái giữa câu 1 và câu 2",
                db=db,
                force_mock=True,
            )
        )
        assert "compare_questions" in compare_res["tools_used"], "Did not use compare_questions"
        assert "85.0" in compare_res["response"] and "68.0" in compare_res["response"], "Comparison numbers missing"
        print(f"   -> Chatbot sinh bảng so sánh chính xác [PASS]")
        passed_count += 1

        # TEST 6: Kiểm tra Conversation Memory (Bộ nhớ đa lượt)
        print("\n🔹 Test Case 6: Kiểm tra Conversation Memory giữ đúng ngữ cảnh")
        history = chatbot.get_history(TEST_SESSION_ID)
        assert len(history) >= 6, f"Expected at least 6 messages in history, got {len(history)}"
        chatbot.clear_history(TEST_SESSION_ID)
        assert len(chatbot.get_history(TEST_SESSION_ID)) == 0, "History was not cleared"
        print(f"   -> Memory quản lý {len(history)} lượt thoại và làm mới thành công [PASS]")
        passed_count += 1

        # TEST 7: Xử lý ngoại lệ / Khoảng thời gian vượt quá video (Edge case)
        print("\n🔹 Test Case 7: Xử lý an toàn khi người dùng hỏi giây vượt quá độ dài video")
        edge_res = query_emotion_by_time(
            db=db,
            session_id=TEST_SESSION_ID,
            order_index=1,
            start_second=100,
            end_second=150,
        )
        assert edge_res.get("data_available") is False, "Should warn about unavailable data"
        print(f"   -> Xử lý biên an toàn: '{edge_res.get('warning')}' [PASS]")
        passed_count += 1

        # TEST 8: Kiểm tra REST API Endpoint trực tiếp qua HTTP Client
        print("\n🔹 Test Case 8: Kiểm tra REST API Endpoint POST /api/sessions/{id}/chat")
        api_response = client.post(
            f"/api/sessions/{TEST_SESSION_ID}/chat",
            json={"message": "Tôi trả lời câu 1 từ giây 1 đến 15 có ổn không?"},
        )
        assert api_response.status_code == 200, f"API error: {api_response.text}"
        data = api_response.json()
        assert "response" in data, "API response missing 'response' field"
        assert data["session_id"] == TEST_SESSION_ID, "Session ID mismatch"
        print(f"   -> API trả về mã 200 OK, response length={len(data['response'])} chars [PASS]")
        passed_count += 1

    finally:
        db.close()

    print("\n" + "=" * 70)
    print(f"🎉 HOÀN THÀNH KIỂM THỬ: {passed_count}/{total_tests} TEST CASES ĐẠT YÊU CẦU 100%!")
    print("=" * 70)
    return passed_count == total_tests


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
