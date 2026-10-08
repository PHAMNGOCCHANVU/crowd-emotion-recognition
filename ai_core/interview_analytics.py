"""
interview_analytics.py — Phân tích Cảm xúc & Phong thái Ứng viên Phỏng vấn
=============================================================================
Refactor từ crowd_analytics.py:
Thay vì thống kê đám đông CCTV, module này phân tích chuỗi cảm xúc cá nhân của
ứng viên qua từng giây trả lời phỏng vấn để tính toán:
1. Confidence Score (Chỉ số Tự tin): Tỷ lệ biểu cảm tích cực & bình thản.
2. Stress Score (Chỉ số Căng thẳng): Tỷ lệ nét mặt lo âu, nhăn nhó, sợ sệt.
3. Emotion Timeline: Chuỗi diễn biến cảm xúc theo giây để đồng bộ video replay.
"""

from collections import Counter
from typing import List, Dict, Any


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
                - emotion_distribution: dict
                - emotion_timeline: List[dict] (tổng hợp theo từng giây)
        """
        if not frame_predictions:
            return {
                "confidence_score": 50.0,
                "stress_score": 0.0,
                "dominant_emotion": "Normal",
                "emotion_distribution": {
                    "Happy": 0.0,
                    "Normal": 1.0,
                    "Sad": 0.0,
                    "Surprised": 0.0,
                },
                "emotion_timeline": [],
            }

        total_frames = len(frame_predictions)
        emotions = [p.get("emotion", "Normal") for p in frame_predictions]
        counts = Counter(emotions)

        dist = {
            "Happy": round(counts.get("Happy", 0) / total_frames, 4),
            "Normal": round(counts.get("Normal", 0) / total_frames, 4),
            "Sad": round(counts.get("Sad", 0) / total_frames, 4),
            "Surprised": round(counts.get("Surprised", 0) / total_frames, 4),
        }

        # 1. Tính Confidence Score (0 - 100%)
        # Tự tin = Tỷ lệ Normal (điềm đạm) * 0.8 + Happy (tươi cười) * 1.0 - phạt Sad/Surprised
        raw_conf = (
            dist["Normal"] * 85.0
            + dist["Happy"] * 100.0
            - dist["Sad"] * 40.0
            - dist["Surprised"] * 30.0
        )
        confidence_score = max(10.0, min(98.0, raw_conf))

        # 2. Tính Stress Score (0 - 100%)
        # Căng thẳng = Sad * 70% + Surprised * 30%
        raw_stress = (dist["Sad"] * 1.2 + dist["Surprised"] * 0.8) * 100.0
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

            is_stress = most_common_emo in ["Sad", "Surprised"]

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
