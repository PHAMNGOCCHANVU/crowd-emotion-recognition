"""
interview_analytics.py — Phân tích Cảm xúc & Phong thái Ứng viên Phỏng vấn (6 Nhãn)
===================================================================================
Module phân tích chuỗi cảm xúc cá nhân của ứng viên qua từng giây trả lời phỏng vấn:
1. Confidence Score (Chỉ số Tự tin): Tỷ lệ biểu cảm tích cực & điềm tĩnh (Normal, Happy),
   trừ điểm các biểu cảm lo âu/tiêu cực (Fear, Sad, Contempt, Surprised).
2. Stress Score (Chỉ số Căng thẳng): Chỉ báo áp lực tâm lý mạnh (Fear, Sad, Contempt).
3. Emotion Timeline: Chuỗi diễn biến cảm xúc 6 nhãn theo từng giây phục vụ video replay và chatbot.
"""

from collections import Counter
from typing import List, Dict, Any

EMOTION_CLASSES = ["Contempt", "Fear", "Happy", "Normal", "Sad", "Surprised"]


class InterviewEmotionAnalytics:
    """
    Phân tích phong thái phỏng vấn từ chuỗi kết quả nhận diện khuôn mặt từng frame.
    """

    def __init__(self, fps: float = 25.0):
        self.fps = fps

    def analyze_interview_sequence(
        self, frame_predictions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Phân tích chuỗi cảm xúc của toàn bộ video câu trả lời.

        Args:
            frame_predictions: Danh sách kết quả theo frame:
                [{"frame_idx": int, "emotion": str, "confidence": float}, ...]

        Returns:
            dict chứa:
                - confidence_score: float (0.0 - 100.0)
                - stress_score: float (0.0 - 100.0)
                - dominant_emotion: str
                - emotion_distribution: dict (đủ 6 nhãn)
                - emotion_timeline: List[dict] (tổng hợp theo từng giây)
        """
        if not frame_predictions:
            return {
                "confidence_score": 50.0,
                "stress_score": 0.0,
                "dominant_emotion": "Normal",
                "emotion_distribution": {emo: (1.0 if emo == "Normal" else 0.0) for emo in EMOTION_CLASSES},
                "emotion_timeline": [],
            }

        total_frames = len(frame_predictions)
        emotions = [p.get("emotion", "Normal") for p in frame_predictions]
        counts = Counter(emotions)

        dist = {
            label: round(counts.get(label, 0) / total_frames, 4)
            for label in EMOTION_CLASSES
        }

        # 1. Tính Confidence Score (0 - 100%)
        # Tự tin = Normal (điềm đạm) * 85 + Happy (tươi cười) * 100 - trừ Fear/Sad/Contempt/Surprised
        raw_conf = (
            dist["Normal"] * 85.0
            + dist["Happy"] * 100.0
            - dist["Fear"] * 50.0
            - dist["Sad"] * 40.0
            - dist["Contempt"] * 25.0
            - dist["Surprised"] * 15.0
        )
        confidence_score = max(10.0, min(98.0, raw_conf))

        # 2. Tính Stress Score (0 - 100%)
        # Căng thẳng = Fear (150%) + Sad (120%) + Contempt (60%) + Surprised (30%)
        raw_stress = (
            dist["Fear"] * 1.5
            + dist["Sad"] * 1.2
            + dist["Contempt"] * 0.6
            + dist["Surprised"] * 0.3
        ) * 100.0
        stress_score = max(0.0, min(100.0, raw_stress))

        # 3. Tổng hợp Emotion Timeline theo từng giây (mỗi giây gồm ~fps frames)
        frames_per_sec = int(self.fps) if self.fps > 0 else 25
        timeline = []

        total_seconds = (total_frames + frames_per_sec - 1) // frames_per_sec
        for sec in range(total_seconds):
            sec_start = sec * frames_per_sec
            sec_end = min(total_frames, (sec + 1) * frames_per_sec)
            sec_frames = frame_predictions[sec_start:sec_end]
            if not sec_frames:
                continue

            sec_emotions = [f.get("emotion", "Normal") for f in sec_frames]
            sec_confidences = [f.get("confidence", 0.8) for f in sec_frames]
            most_common_emo = Counter(sec_emotions).most_common(1)[0][0]
            avg_conf = sum(sec_confidences) / len(sec_confidences)

            # Đánh dấu cờ stress khi cảm xúc là Fear (lo âu), Sad (buồn bã) hoặc Contempt (khó chịu)
            is_stress = most_common_emo in ["Fear", "Sad", "Contempt"]

            timeline.append(
                {
                    "second": sec + 1,
                    "emotion": most_common_emo,
                    "confidence": round(avg_conf, 2),
                    "is_stress": is_stress,
                }
            )

        dominant_emotion = max(dist, key=dist.get)

        return {
            "confidence_score": round(confidence_score, 1),
            "stress_score": round(stress_score, 1),
            "dominant_emotion": dominant_emotion,
            "emotion_distribution": dist,
            "emotion_timeline": timeline,
        }
