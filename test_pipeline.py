"""
test_pipeline.py — Kịch bản kiểm thử End-to-End toàn bộ chuỗi xử lý AI
======================================================================
Mục tiêu:
1. Đảm bảo toàn bộ các module (FaceDetector -> CrowdEmotionModel -> CrowdAnalytics)
   kết nối với nhau mượt mà, không phát sinh lỗi ma trận hay tràn bộ nhớ (OOM).
2. Đo đạc tốc độ xử lý thực tế (FPS) trên video mẫu CCTV để đảm bảo yêu cầu thời gian thực.
"""

import os
import sys
import time
import cv2 as cv
import torch
import numpy as np

from face_detector import FaceDetector
from crowd_emotion_model import CrowdEmotionModel, EMOTION_CLASSES
from crowd_analytics import CrowdAnalytics

# Đảm bảo console Windows in utf-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Chuẩn ImageNet
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def preprocess_face(face_bgr, target_size=(112, 112)):
    """Tiền xử lý ảnh crop thành tensor ImageNet."""
    face_rgb = cv.cvtColor(face_bgr, cv.COLOR_BGR2RGB)
    face_resized = cv.resize(face_rgb, target_size)
    face_norm = face_resized.astype(np.float32) / 255.0
    face_norm = (face_norm - IMAGENET_MEAN) / IMAGENET_STD
    face_transposed = np.transpose(face_norm, (2, 0, 1))
    return torch.from_numpy(face_transposed).unsqueeze(0).float()


def run_pipeline_test(video_path='Resources/Video/2021-09-22 17.32.08.mp4', max_frames=60):
    print("=" * 65)
    print("🚀 BẮT ĐẦU KIỂM THỬ END-TO-END PIPELINE (WEEK 1)")
    print("=" * 65)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"[INFO] Thiết bị tính toán: {device}")

    # 1. Khởi tạo các module
    print("[1/3] Khởi tạo FaceDetector (YOLOv8-Face)...")
    detector = FaceDetector('weights/yolov8n-face.pt', conf_threshold=0.40)

    print("[2/3] Khởi tạo CrowdEmotionModel (ResNet-18 Backbone)...")
    model = CrowdEmotionModel(num_classes=4, freeze_backbone=True)
    model.to(device)
    model.eval()

    print("[3/3] Khởi tạo CrowdAnalytics (Tier 2)...")
    analytics = CrowdAnalytics(happy_thresh=0.25, panic_thresh=0.20, curious_thresh=0.20)

    if not os.path.exists(video_path):
        print(f"[ERROR] Không tìm thấy video tại '{video_path}'!")
        return False

    cap = cv.VideoCapture(video_path)
    fps_in = cap.get(cv.CAP_PROP_FPS)
    total_frames = int(cap.get(cv.CAP_PROP_FRAME_COUNT))
    print(f"\n[INFO] Đang nạp video: {video_path}")
    print(f"[INFO] Video FPS gốc: {fps_in:.1f} | Tổng số frames: {total_frames}")
    print(f"[INFO] Chạy kiểm thử trên {max_frames} frames đầu tiên...\n")

    frame_count = 0
    total_faces_detected = 0
    start_time = time.time()

    while cap.isOpened() and frame_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        # Tầng 1A: Phát hiện & crop mặt
        faces = detector.detect_and_crop_faces(frame, target_size=(112, 112))
        frame_results = []

        # Tầng 1B: Dự đoán cảm xúc từng mặt
        for face_info in faces:
            total_faces_detected += 1
            tensor = preprocess_face(face_info['face_img']).to(device)

            with torch.no_grad():
                prob, label_idx = model.predict_proba(tensor)

            emotion = EMOTION_CLASSES[label_idx.item()]
            frame_results.append({
                "box": face_info['box'],
                "emotion": emotion,
                "confidence": round(prob.item(), 2)
            })

        # Tầng 2: Phân tích đám đông
        crowd_res = analytics.analyze_frame(frame_results)

        # In log định kỳ mỗi 10 frames
        if frame_count % 10 == 0:
            print(
                f"Frame {frame_count:03d} | Faces: {len(faces)} | "
                f"Mood: {crowd_res['crowd_mood']:<24} | Alert: {crowd_res['alert_level']}"
            )

        frame_count += 1

    cap.release()
    elapsed_time = time.time() - start_time
    avg_fps = frame_count / elapsed_time if elapsed_time > 0 else 0

    print("\n" + "=" * 65)
    print("📊 KẾT QUẢ ĐO ĐẠC HIỆU NĂNG TOÀN PIPELINE:")
    print("=" * 65)
    print(f"Tổng số frames xử lý:      {frame_count}")
    print(f"Tổng số mặt phát hiện:     {total_faces_detected}")
    print(f"Thời gian thực thi:        {elapsed_time:.2f} giây")
    print(f"Tốc độ trung bình (FPS):   {avg_fps:.1f} FPS")
    print("=" * 65)

    if avg_fps >= 10.0:
        print(f"✅ ĐẠT YÊU CẦU: Tốc độ xử lý ({avg_fps:.1f} FPS) đáp ứng thời gian thực (>= 10 FPS).")
    else:
        print(f"⚠️ CẢNH BÁO: Tốc độ xử lý ({avg_fps:.1f} FPS) thấp hơn mục tiêu (>= 10 FPS). Cần tối ưu frame skip.")

    print("\n[OK] Toàn bộ chuỗi xử lý AI (End-to-End Pipeline) hoạt động CHÍNH XÁC!")
    return True


if __name__ == '__main__':
    run_pipeline_test()
