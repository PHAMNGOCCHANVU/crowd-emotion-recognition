# 🎥 Crowd Emotion Recognition — Camera CCTV Góc Rộng
> **Hệ thống AI phân tích biểu cảm thời gian thực phục vụ An ninh & Đánh giá trải nghiệm không gian công cộng**  
> *Dự án phát triển và nâng cấp toàn diện từ nền tảng repo gốc `patrikken/emotion_recognition`.*

---

## 📌 1. Giới thiệu Đề tài
Dự án ứng dụng Trí tuệ nhân tạo (AI) và Thị giác máy tính (Computer Vision) để phân tích biểu cảm thời gian thực của dòng người di chuyển qua hành lang, sảnh sự kiện hoặc cửa ra vào thông qua hệ thống **camera góc rộng treo cao (Top-down CCTV)**.

### Mục tiêu nghiệp vụ:
* **Đánh giá trải nghiệm không gian:** Đo lường mức độ **Hài lòng** (dòng người vui vẻ, thoải mái) và mức độ **Tò mò / Thu hút** (chú ý vào gian hàng, màn hình quảng cáo).
* **Cảnh báo an ninh sớm:** Tự động phát hiện trạng thái **Hoang mang / Bất thường** (dấu hiệu hoảng loạn, sợ hãi, chen lấn, mất an ninh trật tự).
* **Trạng thái nền tảng:** Duy trì dòng người lưu thông **Bình thường / Ổn định** (chiếm 80–90% lưu lượng).

---

## 🏗️ 2. Kiến trúc Kỹ thuật Phân tầng (2-Tier Architecture)

Để giải quyết bài toán camera góc rộng (khuôn mặt ở xa, nhỏ 30–80px, mờ chuyển động và góc nghiêng), hệ thống được thiết kế theo mô hình 2 tầng công nghiệp:

```
[ Luồng Video CCTV / IP Camera ]
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│ TẦNG 1: CORE AI VISION (Inference từng khuôn mặt)               │
│ - Face Detector: YOLOv8-Face (bắt mặt cự ly xa, góc nghiêng)     │
│ - Backbone: ResNet-18 (ImageNet Pre-trained) trích xuất đặc trưng│
│ - Classification: 4 nhãn chuẩn (Happy, Normal, Sad, Surprised)  │
└────────────────────────────────┬────────────────────────────────┘
                                 │ Danh sách faces: [ {"box": ..., "emotion": ..., "conf": ...} ]
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ TẦNG 2: CROWD ANALYTICS & ALERT (Thống kê & Cảnh báo ngưỡng)   │
│ - Phân tích phân phối % cảm xúc cả đám đông theo thời gian thực │
│ - Bình thường: Normal > 75% ➔ Dòng người lưu thông ổn định      │
│ - Hài lòng: Happy > 25% ➔ Không khí tích cực / Hài lòng         │
│ - Cảnh báo: Surprised + Sad > 20% ➔ CẢNH BÁO AN NINH / SỰ CỐ    │
│ - Tò mò: Surprised tập trung cao tại booth / biển quảng cáo     │
└────────────────────────────────┬────────────────────────────────┘
                                 │ Kết quả gộp (faces + crowd_insights)
                                 ▼
[ DASHBOARD UI (Thành viên E): Hiển thị Bounding Box + Biểu đồ thời gian thực ]
```

---

## 📁 3. Cấu trúc Thư mục Dự án

```
d:\emotion_recognition\
├── 📂 docs/                            ← Tài liệu nội bộ của nhóm
│   ├── docs.md                         ← Đề tài và kiến trúc tổng quan
│   ├── phanchiacongviec.md             ← Bảng phân chia công việc chi tiết 2 tuần
│   ├── requirements.md                 ← Yêu cầu kỹ thuật chi tiết của Team AI
│   └── xaydungbodulieu.md              ← Cẩm nang chuẩn bị dữ liệu cho Team Data
├── 📂 weights/                         ← Trọng số các mô hình AI
│   ├── yolov8n-face.pt                 ← Model YOLOv8 phát hiện khuôn mặt từ xa
│   └── crowd_emotion_resnet18.pt       ← Model cảm xúc (huấn luyện ở Tuần 2)
├── 📂 Dataset/                         ← Dữ liệu huấn luyện (Team Data bàn giao)
│   ├── Train/{Happy, Normal, Sad, Surprised}/
│   └── Validation/{Happy, Normal, Sad, Surprised}/
├── 📂 Resources/Video/                 ← Video CCTV mẫu để kiểm thử
├── requirements.txt                    ← Danh sách thư viện chuẩn hóa
├── face_detector.py                    ← Module phát hiện khuôn mặt YOLOv8-Face
├── crowd_emotion_model.py              ← Mô hình nhận diện biểu cảm ResNet-18 (4 nhãn)
├── crowd_analytics.py                  ← Tầng phân tích đám đông & cảnh báo ngưỡng
├── data_loader.py                      ← Pipeline nạp dữ liệu + Data Augmentation
├── ai_inference.py                     ← Interface chuẩn bàn giao cho Team UI
├── test_pipeline.py                    ← Script kiểm thử End-to-End toàn hệ thống
├── feature_extractor.py                ← Script bóc tách backbone gốc (đối chứng baseline)
└── live_emotion_recognition.py         ← File demo gốc của tác giả (tham khảo)
```

