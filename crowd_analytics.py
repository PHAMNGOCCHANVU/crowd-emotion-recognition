import sys
from collections import Counter

# Đảm bảo in tiếng Việt trên console Windows không lỗi charmap
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass



class CrowdAnalytics:
    """
    Tier 2: Phân tích cảm xúc đám đông và cảnh báo ngưỡng (Threshold / Aggregation Layer).
    Nhận kết quả biểu cảm của từng cá nhân trong frame và suy luận ra:
    - Mức độ Hài lòng (Đánh giá trải nghiệm sự kiện)
    - Cảnh báo An ninh (Phát hiện hoang mang, bất thường, hoảng loạn)
    - Mức độ Tò mò / Chú ý cao (Thu hút vào không gian/biển quảng cáo)
    - Trạng thái Bình thường / Ổn định
    """
    def __init__(self, happy_thresh=0.25, panic_thresh=0.20, curious_thresh=0.20):
        """
        Args:
            happy_thresh: Tỷ lệ Happy tối thiểu để ghi nhận không khí 'Hài lòng' (mặc định 25%).
            panic_thresh: Tỷ lệ Sad + Surprised tối thiểu để kích hoạt 'Cảnh báo Hoang mang' (mặc định 20%).
            curious_thresh: Tỷ lệ Surprised tối thiểu để ghi nhận 'Tò mò / Chú ý cao' (mặc định 20%).
        """
        self.happy_thresh = happy_thresh
        self.panic_thresh = panic_thresh
        self.curious_thresh = curious_thresh

    def analyze_frame(self, face_results):
        """
        Args:
            face_results: list các dict:
                [{"box": (x1,y1,x2,y2), "emotion": str, "confidence": float}, ...]
        Returns:
            dict chứa:
                - total_faces: Tổng số khuôn mặt nhận diện được
                - distribution: Phân phối % của 4 nhãn chuẩn
                - crowd_mood: Trạng thái tổng quát của đám đông
                - alert_level: "NORMAL" hoặc "WARNING"
                - alert_message: Thông báo diễn giải
        """
        total = len(face_results)
        if total == 0:
            return {
                "total_faces": 0,
                "distribution": {"Happy": 0.0, "Normal": 0.0, "Sad": 0.0, "Surprised": 0.0},
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

        # Thuật toán đánh giá ngưỡng trạng thái đám đông
        alert_level = "NORMAL"
        alert_message = "Dòng người lưu thông ổn định"
        crowd_mood = "Bình thường"

        # 1. ƯU TIÊN CAO NHẤT: Cảnh báo An ninh (Hoang mang / Bất an)
        # Khi có từ 3 người trở lên và tỷ lệ Surprised/Sad tăng vượt ngưỡng
        panic_ratio = round(dist["Surprised"] + dist["Sad"], 2)
        if panic_ratio >= self.panic_thresh and total >= 3:
            alert_level = "WARNING"
            crowd_mood = "Hoang mang / Bất thường"
            alert_message = f"[CANH BAO AN NINH] Ty le bat an/hoang loan cao ({int(panic_ratio * 100)}% dam dong)"

        # 2. Đánh giá Trải nghiệm sự kiện (Hài lòng)
        elif dist["Happy"] >= self.happy_thresh:
            crowd_mood = "Hài lòng / Tích cực"
            alert_message = f"Khong khi tich cuc, trai nghiem hai long ({int(dist['Happy'] * 100)}% Happy)"

        # 3. Đánh giá Mức độ Thu hút (Tò mò / Chú ý cao)
        elif dist["Surprised"] >= self.curious_thresh:
            crowd_mood = "Tò mò / Chú ý cao"
            alert_message = f"Khu vuc thu hut su chu y cao ({int(dist['Surprised'] * 100)}% Surprised)"

        return {
            "total_faces": total,
            "distribution": dist,
            "crowd_mood": crowd_mood,
            "alert_level": alert_level,
            "alert_message": alert_message
        }


if __name__ == '__main__':
    print("--- Test CrowdAnalytics ---")
    analytics = CrowdAnalytics()

    # Case 1: Đám đông bình thường (Normal chiếm đa số)
    case1 = [
        {"box": (0,0,10,10), "emotion": "Normal", "confidence": 0.90},
        {"box": (0,0,10,10), "emotion": "Normal", "confidence": 0.85},
        {"box": (0,0,10,10), "emotion": "Normal", "confidence": 0.88},
        {"box": (0,0,10,10), "emotion": "Normal", "confidence": 0.82},
        {"box": (0,0,10,10), "emotion": "Happy", "confidence": 0.75},
    ]
    res1 = analytics.analyze_frame(case1)
    print(f"Case 1 (Normal): Mood='{res1['crowd_mood']}', Alert={res1['alert_level']}")
    assert res1['alert_level'] == "NORMAL" and "Bình thường" in res1['crowd_mood']

    # Case 2: Đám đông có sự cố hoang mang
    case2 = [
        {"box": (0,0,10,10), "emotion": "Surprised", "confidence": 0.88},
        {"box": (0,0,10,10), "emotion": "Sad", "confidence": 0.75},
        {"box": (0,0,10,10), "emotion": "Normal", "confidence": 0.80},
        {"box": (0,0,10,10), "emotion": "Normal", "confidence": 0.82},
    ]
    res2 = analytics.analyze_frame(case2)
    print(f"Case 2 (Panic):  Mood='{res2['crowd_mood']}', Alert={res2['alert_level']}")
    assert res2['alert_level'] == "WARNING"

    # Case 3: Đám đông hài lòng
    case3 = [
        {"box": (0,0,10,10), "emotion": "Happy", "confidence": 0.95},
        {"box": (0,0,10,10), "emotion": "Happy", "confidence": 0.91},
        {"box": (0,0,10,10), "emotion": "Normal", "confidence": 0.85},
    ]
    res3 = analytics.analyze_frame(case3)
    print(f"Case 3 (Happy):  Mood='{res3['crowd_mood']}', Alert={res3['alert_level']}")
    assert "Hài lòng" in res3['crowd_mood']

    print("[OK] CrowdAnalytics test PASSED!")

