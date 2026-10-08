Mục tiêu tối thượng của Team AI trong Tuần 1 là: Xây dựng xong bộ khung xử lý AI (Pipeline) hoàn chỉnh theo **Kiến trúc Phân tầng (2-Tier Architecture)**:
- **Tầng 1 (AI Core):** Kết hợp mô hình bắt mặt từ xa (**YOLOv8-Face**) và mô hình nhận diện 4 biểu cảm cơ sở chuẩn hóa quốc tế (**Happy, Normal, Sad, Surprised**) sử dụng ResNet-18 Backbone.
- **Tầng 2 (Crowd Analytics & Alert):** Module thống kê phân phối cảm xúc đám đông theo thời gian thực và kích hoạt cảnh báo an ninh / trải nghiệm (**Hài lòng, Hoang mang, Tò mò, Bình thường**).
- Sẵn sàng cấu trúc nạp dữ liệu (Data Loader) cho 4 nhãn chuẩn để tiếp nhận dữ liệu từ Team Data ở tuần sau, đồng thời bàn giao interface `ai_inference.py` (kèm Mock Data) cho Team UI.

Dưới đây là hướng dẫn hành động chi tiết từng ngày cho Thành viên A và B:

------------------------------
## 🚀 Giai đoạn Khởi động: Ngày 1 - Ngày 2 (Thấu hiểu và Tách lõi)
Hai thành viên cùng ngồi lại cài đặt môi trường (PyTorch, OpenCV, CUDA/CPU) để đảm bảo đồng bộ, tránh lỗi cấu hình chéo nhau.

* **Nhiệm vụ 1: Chạy thử nghiệm và Đánh giá Baseline:**
  * Chạy file demo gốc `live_emotion_recognition.py` với video mẫu để kiểm tra cấu trúc dữ liệu đầu vào/đầu ra.
  * Đánh giá tỷ lệ bắt mặt của Haar Cascade trên góc nhìn xa (ghi nhận điểm yếu để làm cơ sở so sánh khi thay bằng YOLOv8-Face).
* **Nhiệm vụ 2: Tách lõi trích xuất đặc trưng & Chuẩn bị ResNet-18 Backbone:**
  * Phân tích file `model.py` gốc (Backbone CNN 4 lớp tự chế, ~547KB).
  * Viết script `feature_extractor.py` để bóc tách Backbone và chuẩn bị chuyển đổi sang **ResNet-18 Pre-trained** (từ `torchvision.models`) nhằm nâng cao năng lực trích xuất đặc trưng trên ảnh CCTV mờ từ xa.

------------------------------
## 👁️ Giai đoạn Nâng cấp: Ngày 3 - Ngày 4 (Tích hợp YOLOv8-Face & Mô hình 4 nhãn)
Giải quyết bài toán camera gắn tường quay từ xa và góc nghiêng bằng công nghệ Deep Learning hiện đại.

* **Nhiệm vụ 3 (Tích hợp YOLOv8-Face):**
  * Tải và cài đặt thư viện `ultralytics`. Tải trọng số `yolov8n-face.pt`.
  * Viết module `face_detector.py` chứa class `FaceDetector` với hàm `detect_and_crop_faces(frame, target_size=(112, 112))`.
  * Hàm này nhận frame ảnh lớn từ camera, tự động quét tìm khuôn mặt từ xa, cắt vùng mặt và chuẩn hóa kích thước cho mô hình phân loại.
* **Nhiệm vụ 4 (Xây dựng Mô hình 4 nhãn & Tầng phân loại mới):**
  * Viết file `crowd_emotion_model.py`: Sử dụng ResNet-18 Backbone kết hợp tầng FC phân loại **4 nhãn chuẩn** (`Happy`, `Normal`, `Sad`, `Surprised`).
  * Thực hiện **Khóa tầng (Freeze Backbone)**: Chỉ huấn luyện cập nhật trọng số cho tầng FC mới, giúp train siêu nhanh và tránh overfitting.
