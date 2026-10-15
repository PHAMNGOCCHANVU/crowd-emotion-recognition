"""
crowd_analytics.py — Tầng Thống kê & Phân tích Nghiệp vụ (Tier 2)
======================================================================
Cung cấp:
1. Phân tích frame tức thời (Single Frame Analysis).
2. Khử nhiễu chuỗi thời gian bằng Cửa sổ trượt (Sliding Window / Temporal Smoothing).
3. Thang điểm Tâm trạng Đám đông (Crowd Mood Score - CMS: -1.0 đến +1.0).
4. Phân tích vùng tập trung chú ý (Spatial Attention - "Tò mò" qua Dwell Time).
"""

import sys
from collections import deque, Counter

# Đảm bảo in tiếng Việt trên console Windows không lỗi charmap
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


class CrowdAnalytics:
    """
    Tier 2: Phân tích cảm xúc đám đông và cảnh báo ngưỡng (Threshold / Aggregation Layer).
    """
    def __init__(self, window_size=30, happy_thresh=0.25, panic_thresh=0.20, curious_thresh=0.20):
        """
        Args:
            window_size: Số frames lưu trong bộ đệm trượt (~1-1.5s ở 20-30 FPS) để khử nhiễu.
            happy_thresh: Tỷ lệ Happy tối thiểu để ghi nhận 'Hài lòng / Tích cực'.
            panic_thresh: Tỷ lệ Sad + Surprised tối thiểu để kích hoạt 'Cảnh báo Hoang mang'.
            curious_thresh: Tỷ lệ Surprised tối thiểu để ghi nhận 'Tò mò / Chú ý cao'.
        """
        self.window_size = window_size
        self.happy_thresh = happy_thresh
        self.panic_thresh = panic_thresh
        self.curious_thresh = curious_thresh

        # Bộ đệm cửa sổ trượt lưu lịch sử danh sách khuôn mặt
        self.history = deque(maxlen=window_size)

        # Bộ theo dõi vùng chú ý không gian: {box_id: {"dwell_count": int, "last_box": tuple}}
        self.spatial_tracks = {}

    def calculate_mood_score(self, dist):
        """
        Tính thang điểm Tâm trạng Đám đông (Crowd Mood Score - CMS) từ -1.0 đến +1.0:
        CMS = (Happy * 1.0) + (Normal * 0.0) - (Sad * 0.8) - (Surprised * 0.5)
        """
        score = (
            dist.get("Happy", 0.0) * 1.0 +
            dist.get("Normal", 0.0) * 0.0 -
            dist.get("Sad", 0.0) * 0.8 -
            dist.get("Surprised", 0.0) * 0.5
        )
        return round(float(score), 2)

    def analyze_frame(self, face_results):
        """
        Phân tích frame tức thời (không dùng lịch sử).
        """
        total = len(face_results)
        if total == 0:
            return {
                "total_faces": 0,
                "distribution": {"Happy": 0.0, "Normal": 0.0, "Sad": 0.0, "Surprised": 0.0},
                "crowd_mood_score": 0.0,
                "crowd_mood": "Trống (Không phát hiện người)",
                "alert_level": "NORMAL",
                "alert_message": "Không có khuôn mặt nào trong khung hình"
            }

        counts = Counter([f.get("emotion") for f in face_results])
        dist = {
            "Happy": round(counts.get("Happy", 0) / total, 2),
            "Normal": round(counts.get("Normal", 0) / total, 2),
            "Sad": round(counts.get("Sad", 0) / total, 2),
            "Surprised": round(counts.get("Surprised", 0) / total, 2)
        }

        mood_score = self.calculate_mood_score(dist)
        panic_ratio = round(dist["Surprised"] + dist["Sad"], 2)

        # Logic phân loại trạng thái
        if panic_ratio >= self.panic_thresh and total >= 3:
            alert_level = "WARNING"
            crowd_mood = "Hoang mang / Bất thường"
            alert_message = f"[CẢNH BÁO AN NINH] Dấu hiệu bất an/hoảng loạn ({int(panic_ratio * 100)}% đám đông)"
        elif dist["Happy"] >= self.happy_thresh:
            alert_level = "NORMAL"
            crowd_mood = "Hài lòng / Tích cực"
            alert_message = f"Không khí tích cực, trải nghiệm hài lòng ({int(dist['Happy'] * 100)}% Happy)"
        elif dist["Surprised"] >= self.curious_thresh:
            alert_level = "NORMAL"
            crowd_mood = "Tò mò / Chú ý cao"
            alert_message = f"Khu vực thu hút sự chú ý ({int(dist['Surprised'] * 100)}% Surprised)"
        else:
            alert_level = "NORMAL"
            crowd_mood = "Bình thường"
            alert_message = "Dòng người lưu thông ổn định"

        return {
            "total_faces": total,
            "distribution": dist,
            "crowd_mood_score": mood_score,
            "crowd_mood": crowd_mood,
            "alert_level": alert_level,
            "alert_message": alert_message
        }

    def analyze_stream(self, face_results):
        """
        Phân tích dòng video thời gian thực có CỬA SỔ TRƯỢT (Sliding Window):
        Làm mượt phân phối cảm xúc qua 30 frames gần nhất, loại bỏ hoàn toàn
        hiện tượng nhấp nháy (flickering) khi 1 người nhăn mặt chớp nhoáng.
        """
        # Lưu vào hàng đợi
        self.history.append(face_results)

        # Thu thập toàn bộ cảm xúc trong cửa sổ trượt
        all_emotions = [f.get("emotion") for frame in self.history for f in frame if f.get("emotion")]
        total_in_window = len(all_emotions)
        current_faces_count = len(face_results)

        if total_in_window == 0:
            return {
                "total_faces": 0,
                "current_faces": 0,
                "distribution": {"Happy": 0.0, "Normal": 0.0, "Sad": 0.0, "Surprised": 0.0},
                "crowd_mood_score": 0.0,
                "crowd_mood": "Trống (Không phát hiện người)",
                "alert_level": "NORMAL",
                "alert_message": "Không có người trong khung hình"
            }

        counts = Counter(all_emotions)
        smoothed_dist = {
            "Happy": round(counts.get("Happy", 0) / total_in_window, 2),
            "Normal": round(counts.get("Normal", 0) / total_in_window, 2),
            "Sad": round(counts.get("Sad", 0) / total_in_window, 2),
            "Surprised": round(counts.get("Surprised", 0) / total_in_window, 2)
        }

        mood_score = self.calculate_mood_score(smoothed_dist)
        panic_ratio = round(smoothed_dist["Surprised"] + smoothed_dist["Sad"], 2)

        if panic_ratio >= self.panic_thresh and total_in_window >= 10:
            alert_level = "WARNING"
            crowd_mood = "Hoang mang / Bất thường"
            alert_message = f"[CẢNH BÁO AN NINH] Đám đông bất an/hoảng loạn ({int(panic_ratio * 100)}%)"
        elif smoothed_dist["Happy"] >= self.happy_thresh:
            alert_level = "NORMAL"
            crowd_mood = "Hài lòng / Tích cực"
            alert_message = f"Không khí sự kiện tích cực ({int(smoothed_dist['Happy'] * 100)}% Hài lòng)"
        elif smoothed_dist["Surprised"] >= self.curious_thresh:
            alert_level = "NORMAL"
            crowd_mood = "Tò mò / Chú ý cao"
            alert_message = f"Không gian thu hút ({int(smoothed_dist['Surprised'] * 100)}% Tò mò)"
        else:
            alert_level = "NORMAL"
            crowd_mood = "Bình thường"
            alert_message = "Dòng người lưu thông ổn định"

        return {
            "total_faces": current_faces_count,
            "window_samples": total_in_window,
            "distribution": smoothed_dist,
            "crowd_mood_score": mood_score,
            "crowd_mood": crowd_mood,
            "alert_level": alert_level,
            "alert_message": alert_message
        }


