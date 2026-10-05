from pathlib import Path

import cv2 as cv


class FaceDetector:
    """YOLO face detector used by the AI-01 inference pipeline."""

    def __init__(self, model_path=None, conf_threshold=0.45):
        self.conf_threshold = conf_threshold
        model_path = Path(model_path) if model_path else Path(__file__).parent / "weights" / "yolov8n-face.pt"
        if not model_path.is_file():
            raise FileNotFoundError(f"Face detector weights not found: {model_path}")

        from ultralytics import YOLO

        self.model = YOLO(str(model_path))

    def detect_and_crop_faces(self, frame, target_size=(112, 112)):
        if frame is None or frame.size == 0:
            return []

        height, width = frame.shape[:2]
        results = self.model(frame, conf=self.conf_threshold, verbose=False)
        faces = []
        for result in results:
            if result.boxes is None:
                continue
            for detection in result.boxes:
                x1, y1, x2, y2 = map(int, detection.xyxy[0].cpu().tolist())
                x1, x2 = max(0, min(width - 1, x1)), max(0, min(width, x2))
                y1, y2 = max(0, min(height - 1, y1)), max(0, min(height, y2))
                if x2 - x1 < 10 or y2 - y1 < 10:
                    continue

                face_image = frame[y1:y2, x1:x2]
                if face_image.size == 0:
                    continue
                faces.append({
                    "box": (x1, y1, x2, y2),
                    "face_img": cv.resize(face_image, target_size, interpolation=cv.INTER_AREA),
                    "confidence": round(float(detection.conf[0].cpu().item()), 2),
                })
        return faces
