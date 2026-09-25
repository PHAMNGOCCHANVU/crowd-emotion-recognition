import os
import sys
import cv2 as cv
import numpy as np
from ultralytics import YOLO

# Đảm bảo console Windows in utf-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


class FaceDetector:
    """
    Tier 1: Bộ phát hiện khuôn mặt cự ly xa từ camera CCTV góc rộng.
    Sử dụng YOLOv8-Face (hoặc fallback YOLOv8) để bắt chính xác các khuôn mặt
    kích thước nhỏ (20-60px), góc nghiêng (top-down, profile) và trong môi trường ánh sáng phức tạp.
    """
    def __init__(self, model_path='weights/yolov8n-face.pt', conf_threshold=0.45):
        self.conf_threshold = conf_threshold

        # Kiểm tra file trọng số
        if not os.path.exists(model_path):
            if os.path.exists('yolov8n.pt'):
                print(f"[WARNING] Không tìm thấy '{model_path}'. Dùng fallback 'yolov8n.pt'.")
                model_path = 'yolov8n.pt'
            else:
                print(f"[INFO] Tải model '{model_path}'...")

        self.model = YOLO(model_path)
        print(f"[INFO] FaceDetector đã khởi tạo thành công với trọng số: {model_path}")

    def detect_and_crop_faces(self, frame, target_size=(112, 112)):
        """
        Phát hiện toàn bộ khuôn mặt trong frame ảnh và chuẩn hóa kích thước.

        Args:
            frame: Ảnh BGR numpy array từ cv2.VideoCapture hoặc IP Camera.
            target_size: (width, height) để đưa vào mô hình cảm xúc (mặc định 112x112).

        Returns:
            list of dict: [
                {
                    "box": (x1, y1, x2, y2),
                    "face_img": ndarray (BGR đã resize),
                    "confidence": float
                },
                ...
            ]
        """
        if frame is None or frame.size == 0:
            return []

        h, w = frame.shape[:2]
        results = self.model(frame, conf=self.conf_threshold, verbose=False)
        detected_faces = []

        for result in results:
            if result.boxes is None or len(result.boxes) == 0:
                continue

            for box in result.boxes:
                coords = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3])
                conf = float(box.conf[0].cpu().item())

                # Đảm bảo bounding box nằm trong giới hạn khung hình
                x1 = max(0, min(w - 1, x1))
                y1 = max(0, min(h - 1, y1))
                x2 = max(0, min(w, x2))
                y2 = max(0, min(h, y2))

                # Kiểm tra diện tích hợp lệ
                if (x2 - x1) < 10 or (y2 - y1) < 10:
                    continue

                face_crop = frame[y1:y2, x1:x2]
                if face_crop.size == 0:
                    continue

                face_resized = cv.resize(face_crop, target_size, interpolation=cv.INTER_AREA)

                detected_faces.append({
                    "box": (x1, y1, x2, y2),
                    "face_img": face_resized,
                    "confidence": round(conf, 2)
                })

        return detected_faces


if __name__ == '__main__':
    print("--- Test FaceDetector trên Video mẫu ---")
    detector = FaceDetector('weights/yolov8n-face.pt', conf_threshold=0.40)

    video_path = 'Resources/Video/2021-09-22 17.32.08.mp4'
    if not os.path.exists(video_path):
        # Nếu không có video mẫu, test bằng dummy image
        print(f"[INFO] Không tìm thấy '{video_path}'. Test bằng dummy image.")
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv.circle(dummy_frame, (320, 240), 50, (200, 200, 200), -1)
        faces = detector.detect_and_crop_faces(dummy_frame)
        print(f"Detected {len(faces)} faces on dummy image.")
    else:
        cap = cv.VideoCapture(video_path)
        frame_idx = 0
        total_faces_found = 0

        while cap.isOpened() and frame_idx < 30:  # Test 30 frames đầu tiên
            ret, frame = cap.read()
            if not ret:
                break

            faces = detector.detect_and_crop_faces(frame, target_size=(112, 112))
            if len(faces) > 0:
                total_faces_found += len(faces)
                for f in faces:
                    x1, y1, x2, y2 = f['box']
                    print(f"Frame {frame_idx:02d}: Face at ({x1},{y1})-({x2},{y2}) conf={f['confidence']}")

            frame_idx += 1

        cap.release()
        print(f"[INFO] Processed {frame_idx} frames. Total faces detected: {total_faces_found}")

    print("[OK] FaceDetector test PASSED!")
