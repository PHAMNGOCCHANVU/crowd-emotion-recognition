"""
chatbot_service.py — Hybrid Chatbot Service (Gemini Function Calling + Mock Mode)
================================================================================
Quản lý hội thoại thông minh giữa Ứng viên và AI Coach:
- Hỗ trợ Gemini Function Calling khi có GEMINI_API_KEY.
- Hỗ trợ Chế độ Giả lập (Mock Mode / Fallback Simulator) để kiểm thử toàn diện
  mà KHÔNG tốn chi phí và không cần API Key thật.
- Lưu trữ Conversation Memory (bộ nhớ nhiều lượt thoại).
"""

import os
import re
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from .temporal_query import (
    query_emotion_by_time,
    get_session_summary,
    compare_questions,
)


class ChatbotService:
    """
    Service Chatbot Hybrid:
    Tích hợp Gemini Tool Calling + Local Temporal Query Engine + Conversation Memory.
    """

    def __init__(self, api_key: Optional[str] = None, max_history_turns: int = 15):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.max_history_turns = max_history_turns
        # Lưu trữ hội thoại in-memory theo session_id: {session_id: [{"role": str, "content": str, "timestamp": str}]}
        self.memory: Dict[str, List[Dict[str, str]]] = {}

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Lấy danh sách các lượt thoại trước đó của phiên."""
        return self.memory.get(session_id, [])

    def add_turn(self, session_id: str, role: str, content: str):
        """Thêm 1 lượt thoại mới vào bộ nhớ hội thoại."""
        if session_id not in self.memory:
            self.memory[session_id] = []
        self.memory[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
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
        tool_args: Dict[str, Any],
        session_id: str,
        db: Session,
    ) -> Dict[str, Any]:
        """Thực thi tool cục bộ dựa trên yêu cầu function calling hoặc mock router."""
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

        return {"error": f"Tool '{tool_name}' không được hỗ trợ."}

    def _mock_intent_parser(self, message: str) -> tuple[str, Dict[str, Any]]:
        """
        Parser dự phòng giả lập: Tự động trích xuất ý định và tham số
        từ câu hỏi của người dùng khi chưa có API Key.
        """
        msg_lower = message.lower()

        # 1. Kiểm tra so sánh 2 câu: ví dụ "so sánh câu 1 và câu 3", "câu 1 vs câu 2"
        compare_match = re.search(r"(?:so sánh|so|vs).*?câu\s*(\d+).*?(?:và|với|vs|,)\s*câu\s*(\d+)", msg_lower)
        if compare_match:
            qa, qb = int(compare_match.group(1)), int(compare_match.group(2))
            return "compare_questions", {"question_a": qa, "question_b": qb}

        # 2. Kiểm tra truy vấn thời gian:
        # Ví dụ: "giây 10 đến 25 câu 1", "từ 00:10 đến 00:30 ở câu hỏi 2", "ở câu 2 lúc giây 15 đến 30"
        order_match = re.search(r"câu(?:\s*hỏi)?\s*(\d+)", msg_lower)
        order_idx = int(order_match.group(1)) if order_match else 1

        # Mẫu 1: mm:ss đến mm:ss
        time_mm_ss = re.search(r"(\d{1,2}):(\d{2})\s*(?:đến|-|tới)\s*(\d{1,2}):(\d{2})", msg_lower)
        if time_mm_ss:
            s_sec = int(time_mm_ss.group(1)) * 60 + int(time_mm_ss.group(2))
            e_sec = int(time_mm_ss.group(3)) * 60 + int(time_mm_ss.group(4))
            return "query_emotion_by_time", {"order_index": order_idx, "start_second": s_sec, "end_second": e_sec}

        # Mẫu 2: từ (giây) X đến (giây) Y
        time_range = re.search(r"(?:từ\s*)?(?:giây\s*)?(\d+)\s*(?:đến|-|tới)\s*(?:giây\s*)?(\d+)", msg_lower)
        if time_range and ("giây" in msg_lower or "khoảng" in msg_lower or "lúc" in msg_lower or "từ" in msg_lower):
            s_sec, e_sec = int(time_range.group(1)), int(time_range.group(2))
            return "query_emotion_by_time", {"order_index": order_idx, "start_second": s_sec, "end_second": e_sec}

        # 3. Kiểm tra tổng kết phiên:
        summary_keywords = ["tổng kết", "tổng quan", "tóm tắt", "toàn bộ", "buổi phỏng vấn", "overall"]
        if any(kw in msg_lower for kw in summary_keywords):
            return "get_session_summary", {"include_timeline": False}

        # Mặc định: Nếu câu hỏi có nhắc đến câu X mà không rõ giây -> xem summary câu đó hoặc cả phiên
        return "get_session_summary", {"include_timeline": False}

    def _generate_mock_response(
        self,
        tool_name: str,
        tool_data: Dict[str, Any],
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

            # Đánh giá sắc thái
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

        return "Cảm ơn bạn đã hỏi. Tôi luôn sẵn sàng hỗ trợ phân tích buổi phỏng vấn của bạn!"

    async def chat(
        self,
        session_id: str,
        user_message: str,
        db: Session,
        force_mock: bool = False,
    ) -> Dict[str, Any]:
        """
        Xử lý 1 câu hỏi từ người dùng:
        - Tự động gọi MockEngine nếu chưa cấu hình GEMINI_API_KEY hoặc force_mock=True.
        - Tự động gọi Gemini Function Calling khi có API Key.
        """
        self.add_turn(session_id, role="user", content=user_message)
        tools_used: List[str] = []

        # Chế độ Mock / Fallback Simulator
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
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Chế độ Production với Gemini API Key
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)

            # Khai báo schema tools cho Gemini
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

            tools = [types.Tool(function_declarations=[query_time_func, get_summary_func, compare_func])]

            # Lắp lịch sử hội thoại vào prompt
            history = self.get_history(session_id)
            history_text = "\n".join([f"{h['role'].upper()}: {h['content']}" for h in history[-6:]])

            system_instruction = (
                "Bạn là AI Chuyên gia Phỏng vấn Nhân sự (HR Interview Coach). "
                "Nhiệm vụ: Phân tích cảm xúc và phong thái của ứng viên một cách trung thực, có số liệu và hữu ích. "
                "Luôn gọi tools để lấy dữ liệu thực tế trước khi trả lời. Trả lời bằng tiếng Việt chuyên nghiệp."
            )

            # Gọi Gemini với Function Calling
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=f"{system_instruction}\n\nLỊCH SỬ HỘI THOẠI:\n{history_text}\n\nCÂU HỎI HIỆN TẠI:\n{user_message}",
                config=types.GenerateContentConfig(
                    tools=tools,
                    temperature=0.2,
                ),
            )

            # Kiểm tra xem Gemini có yêu cầu gọi Tool không
            if response.function_calls:
                tool_call = response.function_calls[0]
                tool_name = tool_call.name
                tool_args = dict(tool_call.args)
                tools_used.append(tool_name)

                # Thực thi tool cục bộ trên DB
                tool_result = self._execute_local_tool(tool_name, tool_args, session_id, db)

                # Gửi kết quả tool lại cho Gemini sinh câu trả lời tự nhiên
                final_response = client.models.generate_content(
                    model="gemini-1.5-flash",
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
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            print(f"[ChatbotService Warning] Gemini API gặp sự cố: {e}. Chuyển sang Fallback Simulator.")
            # Fallback an toàn về Mock Engine
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
                "timestamp": datetime.utcnow().isoformat(),
            }