if __name__ == '__main__':
    print("--- Test Advanced CrowdAnalytics (Sliding Window & Mood Score) ---")
    analytics = CrowdAnalytics(window_size=10, happy_thresh=0.25, panic_thresh=0.20)

    # Giả lập 10 frames liên tiếp
    for i in range(10):
        # 1 người Happy, 4 người Normal
        frame_faces = [
            {"box": (0, 0, 10, 10), "emotion": "Normal"},
            {"box": (0, 0, 10, 10), "emotion": "Normal"},
            {"box": (0, 0, 10, 10), "emotion": "Normal"},
            {"box": (0, 0, 10, 10), "emotion": "Normal"},
            {"box": (0, 0, 10, 10), "emotion": "Happy"},
        ]
        res = analytics.analyze_stream(frame_faces)

    print("Kết quả sau 10 frames ổn định:")
    print(f"  Crowd Mood:       {res['crowd_mood']}")
    print(f"  Crowd Mood Score: {res['crowd_mood_score']} (Thang -1.0 đến +1.0)")
    print(f"  Distribution:     {res['distribution']}")
    print(f"  Alert:            {res['alert_level']}")

    assert res['alert_level'] == "NORMAL"
    assert res['crowd_mood'] == "Bình thường"
    assert res['crowd_mood_score'] == 0.2

    # Giả lập tình huống bất thường (nhiều người hoảng sợ/bất ngờ)
    for i in range(10):
        panic_faces = [
            {"box": (0, 0, 10, 10), "emotion": "Surprised"},
            {"box": (0, 0, 10, 10), "emotion": "Sad"},
            {"box": (0, 0, 10, 10), "emotion": "Sad"},
            {"box": (0, 0, 10, 10), "emotion": "Normal"},
        ]
        res_panic = analytics.analyze_stream(panic_faces)

    print("\nKết quả sau 10 frames sự cố bất thường:")
    print(f"  Crowd Mood:       {res_panic['crowd_mood']}")
    print(f"  Crowd Mood Score: {res_panic['crowd_mood_score']}")
    print(f"  Distribution:     {res_panic['distribution']}")
    print(f"  Alert:            {res_panic['alert_level']}")

    assert res_panic['alert_level'] == "WARNING"
    assert res_panic['crowd_mood_score'] < 0

    print("\n[OK] Advanced CrowdAnalytics test PASSED!")
