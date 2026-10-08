import os
import json
from typing import Dict, Any


def evaluate_interview_answer_llm(
    question_text: str,
    transcript: str,
    confidence_score: float,
    stress_score: float,
    filler_words_count: int,
    role_name: str = "Software Engineer",
) -> Dict[str, Any]:
    """
    Sử dụng Google Gemini Flash API để chấm điểm câu trả lời và nhận xét đa phương thức.
    """
    gemini_key = os.getenv("GEMINI_API_KEY")

    if not gemini_key:
        # Fallback Mock evaluation khi chưa nạp API key
        return {
            "content_score": 85.0,
            "content_critique": (
                "Câu trả lời đi đúng trọng tâm câu hỏi, có cấu trúc mở-thân-kết rõ ràng. "
                "Ứng viên đã thể hiện được tư duy giải quyết vấn đề logic."
            ),
            "delivery_critique": (
                f"Chỉ số tự tin đạt {confidence_score}%. Phong thái nhìn chung điềm tĩnh. "
                f"Cần chú ý giảm bớt {filler_words_count} từ ngập ngừng để lời nói dứt khoát hơn."
            ),
            "suggested_answer": (
                "Bạn có thể bổ sung thêm ví dụ định lượng cụ thể (như: 'đã giúp cải thiện 25% hiệu năng') "
                "để tăng tính thuyết phục cho nhà tuyển dụng."
            ),
        }

    try:
        from google import genai
        client = genai.Client(api_key=gemini_key)

        prompt = f"""
Bạn là chuyên gia phỏng vấn tuyển dụng hàng đầu cho vị trí: {role_name}.
Hãy đánh giá câu trả lời sau đây dựa trên thông tin đa phương thức:
- Câu hỏi phỏng vấn: "{question_text}"
- Bản bóc băng câu trả lời của ứng viên: "{transcript}"
- Chỉ số Tự tin từ biểu cảm khuôn mặt (FER): {confidence_score}/100
- Chỉ số Căng thẳng từ khuôn mặt: {stress_score}/100
- Số từ đệm ấp úng ("ừm", "à"): {filler_words_count}

Yêu cầu trả về DUY NHẤT một chuỗi JSON hợp lệ không chứa markdown backticks, theo cấu trúc:
{{
    "content_score": <float từ 0 đến 100>,
    "content_critique": "<nhận xét chuyên môn, logic, phương pháp STAR>",
    "delivery_critique": "<nhận xét phong thái, độ tự tin, biểu cảm khuôn mặt và từ đệm>",
    "suggested_answer": "<câu trả lời mẫu ngắn gọn, tối ưu cho câu hỏi này>"
}}
"""
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
        )
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]

        parsed = json.loads(raw_text.strip())
        return {
            "content_score": float(parsed.get("content_score", 80.0)),
            "content_critique": str(parsed.get("content_critique", "")),
            "delivery_critique": str(parsed.get("delivery_critique", "")),
            "suggested_answer": str(parsed.get("suggested_answer", "")),
        }
    except Exception as e:
        print(f"[LLM Service Error] Gemini API lỗi: {e}. Dùng fallback evaluation.")
        return {
            "content_score": 80.0,
            "content_critique": "Câu trả lời tương đối đầy đủ ý chính.",
            "delivery_critique": f"Chỉ số tự tin: {confidence_score}%.",
            "suggested_answer": "Nên luyện tập thêm để trả lời mạch lạc và ngắn gọn hơn.",
        }