---

## 🚀 4. Cài đặt & Hướng dẫn Chạy thử

### 4.1. Cài đặt môi trường
Khuyến nghị sử dụng Python 3.10 – 3.12 và môi trường ảo (`.venv`):

```powershell
# 1. Kích hoạt môi trường ảo
.venv\Scripts\activate

# 2. Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

### 4.2. Chạy kiểm thử End-to-End toàn bộ chuỗi AI
Kiểm tra toàn bộ luồng từ đọc video ➔ phát hiện mặt ➔ đoán cảm xúc ➔ phân tích đám đông & đo FPS:

```powershell
python test_pipeline.py
```
*(Kết quả thử nghiệm đạt **~31.4 FPS trên CPU**, bắt chính xác 60/60 khuôn mặt trên video mẫu).*

### 4.3. Kiểm tra riêng từng Module
* **Kiểm tra bộ bắt mặt từ xa:** `python face_detector.py`
* **Kiểm tra mô hình ResNet-18:** `python crowd_emotion_model.py`
* **Kiểm tra logic phân tích đám đông:** `python crowd_analytics.py`
* **Kiểm tra Data Loader:** `python data_loader.py`
* **Kiểm tra Interface bàn giao UI:** `python ai_inference.py`

---

## 🤝 5. Hướng dẫn Tích hợp giữa các Team

### 💻 Dành cho Team UI/System (Thành viên E):
Chỉ cần import duy nhất một hàm từ `ai_inference.py` vào vòng lặp đọc video/camera:

```python
from ai_inference import predict_emotion_from_frame

# Trong vòng lặp đọc frame của OpenCV / Streamlit:
results = predict_emotion_from_frame(frame)

# 1. Lấy danh sách khuôn mặt để vẽ Bounding Box:
for face in results["faces"]:
    x1, y1, x2, y2 = face["box"]
    emotion = face["emotion"]       # 'Happy', 'Normal', 'Sad', 'Surprised'
    conf = face["confidence"]

# 2. Lấy số liệu phân tích đám đông để vẽ biểu đồ & kích hoạt cảnh báo:
insights = results["crowd_insights"]
mood = insights["crowd_mood"]       # e.g. "Hài lòng / Tích cực" hoặc "Hoang mang / Bất thường"
alert = insights["alert_level"]     # "NORMAL" hoặc "WARNING"
dist = insights["distribution"]     # {"Happy": 0.3, "Normal": 0.6, ...}
```
> *(Trong Tuần 1, hàm sẽ tự động trả về Mock Data nếu chưa có model train hoàn chỉnh, giúp Team UI phát triển giao diện hoàn toàn độc lập).*

### 📊 Dành cho Team Data (Thành viên C & D):
* Tận dụng các bộ dữ liệu mở quốc tế (**RAF-DB, FER-2013, AffectNet**) kết hợp cắt video CCTV thực tế bằng chính `face_detector.py`.
* Đóng gói ảnh vào đúng cấu trúc `Dataset/Train/` và `Dataset/Validation/` gồm 4 thư mục: `Happy`, `Normal`, `Sad`, `Surprised`.

---

## 👥 6. Phân công Nhóm & Tiến độ 2 Tuần

| Vai trò | Thành viên | Trách nhiệm chính Tuần 1 | Trách nhiệm chính Tuần 2 |
|---|---|---|---|
| **AI Team** | **Thành viên A (Lead) & B** | Xây dựng Pipeline AI (YOLOv8-Face + ResNet-18 + CrowdAnalytics) + Interface UI | Huấn luyện mô hình trên dữ liệu CCTV + Tối ưu hóa mô hình (.onnx) |
| **Data Team** | **Thành viên C & D** | Thu thập, trích xuất và đóng gói tập dữ liệu 4 nhãn chuẩn | Chuẩn bị Test set thực tế + Đóng vai trò Tester nghiệm thu độ chính xác |
| **UI/System** | **Thành viên E** | Thiết kế Dashboard Mockup + Xây dựng luồng stream video thời gian thực | Nhúng model AI + Kết nối biểu đồ thời gian thực + Hoàn thiện hệ thống |
 
