from collections import Counter


class CrowdAnalytics:
    """Aggregate per-face predictions into crowd mood and alert metrics."""

    def __init__(self, happy_thresh=0.25, panic_thresh=0.20, curious_thresh=0.20):
        self.happy_thresh = happy_thresh
        self.panic_thresh = panic_thresh
        self.curious_thresh = curious_thresh

    def analyze_frame(self, face_results):
        total = len(face_results)
        if total == 0:
            return {
                "total_faces": 0,
                "distribution": {name: 0.0 for name in ("Happy", "Normal", "Sad", "Surprised")},
                "crowd_mood": "Trống (Không phát hiện người)",
                "alert_level": "NORMAL",
                "alert_message": "Không có khuôn mặt nào trong khung hình",
            }

        counts = Counter(face.get("emotion") for face in face_results)
        distribution = {
            name: round(counts.get(name, 0) / total, 2)
            for name in ("Happy", "Normal", "Sad", "Surprised")
        }
        alert_level = "NORMAL"
        alert_message = "Dòng người lưu thông ổn định"
        crowd_mood = "Bình thường"
        panic_ratio = distribution["Sad"] + distribution["Surprised"]

        if panic_ratio >= self.panic_thresh and total >= 3:
            alert_level = "WARNING"
            crowd_mood = "Hoang mang / Bất thường"
            alert_message = f"Tỷ lệ Sad/Surprised cao ({panic_ratio:.0%})"
        elif distribution["Happy"] >= self.happy_thresh:
            crowd_mood = "Hài lòng / Tích cực"
            alert_message = f"Không khí tích cực ({distribution['Happy']:.0%} Happy)"
        elif distribution["Surprised"] >= self.curious_thresh:
            crowd_mood = "Tò mò / Chú ý cao"
            alert_message = f"Tỷ lệ Surprised cao ({distribution['Surprised']:.0%})"

        return {
            "total_faces": total,
            "distribution": distribution,
            "crowd_mood": crowd_mood,
            "alert_level": alert_level,
            "alert_message": alert_message,
        }
