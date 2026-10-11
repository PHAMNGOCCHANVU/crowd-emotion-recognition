import os
import sys
from pathlib import Path
from typing import Dict, Any, List

import cv2 as cv
import numpy as np
import torch

# Đảm bảo đường dẫn import ai_core
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai_core.crowd_emotion_model import CrowdEmotionModel
from ai_core.interview_analytics import InterviewEmotionAnalytics

EMOTION_CLASSES = ["Happy", "Normal", "Sad", "Surprised"]
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_model = None
_analytics = InterviewEmotionAnalytics(fps=25.0)

WEIGHTS_PATH = ROOT_DIR / "weights" / "crowd_emotion_resnet18.pt"


def _load_model():
    global _model
    if _model is None and WEIGHTS_PATH.exists():
        try:
            model = CrowdEmotionModel(num_classes=4, freeze_backbone=True)
            model.load_state_dict(torch.load(str(WEIGHTS_PATH), map_location=_device))
            model.to(_device)
            model.eval()
            _model = model
            print(f"[FER Service] Đã nạp mô hình cảm xúc thành công từ {WEIGHTS_PATH}")
        except Exception as e:
            print(f"[FER Service Warning] Không thể load model: {e}")
    return _model


def _preprocess_face(face_bgr, target_size=(224, 224)):
    face_rgb = cv.cvtColor(face_bgr, cv.COLOR_BGR2RGB)
    face_resized = cv.resize(face_rgb, target_size)
    face_norm = face_resized.astype(np.float32) / 255.0
    face_norm = (face_norm - IMAGENET_MEAN) / IMAGENET_STD
    face_transposed = np.transpose(face_norm, (2, 0, 1))
    tensor = torch.from_numpy(face_transposed).unsqueeze(0).float()
    return tensor.to(_device)


def analyze_interview_video_fer(video_path: str) -> Dict[str, Any]:
    """
    Trích xuất khuôn mặt và biểu cảm từ video câu trả lời phỏng vấn.

    Args:
        video_path: Đường dẫn file video tạm (/tmp/session_q1.webm)

    Returns:
        dict gồm: confidence_score, stress_score, emotion_distribution, emotion_timeline
    """
    model = _load_model()
    cap = cv.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[FER Service Warning] Không thể mở file video: {video_path}")
        return _analytics.analyze_interview_sequence([])

    fps = cap.get(cv.CAP_PROP_FPS) or 25.0
    analytics = InterviewEmotionAnalytics(fps=fps)

    frame_predictions: List[Dict[str, Any]] = []
    frame_idx = 0

    # Dùng Haar Cascade cơ bản cho webcam chính diện để inference siêu tốc
    haar_path = cv.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv.CascadeClassifier(haar_path)

    # Đọc cách quãng (ví dụ lấy mỗi 5 frame một lần để tăng tốc độ phân tích)
    skip_frames = max(1, int(fps // 5))

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % skip_frames == 0:
            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(60, 60))

            if len(faces) > 0 and model is not None:
                # Lấy khuôn mặt lớn nhất (gần camera nhất)
                faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
                x, y, w, h = faces[0]
                face_crop = frame[y : y + h, x : x + w]

                if face_crop.size > 0:
                    tensor = _preprocess_face(face_crop)
                    with torch.no_grad():
                        logits = model(tensor)
                        probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
                    pred_idx = int(np.argmax(probs))
                    emotion = EMOTION_CLASSES[pred_idx]
                    conf = float(probs[pred_idx])
                else:
                    emotion, conf = "Normal", 0.8
            else:
                emotion, conf = "Normal", 0.75

            frame_predictions.append({
                "frame_idx": frame_idx,
                "emotion": emotion,
                "confidence": conf,
            })

        frame_idx += 1

    cap.release()

    # Nếu không bắt được frame nào, tạo phân bổ mặc định
    if not frame_predictions:
        return analytics.analyze_interview_sequence([])

    return analytics.analyze_interview_sequence(frame_predictions)
