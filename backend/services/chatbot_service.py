"""
chatbot_service.py — Hybrid Chatbot Service (Gemini Function Calling + Mock Mode)
================================================================================
Quản lý hội thoại thông minh giữa Ứng viên và AI Coach:
- Hỗ trợ Gemini Function Calling khi có GEMINI_API_KEY.
- Hỗ trợ Chế độ Giả lập (Mock Mode / Fallback Simulator) để kiểm thử toàn diện
  mà KHÔNG tốn chi phí và không cần API Key thật.
- Lưu trữ Conversation Memory (bộ nhớ nhiều lượt thoại).
"""

import json
import logging
import os
import re
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from .temporal_query import (
    compare_questions,
    get_candidate_global_summary,
    get_question_critique_data,
    get_session_summary,
    query_emotion_by_time,
)

logger = logging.getLogger("chatbot_service")


class ChatbotService:
    """
    Service Chatbot Hybrid:
    Tích hợp Gemini Tool Calling + Local Temporal Query Engine + Conversation Memory.
    Hỗ trợ cả phân tích cụ thể từng phiên phỏng vấn và Cố vấn AI toàn cục (Advisor).
    """

    def __init__(self, api_key: str | None = None, max_history_turns: int = 15):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.max_history_turns = max_history_turns
        # Lưu trữ hội thoại in-memory: {conv_id: [{"role": str, "content": str, "timestamp": str}]}
        self.memory: dict[str, list[dict[str, str]]] = {}

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        """Lấy danh sách các lượt thoại trước đó của phiên."""
        return self.memory.get(session_id, [])

    def add_turn(self, session_id: str, role: str, content: str):
        """Thêm 1 lượt thoại mới vào bộ nhớ hội thoại."""
        if session_id not in self.memory:
            self.memory[session_id] = []
        self.memory[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(UTC).isoformat(),
        })
        # Giới hạn số lượt thoại gần nhất để tránh tràn context
        max_items = self.max_history_turns * 2
        if len(self.memory[session_id]) > max_items:
            self.memory[session_id] = self.memory[session_id][-max_items:]

    def clear_history(self, session_id: str):
        """Xóa lịch sử hội thoại của 1 session."""
        if session_id in self.memory:
            del self.memory[session_id]

    def _execute_local_tool(
        self,
        tool_name: str,
        tool_args: dict[str, Any],
        session_id: str,
        db: Session,
    ) -> dict[str, Any]:
        """Thực thi tool cục bộ dựa trên yêu cầu function calling hoặc mock router."""
        if not session_id:
            return {"error": "Cần có mã phiên phỏng vấn (session_id) để tra cứu dữ liệu chi tiết."}

        if tool_name == "query_emotion_by_time":
            order_index = tool_args.get("order_index", 1)
            start_second = tool_args.get("start_second", 0)
            end_second = tool_args.get("end_second", 15)
            return query_emotion_by_time(
                db=db,
                session_id=session_id,
                order_index=int(order_index),
                start_second=int(start_second),
                end_second=int(end_second),
            )

        elif tool_name == "get_session_summary":
            include_timeline = tool_args.get("include_timeline", False)
            return get_session_summary(
                db=db,
                session_id=session_id,
                include_timeline=bool(include_timeline),
            )

        elif tool_name == "compare_questions":
            q_a = tool_args.get("question_a", 1)
            q_b = tool_args.get("question_b", 2)
            return compare_questions(
                db=db,
                session_id=session_id,
                question_a=int(q_a),
                question_b=int(q_b),
            )

        elif tool_name == "get_question_critique":
            order_index = tool_args.get("order_index", 1)
            return get_question_critique_data(
                db=db,
                session_id=session_id,
                order_index=int(order_index),
            )

        return {"error": f"Tool '{tool_name}' không được hỗ trợ."}

    def _mock_intent_parser(self, message: str) -> tuple[str, dict[str, Any]]:
        """
        Parser dự phòng giả lập: Tự động trích xuất ý định và tham số
        từ câu hỏi của người dùng khi chưa có API Key hoặc gọi mock.
        """
        msg_lower = message.lower()

        # 1. Kiểm tra so sánh 2 câu: ví dụ "so sánh câu 1 và câu 3", "câu 1 vs câu 2"
        compare_match = re.search(r"(?:so sánh|so|vs).*?câu\s*(\d+).*?(?:và|với|vs|,)\s*câu\s*(\d+)", msg_lower)
        if compare_match:
            qa, qb = int(compare_match.group(1)), int(compare_match.group(2))
            return "compare_questions", {"question_a": qa, "question_b": qb}

        # 2. Kiểm tra nhận xét / góp ý câu hỏi cụ thể:
        order_match = re.search(r"câu(?:\s*hỏi)?\s*(\d+)", msg_lower)
        order_idx = int(order_match.group(1)) if order_match else 1

        if any(kw in msg_lower for kw in ["nhận xét", "góp ý", "chấm điểm", "câu trả lời mẫu", "sửa câu", "đánh giá", "lời nói", "transcript"]):
            return "get_question_critique", {"order_index": order_idx}

        # 3. Kiểm tra truy vấn thời gian:
        time_mm_ss = re.search(r"(\d{1,2}):(\d{2})\s*(?:đến|-|tới)\s*(\d{1,2}):(\d{2})", msg_lower)
        if time_mm_ss:
            s_sec = int(time_mm_ss.group(1)) * 60 + int(time_mm_ss.group(2))
            e_sec = int(time_mm_ss.group(3)) * 60 + int(time_mm_ss.group(4))
            return "query_emotion_by_time", {"order_index": order_idx, "start_second": s_sec, "end_second": e_sec}

        time_range = re.search(r"(?:từ\s*)?(?:giây\s*)?(\d+)\s*(?:đến|-|tới)\s*(?:giây\s*)?(\d+)", msg_lower)
        if time_range and ("giây" in msg_lower or "khoảng" in msg_lower or "lúc" in msg_lower or "từ" in msg_lower):
            s_sec, e_sec = int(time_range.group(1)), int(time_range.group(2))
            return "query_emotion_by_time", {"order_index": order_idx, "start_second": s_sec, "end_second": e_sec}

        # 4. Kiểm tra tổng kết phiên:
        return "get_session_summary", {"include_timeline": False}

    def _generate_mock_response(
        self,
        tool_name: str,
        tool_data: dict[str, Any],
        user_message: str,
    ) -> str:
        """
        Sinh câu trả lời tiếng Việt chuyên nghiệp giả lập LLM
        dựa trên dữ liệu thực tế trích xuất từ database.
        """
        if not tool_data.get("success", False):
            err_msg = tool_data.get("error") or tool_data.get("warning") or "Không tìm thấy dữ liệu phù hợp."
            return f"⚠️ **Thông báo từ AI Coach:** {err_msg}\n\n*Gợi ý:* Bạn hãy kiểm tra lại số thứ tự câu hỏi hoặc khoảng thời gian video của bạn nhé!"

        if tool_name == "query_emotion_by_time":
            time_range = tool_data.get("time_range", "")
            q_idx = tool_data.get("order_index", 1)
            dominant = tool_data.get("dominant_emotion", "Normal")
            avg_conf = round(tool_data.get("average_confidence", 0.0) * 100, 1)
            stress_ratio = round(tool_data.get("stress_ratio", 0.0) * 100, 1)
            dist = tool_data.get("emotion_distribution", {})

            if dominant in ["Happy", "Normal"] and stress_ratio < 20:
                tone_comment = "Phong thái của bạn trong giai đoạn này rất điềm tĩnh, tự nhiên và vững vàng."
                advice = "Hãy tiếp tục duy trì ánh mắt hướng về ống kính và nụ cười tự tin như trong khoảng thời gian này!"
            elif dominant in ["Fear", "Sad"] or stress_ratio >= 40:
                tone_comment = f"Trong khoảng này, hệ thống phát hiện biểu cảm lo âu/căng thẳng chiếm {stress_ratio}%. Có thể bạn đang suy nghĩ giải thuật hoặc gặp câu hỏi hóc búa."
                advice = "Khi cần suy nghĩ, bạn có thể xin phép nhà tuyển dụng 5-10 giây để sắp xếp ý thay vì để lộ nét mặt bối rối."
            else:
                tone_comment = f"Cảm xúc chủ đạo là **{dominant}** với độ tin cậy {avg_conf}%."
                advice = "Hãy giữ nhịp thở đều đặn để giọng nói và cơ mặt được thư giãn tự nhiên hơn."

            dist_str = ", ".join([f"{k}: {v*100:.0f}%" for k, v in dist.items() if v > 0])

            return (
                f"📊 **Phân tích Cảm xúc Câu {q_idx} (Thời gian {time_range}):**\n\n"
                f"- **Biểu cảm chủ đạo:** `{dominant}` (Độ tự tin trung bình: {avg_conf}%)\n"
                f"- **Mức độ căng thẳng (Stress):** `{stress_ratio}%`\n"
                f"- **Phân bổ cảm xúc:** {dist_str}\n\n"
                f"💡 **Nhận xét từ AI Coach:** {tone_comment}\n\n"
                f"🎯 **Lời khuyên:** {advice}"
            )

        elif tool_name == "get_session_summary":
            role = tool_data.get("role_name", "General")
            overall = tool_data.get("overall_score", 0.0)
            conf_avg = tool_data.get("confidence_avg", 0.0)
            stress_avg = tool_data.get("stress_avg", 0.0)
            fillers = tool_data.get("total_filler_words", 0)
            q_list = tool_data.get("questions", [])

            lines = [
                f"🏆 **Tổng quan Buổi Phỏng vấn Thử (Vị trí: {role}):**\n",
                f"- **Điểm tổng kết:** `{overall}/100`",
                f"- **Chỉ số Tự tin trung bình:** `{conf_avg}%`",
                f"- **Chỉ số Căng thẳng trung bình:** `{stress_avg}%`",
                f"- **Tổng số từ đệm (ừm, à):** `{fillers}` từ\n",
                "📝 **Chi tiết từng câu hỏi:**",
            ]
            for q in q_list:
                lines.append(
                    f"  • **Câu {q['order_index']}:** Tự tin: {q['confidence_score']}% | Căng thẳng: {q['stress_score']}% | Điểm nội dung: {q['content_score']}%"
                )

            lines.append("\n💡 **Lời khuyên tổng thể:** Bạn có nền tảng kiến thức tốt. Hãy tập trung giảm bớt từ đệm và duy trì phong thái tự tin ở những câu hỏi tình huống hóc búa!")
            return "\n".join(lines)

        elif tool_name == "compare_questions":
            qa = tool_data.get("question_a", {})
            qb = tool_data.get("question_b", {})
            comp = tool_data.get("comparison_result", {})

            return (
                f"⚖️ **So sánh Phong thái giữa Câu {qa.get('order_index')} và Câu {qb.get('order_index')}:**\n\n"
                f"| Tiêu chí | Câu {qa.get('order_index')} | Câu {qb.get('order_index')} |\n"
                f"|---|---|---|\n"
                f"| **Độ tự tin** | {qa.get('confidence_score')}% | {qb.get('confidence_score')}% |\n"
                f"| **Căng thẳng** | {qa.get('stress_score')}% | {qb.get('stress_score')}% |\n"
                f"| **Điểm nội dung** | {qa.get('content_score')}% | {qb.get('content_score')}% |\n"
                f"| **Từ đệm** | {qa.get('filler_words_count')} từ | {qb.get('filler_words_count')} từ |\n\n"
                f"📌 **Kết luận:** Bạn thể hiện tự tin hơn ở **Câu {comp.get('more_confident_question')}** "
                f"(chênh lệch {comp.get('confidence_delta')} điểm tự tin)."
            )

        elif tool_name == "get_question_critique":
            q_idx = tool_data.get("order_index", 1)
            q_text = tool_data.get("question_text", f"Câu hỏi {q_idx}")
            transcript = tool_data.get("transcript", "")
            content_fb = tool_data.get("content_feedback", "")
            delivery_fb = tool_data.get("delivery_feedback", "")
            sample_ans = tool_data.get("sample_answer", "")
            fillers = tool_data.get("filler_words_count", 0)

            return (
                f"📝 **Đánh giá & Gợi ý Cải thiện Câu {q_idx}:**\n"
                f"❓ *\"{q_text}\"*\n\n"
                f"- **Lời nói của bạn (Transcript):** \"{transcript if transcript else 'Không có dữ liệu âm thanh'}\"\n"
                f"- **Số lượng từ đệm:** {fillers} từ\n\n"
                f"🎯 **Nhận xét chuyên môn:**\n{content_fb if content_fb else 'Câu trả lời đã nêu được các ý chính, tuy nhiên cần gắn thêm số liệu thực tế.'}\n\n"
                f"✨ **Nhận xét phong thái:**\n{delivery_fb if delivery_fb else 'Phong thái tương đối tự nhiên, cần chú ý nhìn thẳng vào camera nhiều hơn.'}\n\n"
                f"💡 **Câu trả lời mẫu đề xuất (Model Answer):**\n"
                f"> {sample_ans if sample_ans else 'Áp dụng mô hình STAR (Situation, Task, Action, Result) để cấu trúc câu trả lời mạch lạc.'}"
            )

        return "Cảm ơn bạn đã hỏi. Tôi luôn sẵn sàng hỗ trợ phân tích buổi phỏng vấn của bạn!"

    def _mock_advisor_chat(
        self,
        user_message: str,
        global_summary: dict[str, Any],
        session_id: str | None,
        db: Session,
    ) -> tuple[str, list[str], list[str]]:
        """
        Bộ giả lập phản hồi AI Advisor thông minh dự phòng (Mock Engine):
        Hiểu cả tổng quan ứng viên lẫn chi tiết phiên mà không cần gọi API ngoài.
        """
        tools_used: list[str] = []
        msg_lower = user_message.lower()
        total_sessions = global_summary.get("total_sessions", 0)
        avg_score = global_summary.get("average_overall_score", 0.0)
        avg_conf = global_summary.get("average_confidence", 0.0)
        avg_stress = global_summary.get("average_stress", 0.0)
        roles = global_summary.get("practiced_roles", [])
        recent_sessions = global_summary.get("recent_sessions", [])

        # Trường hợp 1: Hỏi về tổng quan hành trình / số buổi phỏng vấn / điểm trung bình
        if any(kw in msg_lower for kw in ["bao nhiêu phiên", "bao nhiêu lần", "điểm trung bình", "tiến độ", "hành trình", "tổng quan của tôi", "lịch sử"]):
            reply = (
                f"📈 **Tổng quan Hành trình Luyện tập của bạn:**\n\n"
                f"- **Tổng số phiên đã hoàn thành:** `{total_sessions}` buổi\n"
                f"- **Điểm số trung bình:** `{avg_score}/100`\n"
                f"- **Chỉ số Tự tin trung bình:** `{avg_conf}%`\n"
                f"- **Chỉ số Căng thẳng trung bình:** `{avg_stress}%`\n"
                f"- **Các vị trí đã luyện tập:** {', '.join(roles) if roles else 'Chưa có'}\n\n"
            )
            if recent_sessions:
                reply += "✨ **Phiên gần nhất:** " + f"Vị trí `{recent_sessions[0]['role_name']}` đạt `{recent_sessions[0]['overall_score']}` điểm.\n"
                reply += "Bạn muốn tôi phân tích sâu hơn về buổi phỏng vấn gần nhất hay tư vấn cách cải thiện chỉ số nào?"
            else:
                reply += "Bạn hãy bắt đầu phiên phỏng vấn đầu tiên để tôi có thể hỗ trợ chấm điểm và nhận xét chi tiết nhé!"

            return reply, [
                "Phân tích chi tiết buổi phỏng vấn gần nhất",
                "Cách khắc phục điểm yếu và giảm từ đệm",
                "Làm thế nào để nâng điểm tự tin trên 80%?",
            ], tools_used

        # Trường hợp 2: Hỏi về từ đệm (filler words)
        if any(kw in msg_lower for kw in ["từ đệm", "ừm", "à", "filler"]):
            reply = (
                "🗣️ **Chiến lược khắc phục thói quen nói từ đệm (Ừm, À, Dạ):**\n\n"
                "1. **Tạm dừng có chủ đích (Power of Pause):** Khi cần suy nghĩ ý tiếp theo, hãy im lặng 1-2 giây thay vì phát ra âm thanh đệm. Khoảng dừng tạo cảm giác chín chắn và điềm đạm.\n"
                "2. **Thở sâu và hạ nhịp nói:** Nói chậm lại khoảng 15% so với thói quen giúp não bộ kịp sắp xếp từ ngữ.\n"
                "3. **Nguyên tắc một ý - một câu:** Tránh nói các câu phức quá dài khiến bạn bị đuối từ ở giữa câu."
            )
            return reply, [
                "Tôi đã dùng bao nhiêu từ đệm trong phiên vừa rồi?",
                "Phân tích phong thái câu hỏi đầu tiên",
                "Kỹ thuật kiểm soát nhịp thở khi phỏng vấn",
            ], tools_used

        # Trường hợp 3: Hỏi về giảm căng thẳng / stress / lo âu
        if any(kw in msg_lower for kw in ["stress", "căng thẳng", "run", "lo âu", "bình tĩnh"]):
            reply = (
                f"🧘 **Kỹ thuật kiểm soát căng thẳng khi phỏng vấn (Chỉ số stress TB của bạn: {avg_stress}%):**\n\n"
                "1. **Kỹ thuật thở 4-7-8 trước khi bắt đầu:** Hít vào 4 giây, giữ hơi 7 giây và thở ra từ từ trong 8 giây.\n"
                "2. **Ánh mắt hướng camera:** Tránh nhìn quanh phòng khi bị hỏi dồn dập, hãy tập trung vào camera để giữ thế chủ động.\n"
                "3. **Cấu trúc STAR:** Khi gặp câu hỏi khó, bám sát S (Bối cảnh) -> T (Nhiệm vụ) -> A (Hành động) -> R (Kết quả) để tránh bị lạc ý."
            )
            return reply, [
                "Khoảnh khắc nào tôi bị căng thẳng nhất trong phiên?",
                "So sánh mức độ căng thẳng giữa câu 1 và câu 2",
                "Cách mở đầu câu trả lời ấn tượng",
            ], tools_used

        # Trường hợp 4: Người dùng hỏi sâu vào phiên cụ thể hoặc câu hỏi cụ thể
        target_session = session_id or (recent_sessions[0]["id"] if recent_sessions else None)
        if target_session and any(kw in msg_lower for kw in ["câu", "giây", "phút", "vừa rồi", "phiên", "so sánh", "nhận xét", "chấm điểm", "kết quả"]):
            tool_name, tool_args = self._mock_intent_parser(user_message)
            tool_data = self._execute_local_tool(tool_name, tool_args, target_session, db)
            tools_used.append(tool_name)
            response_text = self._generate_mock_response(tool_name, tool_data, user_message)
            suggestions = [
                "Xem nhận xét chi tiết câu 1",
                "So sánh phong thái câu 1 và câu 2",
                "Tổng quan toàn bộ buổi phỏng vấn này",
            ]
            return response_text, suggestions, tools_used

        # Mặc định: Lời chào và giới thiệu khả năng hỗ trợ
        reply = (
            f"Chào bạn! Tôi là **AI Cố vấn Phỏng vấn Nhân sự** của InterviewLab. "
            f"Tôi đã nắm được toàn bộ hành trình với **{total_sessions} phiên luyện tập** của bạn "
            f"(Điểm TB: `{avg_score}/100`, Tự tin TB: `{avg_conf}%`).\n\n"
            "Tôi có thể hỗ trợ bạn:\n"
            "- 📊 Phân tích timeline cảm xúc theo từng giây của từng câu hỏi.\n"
            "- ⚖️ So sánh phong thái, độ tự tin và stress giữa các câu trả lời.\n"
            "- 📝 Góp ý nội dung câu trả lời, phát hiện từ đệm và cung cấp câu trả lời mẫu theo chuẩn STAR.\n\n"
            "Bạn muốn bắt đầu với nội dung nào?"
        )
        suggestions = [
            "Phân tích tổng quan buổi phỏng vấn gần nhất",
            "Xem góp ý câu trả lời mẫu cho câu 1",
            "Mẹo giảm từ đệm và tăng độ tự tin",
        ]
        return reply, suggestions, tools_used

    def _extract_suggestions(self, reply_text: str, current_message: str, has_session: bool) -> list[str]:
        """Tạo gợi ý thông minh linh hoạt theo nội dung câu trả lời."""
        low_text = (reply_text + " " + current_message).lower()
        if "câu 1" in low_text:
            return [
                "So sánh câu 1 và câu 2",
                "Phân tích cảm xúc giây 10 đến 30 câu 1",
                "Gợi ý câu trả lời mẫu hoàn chỉnh cho câu 1",
            ]
        elif "stress" in low_text or "căng thẳng" in low_text:
            return [
                "Làm sao để giữ nụ cười tự nhiên khi bị hỏi khó?",
                "Phân tích những đoạn tôi bị căng thẳng nhất",
                "Kỹ thuật kiểm soát nhịp thở trong 5 giây",
            ]
        elif has_session:
            return [
                "Nhận xét chi tiết nội dung câu 1",
                "So sánh phong thái giữa câu 1 và câu 2",
                "Tổng quan toàn bộ buổi phỏng vấn này",
            ]
        else:
            return [
                "Điểm trung bình và vị trí tôi luyện tập nhiều nhất",
                "Chiến lược giảm từ đệm ừm à hiệu quả",
                "Làm sao để trả lời ấn tượng theo mô hình STAR?",
            ]

    async def chat_advisor(
        self,
        user_message: str,
        db: Session,
        user_id: str = "user_123",
        session_id: str | None = None,
        conversation_history: list[dict[str, str]] | None = None,
        force_mock: bool = False,
    ) -> tuple[str, list[str], list[str]]:
        """
        Unified AI Coach & Advisor:
        Kết hợp dữ liệu tổng hợp toàn cục (Global Context) + Dữ liệu cục bộ của phiên (Local Session)
        thông qua Gemini Function Calling và Mock Fallback chuyên nghiệp.
        """
        # 1. Trích xuất Global Summary
        global_summary = get_candidate_global_summary(db=db, user_id=user_id)
        recent_sessions = global_summary.get("recent_sessions", [])

        # Xác định target session_id: nếu không truyền trực tiếp mà có phiên gần đây
        target_session = session_id
        if not target_session and recent_sessions:
            # Nếu câu hỏi nhắc đến phiên vừa rồi / câu X / giây X -> ưu tiên session gần nhất
            low_msg = user_message.lower()
            if any(k in low_msg for k in ["vừa rồi", "gần nhất", "câu ", "giây", "so sánh", "nhận xét câu"]):
                target_session = recent_sessions[0]["id"]

        tools_used: list[str] = []

        # 2. Kiểm tra chế độ Mock / Fallback
        if not self.api_key or force_mock:
            return self._mock_advisor_chat(
                user_message=user_message,
                global_summary=global_summary,
                session_id=target_session,
                db=db,
            )

        # 3. Chế độ Gemini LLM Function Calling
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)

            # Khai báo 4 Function Declarations
            query_time_func = types.FunctionDeclaration(
                name="query_emotion_by_time",
                description="Truy vấn diễn biến cảm xúc (tự tin, stress, dominant emotion) trong khoảng thời gian cụ thể (giây X đến Y) của một câu hỏi phỏng vấn.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "order_index": types.Schema(type=types.Type.INTEGER, description="Số thứ tự câu hỏi (1, 2, 3...)"),
                        "start_second": types.Schema(type=types.Type.INTEGER, description="Giây bắt đầu"),
                        "end_second": types.Schema(type=types.Type.INTEGER, description="Giây kết thúc"),
                    },
                    required=["order_index", "start_second", "end_second"],
                ),
            )

            get_summary_func = types.FunctionDeclaration(
                name="get_session_summary",
                description="Lấy báo cáo tổng hợp buổi phỏng vấn cụ thể (điểm tổng, tự tin, stress, số từ đệm, điểm từng câu).",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "include_timeline": types.Schema(type=types.Type.BOOLEAN, description="Kèm timeline chi tiết theo giây"),
                    },
                ),
            )

            compare_func = types.FunctionDeclaration(
                name="compare_questions",
                description="So sánh chỉ số cảm xúc, phong thái, độ tự tin và stress giữa 2 câu hỏi trong cùng phiên.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "question_a": types.Schema(type=types.Type.INTEGER, description="Số câu hỏi thứ nhất (1, 2...)"),
                        "question_b": types.Schema(type=types.Type.INTEGER, description="Số câu hỏi thứ hai (1, 2...)"),
                    },
                    required=["question_a", "question_b"],
                ),
            )

            critique_func = types.FunctionDeclaration(
                name="get_question_critique",
                description="Lấy chi tiết transcript (lời nói), nhận xét chuyên môn, nhận xét phong thái, số từ đệm và câu trả lời mẫu chuẩn STAR của một câu hỏi.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "order_index": types.Schema(type=types.Type.INTEGER, description="Số thứ tự câu hỏi cần nhận xét (1, 2...)"),
                    },
                    required=["order_index"],
                ),
            )

            tools = [types.Tool(function_declarations=[query_time_func, get_summary_func, compare_func, critique_func])]

            # Chuẩn bị Global Context
            roles_str = ", ".join(global_summary.get("practiced_roles", [])) or "Chưa ghi nhận"
            recent_str = "\n".join([
                f"- ID: {s['id']} | Vị trí: {s['role_name']} | Điểm: {s['overall_score']} | Ngày: {s['created_at'][:10]}"
                for s in recent_sessions[:3]
            ]) or "Chưa có phiên hoàn thành nào."

            system_instruction = (
                "Bạn là AI Cố vấn Phỏng vấn Nhân sự Cao cấp (Senior Interview & HR Coach) tại InterviewLab. "
                "Nhiệm vụ: Cung cấp nhận xét, phân tích dữ liệu cảm xúc, phong thái và hướng dẫn kỹ năng phỏng vấn cho ứng viên một cách chuyên nghiệp, tích cực, số liệu thực chứng rõ ràng.\n\n"
                f"HỒ SƠ TỔNG HỢP CỦA ỨNG VIÊN (GLOBAL CONTEXT):\n"
                f"- Tổng số phiên phỏng vấn đã hoàn thành: {global_summary.get('total_sessions', 0)}\n"
                f"- Điểm số trung bình toàn diện: {global_summary.get('average_overall_score', 0)}/100\n"
                f"- Độ tự tin trung bình: {global_summary.get('average_confidence', 0)}%\n"
                f"- Độ căng thẳng trung bình: {global_summary.get('average_stress', 0)}%\n"
                f"- Các vị trí đã luyện tập: {roles_str}\n"
                f"- Các phiên gần nhất:\n{recent_str}\n"
                f"- Phiên đang xét (Active Session ID): {target_session or 'Chưa chọn'}\n\n"
                "QUY TẮC:\n"
                "1. Khi ứng viên hỏi về số liệu chi tiết, thời gian cụ thể (giây nào, phút nào), nhận xét transcript câu hỏi hoặc so sánh 2 câu, BẮT BUỘC gọi function thích hợp.\n"
                "2. Trả lời bằng tiếng Việt chuyên nghiệp, sử dụng định dạng Markdown rõ ràng, gạch đầu dòng, bảng số liệu nếu thích hợp.\n"
                "3. Kết thúc câu trả lời bằng một lời động viên súc tích hoặc gợi ý bước cải thiện tiếp theo."
            )

            # Định dạng lịch sử hội thoại
            history_text = ""
            if conversation_history:
                history_text = "\n".join([f"{h.get('role', 'user').upper()}: {h.get('content', '')}" for h in conversation_history[-6:]])

            prompt_content = f"LỊCH SỬ HỘI THOẠI TRƯỚC ĐÓ:\n{history_text}\n\nCÂU HỎI HIỆN TẠI CỦA ỨNG VIÊN:\n{user_message}"

            # Gọi Gemini lượt 1
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt_content,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=tools,
                    temperature=0.3,
                ),
            )

            # Xử lý Function Calling nếu model yêu cầu
            if response.function_calls:
                tool_call = response.function_calls[0]
                tool_name = tool_call.name
                tool_args = dict(tool_call.args)
                tools_used.append(tool_name)

                # Thực thi tool cục bộ trên DB
                tool_result = self._execute_local_tool(tool_name, tool_args, target_session or "", db)

                # Lượt 2: Gửi kết quả tool cho Gemini sinh phản hồi cuối cùng
                final_response = client.models.generate_content(
                    model=self.model_name,
                    contents=[
                        types.Part.from_text(f"Dữ liệu trích xuất từ database cho tool `{tool_name}`:\n{json.dumps(tool_result, ensure_ascii=False)}"),
                        types.Part.from_text(f"Dựa vào dữ liệu trên và ngữ cảnh của ứng viên, hãy trả lời câu hỏi: '{user_message}'"),
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.3,
                    ),
                )
                reply_text = final_response.text.strip()
            else:
                reply_text = response.text.strip()

            suggestions = self._extract_suggestions(reply_text, user_message, bool(target_session))
            return reply_text, suggestions, tools_used

        except Exception as e:  # noqa: BLE001
            logger.warning(f"Gemini API gặp lỗi: {e}. Tự động fallback sang Mock Engine.")
            return self._mock_advisor_chat(
                user_message=user_message,
                global_summary=global_summary,
                session_id=target_session,
                db=db,
            )

    async def chat(
        self,
        session_id: str,
        user_message: str,
        db: Session,
        force_mock: bool = False,
    ) -> dict[str, Any]:
        """
        Xử lý 1 câu hỏi từ người dùng trong màn hình kết quả phiên cụ thể:
        - Giữ nguyên tương thích với /api/sessions/{session_id}/chat.
        - Hỗ trợ đầy đủ 4 tools: thời gian, summary, so sánh, nhận xét câu.
        """
        self.add_turn(session_id, role="user", content=user_message)
        tools_used: list[str] = []

        if not self.api_key or force_mock:
            tool_name, tool_args = self._mock_intent_parser(user_message)
            tool_data = self._execute_local_tool(tool_name, tool_args, session_id, db)
            tools_used.append(tool_name)
            response_text = self._generate_mock_response(tool_name, tool_data, user_message)

            self.add_turn(session_id, role="assistant", content=response_text)
            return {
                "session_id": session_id,
                "response": response_text,
                "tools_used": tools_used,
                "is_mock": True,
                "timestamp": datetime.now(UTC).isoformat(),
            }

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)

            query_time_func = types.FunctionDeclaration(
                name="query_emotion_by_time",
                description="Truy vấn diễn biến cảm xúc trong khoảng thời gian cụ thể của một câu hỏi phỏng vấn.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "order_index": types.Schema(type=types.Type.INTEGER, description="Số thứ tự câu hỏi (1, 2, 3...)"),
                        "start_second": types.Schema(type=types.Type.INTEGER, description="Giây bắt đầu"),
                        "end_second": types.Schema(type=types.Type.INTEGER, description="Giây kết thúc"),
                    },
                    required=["order_index", "start_second", "end_second"],
                ),
            )

            get_summary_func = types.FunctionDeclaration(
                name="get_session_summary",
                description="Lấy báo cáo tổng hợp toàn bộ phiên phỏng vấn (tổng điểm, tự tin, stress).",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "include_timeline": types.Schema(type=types.Type.BOOLEAN, description="Kèm timeline chi tiết"),
                    },
                ),
            )

            compare_func = types.FunctionDeclaration(
                name="compare_questions",
                description="So sánh chỉ số cảm xúc và phong thái giữa 2 câu hỏi.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "question_a": types.Schema(type=types.Type.INTEGER, description="Số câu hỏi thứ nhất"),
                        "question_b": types.Schema(type=types.Type.INTEGER, description="Số câu hỏi thứ hai"),
                    },
                    required=["question_a", "question_b"],
                ),
            )

            critique_func = types.FunctionDeclaration(
                name="get_question_critique",
                description="Lấy chi tiết transcript (lời nói), nhận xét chuyên môn, phong thái và câu trả lời mẫu của một câu hỏi.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "order_index": types.Schema(type=types.Type.INTEGER, description="Số thứ tự câu hỏi (1, 2...)"),
                    },
                    required=["order_index"],
                ),
            )

            tools = [types.Tool(function_declarations=[query_time_func, get_summary_func, compare_func, critique_func])]

            history = self.get_history(session_id)
            history_text = "\n".join([f"{h['role'].upper()}: {h['content']}" for h in history[-6:]])

            system_instruction = (
                "Bạn là AI Chuyên gia Phỏng vấn Nhân sự (HR Interview Coach). "
                "Nhiệm vụ: Phân tích cảm xúc và phong thái của ứng viên một cách trung thực, có số liệu và hữu ích. "
                "Luôn gọi tools để lấy dữ liệu thực tế trước khi trả lời. Trả lời bằng tiếng Việt chuyên nghiệp."
            )

            response = client.models.generate_content(
                model=self.model_name,
                contents=f"{system_instruction}\n\nLỊCH SỬ HỘI THOẠI:\n{history_text}\n\nCÂU HỎI HIỆN TẠI:\n{user_message}",
                config=types.GenerateContentConfig(
                    tools=tools,
                    temperature=0.2,
                ),
            )

            if response.function_calls:
                tool_call = response.function_calls[0]
                tool_name = tool_call.name
                tool_args = dict(tool_call.args)
                tools_used.append(tool_name)

                tool_result = self._execute_local_tool(tool_name, tool_args, session_id, db)

                final_response = client.models.generate_content(
                    model=self.model_name,
                    contents=[
                        types.Part.from_text(f"Dữ liệu trích xuất từ hệ thống cho {tool_name}:\n{json.dumps(tool_result, ensure_ascii=False)}"),
                        types.Part.from_text(f"Dựa vào dữ liệu trên, hãy trả lời câu hỏi của ứng viên: '{user_message}'"),
                    ],
                )
                final_text = final_response.text.strip()
            else:
                final_text = response.text.strip()

            self.add_turn(session_id, role="assistant", content=final_text)
            return {
                "session_id": session_id,
                "response": final_text,
                "tools_used": tools_used,
                "is_mock": False,
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except Exception as e:  # noqa: BLE001
            logger.warning(f"Gemini API gặp sự cố: {e}. Chuyển sang Fallback Simulator.")
            tool_name, tool_args = self._mock_intent_parser(user_message)
            tool_data = self._execute_local_tool(tool_name, tool_args, session_id, db)
            tools_used.append(tool_name)
            fallback_text = self._generate_mock_response(tool_name, tool_data, user_message)
            self.add_turn(session_id, role="assistant", content=fallback_text)
            return {
                "session_id": session_id,
                "response": fallback_text,
                "tools_used": tools_used,
                "is_mock": True,
                "fallback_reason": str(e),
                "timestamp": datetime.now(UTC).isoformat(),
            }

