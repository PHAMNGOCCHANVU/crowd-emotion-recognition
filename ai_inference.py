"""
ai_inference.py — Interface chuẩn bàn giao cho Team UI (Thành viên E)
======================================================================
Thành viên E chỉ cần import hàm `predict_emotion_from_frame` và gọi trong vòng lặp đọc camera/video:

    from ai_inference import predict_emotion_from_frame
    result = predict_emotion_from_frame(frame)

Định dạng trả về (2 tầng):
    {
        "faces": [
            {"box": (x1, y1, x2, y2), "emotion": "Happy", "confidence": 0.88},
            ...
        ],
        "crowd_insights": {
            "total_faces": 2,
            "distribution": {"Happy": 0.5, "Normal": 0.5, "Sad": 0.0, "Surprised": 0.0},
            "crowd_mood": "Hài lòng / Tích cực",
            "alert_level": "NORMAL", # hoặc "WARNING"
            "alert_message": "Không gian tích cực, dòng người hài lòng"
        }
    }
"""

import sys
import os
import cv2 as cv
import torch
import numpy as np
from crowd_analytics import CrowdAnalytics

# Đảm bảo console Windows in utf-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 4 nhãn chuẩn hóa
EMOTION_CLASSES = ['Happy', 'Normal', 'Sad', 'Surprised']

# Chuẩn ImageNet
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

# Cấu hình đường dẫn model
FACE_MODEL_PATH = 'weights/yolov8n-face.pt'
EMOTION_MODEL_PATH = 'weights/crowd_emotion_resnet18.pt'  # Sẽ có sau khi train ở Tuần 2

# Chế độ hoạt động: Mặc định True trong Tuần 1 (Mock data cho UI), đổi thành False khi cắm model thật
USE_MOCK_DATA = False

# Lazy-loaded singletons
_analytics = CrowdAnalytics(happy_thresh=0.25, panic_thresh=0.20, curious_thresh=0.20)
_detector = None
_model = None
_device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


def _ensure_models_loaded():
    """Khởi tạo detector và model nếu chưa load (chỉ load 1 lần)."""
    global _detector, _model
    if _detector is None:
        try:
            from face_detector import FaceDetector
            _detector = FaceDetector(FACE_MODEL_PATH)
        except Exception as e:
            print(f"[WARNING] Không thể load FaceDetector: {e}. Sẽ dùng Mock data.")

    if _model is None and os.path.exists(EMOTION_MODEL_PATH):
        try:
            from crowd_emotion_model import CrowdEmotionModel
            _model = CrowdEmotionModel(num_classes=4, freeze_backbone=True)
            _model.load_state_dict(torch.load(EMOTION_MODEL_PATH, map_location=_device))
            _model.to(_device)
            _model.eval()
            print(f"[INFO] Đã nạp thành công mô hình cảm xúc từ '{EMOTION_MODEL_PATH}'")
        except Exception as e:
            print(f"[WARNING] Không thể load EmotionModel: {e}")


def _preprocess_face(face_bgr, target_size=(224, 224)):
    """Tiền xử lý ảnh khuôn mặt BGR thành Tensor chuẩn ImageNet."""
    face_rgb = cv.cvtColor(face_bgr, cv.COLOR_BGR2RGB)
    face_resized = cv.resize(face_rgb, target_size)
    face_norm = face_resized.astype(np.float32) / 255.0
    face_norm = (face_norm - IMAGENET_MEAN) / IMAGENET_STD
    face_transposed = np.transpose(face_norm, (2, 0, 1))  # [3, H, W]
    tensor = torch.from_numpy(face_transposed).unsqueeze(0).float()  # [1, 3, H, W]
    return tensor.to(_device)


def predict_emotion_from_frame(frame, force_mock=False):
    """
    Hàm chính bàn giao cho Thành viên E gọi liên tục trong vòng lặp VideoCapture.

    Args:
        frame: numpy array BGR đọc từ OpenCV.
        force_mock: Nếu True, ép trả về Mock data để kiểm thử UI.

    Returns:
        dict: {"faces": [...], "crowd_insights": {...}}
    """
    if frame is None or frame.size == 0:
        return {"faces": [], "crowd_insights": _analytics.analyze_frame([])}

    h, w = frame.shape[:2]

    # === CHẾ ĐỘ MOCK DATA (Dành cho Team UI trong Tuần 1) ===
    if force_mock or USE_MOCK_DATA:
        mock_faces = [
            {"box": (w // 4, h // 4, w // 4 + 120, h // 4 + 140), "emotion": "Happy", "confidence": 0.88},
            {"box": (w // 2, h // 3, w // 2 + 100, h // 3 + 120), "emotion": "Normal", "confidence": 0.92},
            {"box": (w * 3 // 4, h // 4, w * 3 // 4 + 110, h // 4 + 130), "emotion": "Normal", "confidence": 0.85},
        ]
        insights = _analytics.analyze_frame(mock_faces)
        return {"faces": mock_faces, "crowd_insights": insights}

    # === CHẾ ĐỘ INFERENCE THỰC TẾ (Tích hợp FaceDetector + Model) ===
    _ensure_models_loaded()

    if _detector is None:
        # Fallback về Mock nếu detector chưa sẵn sàng
        return predict_emotion_from_frame(frame, force_mock=True)

    detected_faces = _detector.detect_and_crop_faces(frame, target_size=(112, 112))
    face_results = []

    for item in detected_faces:
        box = item['box']
        face_img = item['face_img']

        if _model is not None:
            # Dùng model đã train
            tensor = _preprocess_face(face_img)
            with torch.no_grad():
                prob, label_idx = _model.predict_proba(tensor)
            emotion = EMOTION_CLASSES[label_idx.item()]
            confidence = round(prob.item(), 2)
        else:
            # Tuần 1: Model chưa train xong -> Gán nhãn tạm thời (heuristic/baseline)
            # để UI thấy bounding box thật trên video!
            emotion = "Normal"
            confidence = item['confidence']

        face_results.append({
            "box": box,
            "emotion": emotion,
            "confidence": confidence
        })

    # Phân tích tổng thể đám đông qua Tầng 2 với cơ chế Cửa sổ trượt (Sliding Window)
    crowd_insights = _analytics.analyze_stream(face_results)

    return {
        "faces": face_results,
        "crowd_insights": crowd_insights
    }



if __name__ == '__main__':
    print("--- Test ai_inference.py ---")
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # 1. Test Mock mode
    mock_res = predict_emotion_from_frame(dummy_frame, force_mock=True)
    print("\n1. Mock Data Output:")
    print("   Faces count:", len(mock_res['faces']))
    print("   Crowd mood: ", mock_res['crowd_insights']['crowd_mood'])
    print("   Alert level:", mock_res['crowd_insights']['alert_level'])
    assert len(mock_res['faces']) > 0

    # 2. Test Real Video Frame (nếu có video mẫu)
    video_path = 'Resources/Video/2021-09-22 17.32.08.mp4'
    if os.path.exists(video_path):
        cap = cv.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()
        if ret:
            real_res = predict_emotion_from_frame(frame, force_mock=False)
            print("\n2. Real Video Frame Output:")
            print("   Faces count:", len(real_res['faces']))
            print("   First face: ", real_res['faces'][0] if real_res['faces'] else "None")
            print("   Crowd mood: ", real_res['crowd_insights']['crowd_mood'])

    print("\n[OK] ai_inference.py test PASSED!")
