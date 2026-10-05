"""AI-01 inference interface, with mock fallback until model weights exist."""

import os
from pathlib import Path

import cv2 as cv
import numpy as np

from crowd_analytics import CrowdAnalytics

EMOTION_CLASSES = ["Happy", "Normal", "Sad", "Surprised"]
ROOT = Path(__file__).parent
FACE_MODEL_PATH = ROOT / "weights" / "yolov8n-face.pt"
EMOTION_MODEL_PATH = ROOT / "weights" / "crowd_emotion_resnet18.pt"
USE_MOCK_DATA = os.getenv("AI_USE_MOCK_DATA", "0").lower() in {"1", "true", "yes"}

_analytics = CrowdAnalytics()
_detector = None
_model = None
_load_attempted = False


def _load_models():
    global _detector, _model, _load_attempted
    if _load_attempted:
        return
    _load_attempted = True

    if not FACE_MODEL_PATH.is_file():
        return

    try:
        from face_detector import FaceDetector

        _detector = FaceDetector(FACE_MODEL_PATH)
    except Exception as error:
        print(f"[AI-01] Face detector unavailable; using mock output: {error}")
        return

    if not EMOTION_MODEL_PATH.is_file():
        return

    try:
        import torch
        from crowd_emotion_model import CrowdEmotionModel

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _model = CrowdEmotionModel(num_classes=4, freeze_backbone=True, pretrained_backbone=False)
        _model.load_state_dict(torch.load(EMOTION_MODEL_PATH, map_location=device))
        _model.to(device).eval()
    except Exception as error:
        _model = None
        print(f"[AI-01] Emotion model unavailable; using detector-only labels: {error}")


def _mock_result(frame):
    height, width = frame.shape[:2]
    box_width = max(1, min(120, width // 4))
    box_height = max(1, min(140, height // 3))
    mock_faces = [
        {"box": (width // 4, height // 4, min(width, width // 4 + box_width), min(height, height // 4 + box_height)), "emotion": "Happy", "confidence": 0.88},
        {"box": (width // 2, height // 3, min(width, width // 2 + box_width), min(height, height // 3 + box_height)), "emotion": "Normal", "confidence": 0.92},
        {"box": (width * 3 // 4, height // 4, min(width, width * 3 // 4 + box_width), min(height, height // 4 + box_height)), "emotion": "Normal", "confidence": 0.85},
    ]
    return {"faces": mock_faces, "crowd_insights": _analytics.analyze_frame(mock_faces)}


def _preprocess_face(face_bgr, device, target_size=(112, 112)):
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    face_rgb = cv.cvtColor(face_bgr, cv.COLOR_BGR2RGB)
    face = cv.resize(face_rgb, target_size).astype(np.float32) / 255.0
    face = (face - mean) / std
    tensor = np.transpose(face, (2, 0, 1)).copy()

    import torch

    return torch.from_numpy(tensor).unsqueeze(0).to(device)


def predict_emotion_from_frame(frame, force_mock=False):
    """Analyze one OpenCV BGR frame; return AI-01's faces/crowd_insights schema."""
    if frame is None or frame.size == 0:
        return {"faces": [], "crowd_insights": _analytics.analyze_frame([])}
    if force_mock or USE_MOCK_DATA:
        return _mock_result(frame)

    _load_models()
    if _detector is None:
        return _mock_result(frame)

    detections = _detector.detect_and_crop_faces(frame, target_size=(112, 112))
    faces = []
    for detection in detections:
        emotion = "Normal"
        confidence = detection["confidence"]
        if _model is not None:
            import torch

            device = next(_model.parameters()).device
            tensor = _preprocess_face(detection["face_img"], device)
            with torch.no_grad():
                probabilities, label_index = _model.predict_proba(tensor)
            emotion = EMOTION_CLASSES[label_index.item()]
            confidence = round(probabilities.item(), 2)

        faces.append({
            "box": detection["box"],
            "emotion": emotion,
            "confidence": confidence,
        })

    return {"faces": faces, "crowd_insights": _analytics.analyze_frame(faces)}
