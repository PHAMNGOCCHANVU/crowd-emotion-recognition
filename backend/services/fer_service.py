import os
import sys
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import cv2 as cv
import numpy as np

# Đảm bảo đường dẫn import linh hoạt (chạy từ backend/ hoặc từ root)
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
ROOT_DIR = BACKEND_DIR.parent
for p in [str(BACKEND_DIR), str(ROOT_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from backend.ai_core.interview_analytics import InterviewEmotionAnalytics
except ImportError:
    from ai_core.interview_analytics import InterviewEmotionAnalytics

# 6 nhãn cảm xúc chuẩn hóa theo Class Mapping
EMOTION_CLASSES = ["Contempt", "Fear", "Happy", "Normal", "Sad", "Surprised"]


def _find_weights_path(filename: str) -> Path:
    """Tìm đường dẫn weights trong backend/weights/ hoặc root weights/."""
    candidates = [
        BACKEND_DIR / "weights" / filename,
        ROOT_DIR / "weights" / filename,
    ]
    for c in candidates:
        if c.exists():
            return c
    return BACKEND_DIR / "weights" / filename


# Đường dẫn các mô hình ONNX và PyTorch
ONNX_FP32_PATH = _find_weights_path("mini_resnet_se_6emo.onnx")
ONNX_QUANT_PATH = _find_weights_path("mini_resnet_se_6emo_quant.onnx")
PYTORCH_PATH = _find_weights_path("mini_resnet_se_best.pt")

_ort_session = None
_ort_input_name = None
_pt_model = None
_analytics = InterviewEmotionAnalytics(fps=25.0)


def _load_engine():
    """
    Nạp engine inference cảm xúc:
    1. Ưu tiên ONNX FP32 (độ chính xác tuyệt đối, latency < 2ms).
    2. Fallback ONNX INT8 Quantized (siêu nhẹ 4.7MB).
    3. Fallback PyTorch (nếu chưa biên dịch ONNX).
    """
    global _ort_session, _ort_input_name, _pt_model

    if _ort_session is not None or _pt_model is not None:
        return _ort_session, _pt_model

    # 1. Thử load ONNX FP32 hoặc INT8
    for onnx_path in [ONNX_FP32_PATH, ONNX_QUANT_PATH]:
        if onnx_path.exists():
            try:
                import onnxruntime as ort
                sess_opts = ort.SessionOptions()
                sess_opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
                _ort_session = ort.InferenceSession(str(onnx_path), sess_opts, providers=["CPUExecutionProvider"])
                _ort_input_name = _ort_session.get_inputs()[0].name
                print(f"[FER Service] Đã nạp thành công mô hình ONNX: {onnx_path.name}")
                return _ort_session, None
            except Exception as e:
                print(f"[FER Service Warning] Không thể khởi tạo ONNX runtime từ {onnx_path.name}: {e}")

    # 2. Fallback sang PyTorch nếu có file .pt
    if PYTORCH_PATH.exists():
        try:
            import torch
            try:
                from backend.model import MiniResNetSE
            except ImportError:
                from model import MiniResNetSE
            model = MiniResNetSE(num_classes=6, dropout_rate=0.0)
            model.load_state_dict(torch.load(str(PYTORCH_PATH), map_location="cpu"))
            model.eval()
            _pt_model = model
            print(f"[FER Service] Đã nạp mô hình PyTorch fallback từ {PYTORCH_PATH.name}")
            return None, _pt_model
        except Exception as e:
            print(f"[FER Service Error] Không thể nạp mô hình PyTorch: {e}")


    print("[FER Service Warning] Không tìm thấy file trọng số hợp lệ trong thư mục weights/")
    return None, None


def _preprocess_face(face_bgr, target_size=(64, 64)) -> np.ndarray:
    """
    Tiền xử lý ảnh khuôn mặt chuẩn MiniResNetSE:
    - BGR -> Grayscale 1 kênh
    - Resize 64x64 pixel
    - Chuẩn hóa: (pixel / 255.0 - 0.5) / 0.5 -> [-1.0, 1.0]
    - Reshape sang batch tensor: (1, 1, 64, 64) Float32
    """
    face_gray = cv.cvtColor(face_bgr, cv.COLOR_BGR2GRAY)
    face_resized = cv.resize(face_gray, target_size, interpolation=cv.INTER_AREA)
    face_norm = (face_resized.astype(np.float32) / 255.0 - 0.5) / 0.5
    tensor = face_norm[np.newaxis, np.newaxis, :, :]  # (1, 1, 64, 64)
    return tensor


def _predict_emotion(face_bgr) -> tuple[str, float]:
    """Dự đoán cảm xúc và độ tin cậy từ ảnh khuôn mặt crop."""
    session, pt_model = _load_engine()
    if session is None and pt_model is None:
        return "Normal", 0.75

    tensor = _preprocess_face(face_bgr, target_size=(64, 64))

    # Inference qua ONNX Runtime (Tốc độ cao)
    if session is not None:
        logits = session.run(None, {_ort_input_name: tensor})[0]
        # Softmax ổn định số học
        exp_logits = np.exp(logits - np.max(logits, axis=1, keepdims=True))
        probs = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
        pred_idx = int(np.argmax(probs[0]))
        return EMOTION_CLASSES[pred_idx], float(probs[0][pred_idx])

    # Fallback qua PyTorch
    import torch
    with torch.no_grad():
        logits = pt_model(torch.from_numpy(tensor)).numpy()
        exp_logits = np.exp(logits - np.max(logits, axis=1, keepdims=True))
        probs = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
        pred_idx = int(np.argmax(probs[0]))
        return EMOTION_CLASSES[pred_idx], float(probs[0][pred_idx])


def _prepare_video_for_opencv(video_path: str) -> tuple[str, bool]:
    """
    Chuẩn hóa container video (đặc biệt WebM từ browser MediaRecorder thiếu metadata)
    bằng cách remux sang Matroska (.mkv) có đầy đủ index và timestamps để OpenCV đọc ổn định.
    Returns: (path_to_open, is_temporary_file)
    """
    if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
        return video_path, False

    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        fd, temp_mkv = tempfile.mkstemp(suffix=".mkv", prefix="fer_remux_")
        os.close(fd)
        cmd = [
            ffmpeg_exe, "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
            "-i", video_path, "-c:v", "copy", "-an", "-fflags", "+genpts", temp_mkv
        ]
        res = subprocess.run(cmd, capture_output=True, timeout=15)
        if res.returncode == 0 and os.path.exists(temp_mkv) and os.path.getsize(temp_mkv) > 0:
            return temp_mkv, True
        if os.path.exists(temp_mkv):
            os.remove(temp_mkv)
    except Exception as e:
        print(f"[FER Service Warning] Không thể remux video bằng FFmpeg, dùng file gốc: {e}")

    return video_path, False


def analyze_interview_video_fer(video_path: str) -> Dict[str, Any]:
    """
    Trích xuất khuôn mặt và nhận diện 6 nhãn cảm xúc từ video phỏng vấn:
    Contempt, Fear, Happy, Normal, Sad, Surprised.

    Args:
        video_path: Đường dẫn file video tạm (VD: /tmp/session_q1.webm)

    Returns:
        dict gồm: confidence_score, stress_score, dominant_emotion, emotion_distribution, emotion_timeline
    """
    video_to_read, is_temp = _prepare_video_for_opencv(video_path)
    cap = cv.VideoCapture(video_to_read)
    if not cap.isOpened():
        print(f"[FER Service Warning] Không thể mở file video: {video_path}")
        if is_temp and os.path.exists(video_to_read):
            try:
                os.remove(video_to_read)
            except Exception:
                pass
        return _analytics.analyze_interview_sequence([])

    try:
        raw_fps = cap.get(cv.CAP_PROP_FPS) or 25.0
        fps = raw_fps if (0 < raw_fps <= 120.0) else 25.0

        # Đọc cách quãng (mỗi 5 frame đọc 1 frame) để tăng tốc độ xử lý video
        skip_frames = max(1, int(fps // 5))
        effective_fps = max(1.0, fps / skip_frames)
        analytics = InterviewEmotionAnalytics(fps=effective_fps)

        frame_predictions: List[Dict[str, Any]] = []
        frame_idx = 0

        # Dùng Haar Cascade phát hiện khuôn mặt chính diện với tốc độ xử lý cao
        haar_path = cv.data.haarcascades + "haarcascade_frontalface_default.xml"
        face_cascade = cv.CascadeClassifier(haar_path)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % skip_frames == 0:
                gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=4,
                    minSize=(60, 60),
                )

                if len(faces) > 0:
                    # Lấy khuôn mặt lớn nhất (gần webcam nhất)
                    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
                    x, y, w, h = faces[0]
                    face_crop = frame[y : y + h, x : x + w]

                    if face_crop.size > 0:
                        emotion, conf = _predict_emotion(face_crop)
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

        if not frame_predictions:
            return analytics.analyze_interview_sequence([])

        return analytics.analyze_interview_sequence(frame_predictions)

    finally:
        cap.release()
        if is_temp and os.path.exists(video_to_read):
            try:
                os.remove(video_to_read)
            except Exception:
                pass
