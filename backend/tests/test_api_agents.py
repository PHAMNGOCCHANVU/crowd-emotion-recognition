"""
Test Suite: AI Advisor Agent API (/api/agents/chat & /api/agents/conversations)
Covers Happy Path, Contextual Awareness, Edge Cases, Failure Modes, and Security.
"""

import pytest
from backend.tests.fixtures_api import db_session, client
from backend.tests.test_api_sessions import seed_completed_session


class TestAgentChatAPI:
    """Kiểm thử chat với Cố vấn AI (/api/agents/chat)."""

    def test_agent_chat_general_message(self, client):
        """Happy Path: Gửi tin nhắn chào hỏi thông thường."""
        payload = {
            "message": "Xin chào Cố vấn AI, tôi cần lời khuyên.",
            "user_id": "user_123",
        }
        response = client.post("/api/agents/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "conversation_id" in data
        assert "reply" in data
        assert len(data["reply"]) > 0
        assert isinstance(data["suggestions"], list)
        assert len(data["suggestions"]) >= 1

    def test_agent_chat_filler_word_awareness(self, client, db_session):
        """Contextual Logic: Nhắc đến 'từ đệm' kích hoạt hướng dẫn STAR & hơi thở bụng."""
        seed_completed_session(db_session, user_id="user_123", session_id="sess_agent_1")
        payload = {
            "message": "Tôi hay bị run và dùng nhiều từ đệm khi nói, làm sao khắc phục?",
            "user_id": "user_123",
        }
        response = client.post("/api/agents/chat", json=payload)
        assert response.status_code == 200
        reply = response.json()["reply"]
        assert "từ đệm" in reply or "STAR" in reply or "hơi thở" in reply

    def test_agent_chat_performance_awareness(self, client, db_session):
        """Contextual Logic: Nhắc đến 'tiến độ', 'cải thiện' kích hoạt phân tích điểm."""
        seed_completed_session(db_session, user_id="user_123", session_id="sess_agent_2")
        payload = {
            "message": "Đánh giá giúp tôi điểm mạnh và tiến độ cải thiện gần đây.",
            "user_id": "user_123",
        }
        response = client.post("/api/agents/chat", json=payload)
        assert response.status_code == 200
        reply = response.json()["reply"]
        assert "Điểm trung bình" in reply or "Điểm mạnh" in reply

    def test_agent_chat_continue_existing_conversation(self, client):
        """Happy Path: Gửi tin nhắn tiếp theo trong cùng conversation_id."""
        first_payload = {"message": "Câu hỏi đầu tiên", "user_id": "user_123"}
        first_res = client.post("/api/agents/chat", json=first_payload)
        assert first_res.status_code == 200
        conv_id = first_res.json()["conversation_id"]

        second_payload = {
            "conversation_id": conv_id,
            "message": "Câu hỏi tiếp theo",
            "user_id": "user_123",
        }
        second_res = client.post("/api/agents/chat", json=second_payload)
        assert second_res.status_code == 200
        assert second_res.json()["conversation_id"] == conv_id

        # Kiểm tra danh sách hội thoại có conversation_id này
        list_res = client.get("/api/agents/conversations?user_id=user_123")
        assert list_res.status_code == 200
        conv_item = next((c for c in list_res.json() if c["id"] == conv_id), None)
        assert conv_item is not None
        assert len(conv_item["messages"]) >= 4  # 2 user + 2 assistant

    def test_agent_chat_xss_and_sql_injection_payload(self, client):
        """Security: Payload độc hại XSS và SQL Injection được lưu an toàn."""
        malicious_msg = "<script>alert('xss');</script>' OR '1'='1; DROP TABLE users; --"
        payload = {"message": malicious_msg, "user_id": "user_123"}
        response = client.post("/api/agents/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "conversation_id" in data

    def test_agent_chat_unicode_and_special_characters(self, client):
        """Boundary Case: Tiếng Việt có dấu, emoji, ký tự đặc biệt."""
        unicode_msg = "🔥 Thử nghiệm tiếng Việt: Nguyễn Văn A, đỗ đạt thủ khoa! 🎉 @#$%^&*"
        payload = {"message": unicode_msg, "user_id": "user_123"}
        response = client.post("/api/agents/chat", json=payload)
        assert response.status_code == 200


class TestAgentConversationsAPI:
    """Kiểm thử quản lý cuộc hội thoại (/api/agents/conversations)."""

    def test_list_conversations_happy_path(self, client):
        """Happy Path: Lấy danh sách hội thoại của user."""
        client.post("/api/agents/chat", json={"message": "Chào bạn", "user_id": "user_123"})
        response = client.get("/api/agents/conversations?user_id=user_123")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_save_conversation_sync(self, client):
        """Happy Path: Đồng bộ conversation qua PUT /api/agents/conversations/{conv_id}."""
        sync_payload = {
            "title": "Hội thoại lưu từ giao diện",
            "messages": [
                {"role": "user", "content": "Em muốn hỏi về lương"},
                {"role": "assistant", "content": "Bạn hãy nghiên cứu thị trường trước"},
            ],
        }
        res = client.put("/api/agents/conversations/conv_custom_sync", json=sync_payload)
        assert res.status_code == 200
        assert res.json()["status"] == "success"

        # Kiểm tra danh sách có hội thoại vừa sync
        list_res = client.get("/api/agents/conversations?user_id=user_123")
        assert list_res.status_code == 200
        found = any(c["id"] == "conv_custom_sync" for c in list_res.json())
        assert found is True

    def test_delete_conversation_happy_path(self, client):
        """Happy Path: Xóa hội thoại thành công."""
        chat_res = client.post("/api/agents/chat", json={"message": "Tạm biệt", "user_id": "user_123"})
        conv_id = chat_res.json()["conversation_id"]

        del_res = client.delete(f"/api/agents/conversations/{conv_id}")
        assert del_res.status_code in [200, 204]

        # Sau khi xóa, không còn trong danh sách
        list_res = client.get("/api/agents/conversations?user_id=user_123")
        assert all(c["id"] != conv_id for c in list_res.json())

    def test_delete_conversation_not_found(self, client):
        """Failure Mode: Xóa conversation không tồn tại trả về 404."""
        response = client.delete("/api/agents/conversations/ghost_id_000")
        assert response.status_code == 404