* **Nhiệm vụ 4B (Xây dựng Tầng Thống kê & Cảnh báo ngưỡng - `crowd_analytics.py`):**
  * Viết thuật toán tổng hợp danh sách biểu cảm cá nhân trong frame thành chỉ số đám đông:
    * `Normal > 75%`: Lưu lượng ổn định / Bình thường.
    * `Happy > 25%`: Đám đông Hài lòng / Không khí tích cực (Đo trải nghiệm).
    * `Surprised + Sad > 20%`: **CẢNH BÁO AN NINH: Hoang mang / Bất thường** (Phát hiện hoảng loạn, chen lấn).
    * `Surprised tập trung cao`: Mức độ Tò mò / Chú ý cao vào không gian.

------------------------------
## 🛠️ Giai đoạn Chuẩn bị Train: Ngày 5 - Ngày 7 (Hợp nhất Pipeline & Viết Data Loader)
Hợp nhất toàn bộ các module thành một chuỗi xử lý AI hoàn chỉnh từ đầu đến cuối (End-to-End).

* **Nhiệm vụ 5 (Viết cấu trúc nạp dữ liệu - Data Loader):**
  * Thống nhất với Team Data về cấu trúc thư mục 4 nhãn chuẩn:
    ```
    Dataset/
    ├── Train/{Happy, Normal, Sad, Surprised}/
    └── Validation/{Happy, Normal, Sad, Surprised}/
    ```
  * Sử dụng `torchvision.datasets.ImageFolder` và `torch.utils.data.DataLoader` viết file `data_loader.py`.
  * Thêm các phép tăng cường dữ liệu (**Data Augmentation**) chuyên biệt cho CCTV: ColorJitter, GaussianBlur, RandomCrop.
* **Nhiệm vụ 6 (Hợp nhất và Kiểm thử khung AI với dữ liệu giả):**
  * Viết script kiểm thử `test_pipeline.py`: Chạy chuỗi `VideoCapture ➔ FaceDetector ➔ CrowdEmotionModel ➔ CrowdAnalytics`.
  * Tạo dữ liệu giả (vài tấm ảnh mỗi nhãn) chạy thử `model.train()` để đảm bảo không bị lỗi shape tensor, cú pháp hay tràn bộ nhớ (OOM).
  * Đo FPS tổng thể của toàn pipeline (Target: ≥ 12 FPS trên CPU).

------------------------------
## 🤝 Thỏa thuận đầu ra (Interface) để bàn giao cho Team UI (Thành viên E) vào ngày thứ 7
Vào cuối tuần 1, Thành viên A (AI Lead) bàn giao cho Thành viên E (UI) file `ai_inference.py` chứa hàm chuẩn có định dạng dữ liệu 2 tầng:

```python
"""
ai_inference.py — Interface chuẩn bàn giao cho Team UI (Thành viên E)
"""
from crowd_analytics import CrowdAnalytics

_analytics = CrowdAnalytics()
_model = None
_detector = None

def predict_emotion_from_frame(frame):
    """
    Hàm Thành viên E gọi liên tục trong vòng lặp đọc Video của OpenCV.
    Input:  frame (ảnh numpy array BGR từ camera/video)
    Output: dict chứa danh sách khuôn mặt (vẽ bounding box) và phân tích đám đông (vẽ biểu đồ)
    """
    # === TUẦN 1: Trả về MOCK DATA để Team UI lập trình song song ===
    if _model is None:
        h, w = frame.shape[:2]
        mock_faces = [
            {"box": (w//4, h//4, w//4+100, h//4+120), "emotion": "Happy", "confidence": 0.88},
            {"box": (w//2, h//3, w//2+90, h//3+110), "emotion": "Normal", "confidence": 0.92},
        ]
        insights = _analytics.analyze_frame(mock_faces)
        return {
            "faces": mock_faces,
            "crowd_insights": insights
        }

    # === TUẦN 2: Chạy Model thật sau khi train xong ===
    # faces = _detector.detect_and_crop_faces(frame)
    # results = _model.predict_proba(faces)
    # insights = _analytics.analyze_frame(results)
    # return {"faces": results, "crowd_insights": insights}
```




