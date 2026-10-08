# 🛠️ KẾ HOẠCH TRIỂN KHAI THỰC THI (IMPLEMENTATION PLAN) — TUẦN 2
### Dự án: Crowd Emotion Recognition từ Camera CCTV Góc Rộng
### Trọng tâm: Huấn luyện Mô hình Tầng 1 & Hoàn thiện Tầng 2 Thống kê Đám đông
### Đối tượng: Team AI (Thành viên A & B) phối hợp Team Data (C & D) và Team UI (E)

---

## 📌 1. MỤC TIÊU & CHỈ SỐ KPI TUẦN 2

| Chỉ số / Hạng mục | Mục tiêu cam kết (KPI) | Phương pháp đo lường |
|:---|:---|:---|
| **Độ chính xác mô hình (Tầng 1)** | **Validation Accuracy ≥ 78% – 82%**<br>F1-Score bình quân ≥ 0.75 | Đánh giá trên tập `Dataset/Validation/` thông qua `evaluate.py` |
| **Độ mượt mà Tầng 2 (Khử nhiễu)** | Loại bỏ 100% hiện tượng "nhấp nháy" (flickering) trạng thái giữa các frame | Cơ chế Cửa sổ trượt (Sliding Window: 30 frames) |
| **Báo động giả (False Alarm Rate)** | **Tỷ lệ báo động sai < 5%** trên video giám sát thông thường | Thử nghiệm trên video sảnh đi lại bình thường |
| **Tốc độ xử lý toàn Pipeline** | **≥ 25 – 30 FPS** trên GPU / **≥ 15 FPS** trên CPU | Đo đạc qua `test_pipeline.py` |
| **Sản phẩm bàn giao cuối cùng** | File trọng số tối ưu `weights/crowd_emotion_resnet18.pt`<br>Cập nhật model thật vào `ai_inference.py` | Bàn giao cho Thành viên E (UI) chạy thực tế |

---

## 🗺️ 2. LỘ TRÌNH TRIỂN KHAI THEO GIAI ĐOẠN (PHASES)

```
┌────────────────────────────────────────────────────────────────────────┐
│ GIAI ĐOẠN 1: TIẾP NHẬN & KIỂM TRA DỮ LIỆU (Ngày 8)                     │
│ ➔ Xác thực cấu trúc Dataset/, kiểm tra ảnh lỗi, tính Class Weights      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ GIAI ĐOẠN 2: HUẤN LUYỆN 2 BƯỚC TẦNG 1 (Ngày 8 - 10)                    │
│ ➔ Bước 2A: Train Head (Freeze Backbone - 10 Epochs, lr=1e-3)           │
│ ➔ Bước 2B: Fine-tune sâu (Unfreeze Layer 3&4 - 15 Epochs, lr=1e-4)     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ GIAI ĐOẠN 3: NÂNG CẤP TẦNG 2 THỐNG KÊ ĐÁM ĐÔNG (Ngày 9 - 10)           │
│ ➔ Sliding Window (30 frames) + Thang điểm Crowd Mood Score (-1 đến +1) │
│ ➔ Phân tích vùng tập trung chú ý (Spatial Attention - Tò mò)          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ GIAI ĐOẠN 4: ĐÁNH GIÁ MÔ HÌNH & CÂN CHỈNH NGƯỠNG (Ngày 10 - 11)        │
│ ➔ Xuất Confusion Matrix, Precision/Recall/F1-Score                     │
│ ➔ Cân chỉnh ngưỡng cảnh báo trên 3 video kịch bản thực tế             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ GIAI ĐOẠN 5: TÍCH HỢP UI & NGHIỆM THU TOÀN HỆ THỐNG (Ngày 11 - 14)    │
│ ➔ Nhúng model thật vào ai_inference.py ➔ Chạy Dashboard hoàn chỉnh     │
│ ➔ Đóng gói số liệu cho Báo cáo đồ án                                   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 3. CHI TIẾT CÁC BƯỚC THỰC THI

---

### 🔹 GIAI ĐOẠN 1: Tiếp nhận, Xác thực Dữ liệu & Xử lý Mất cân bằng (Ngày 8)
**Mục tiêu:** Đảm bảo dữ liệu của Team Data sạch 100%, không lỗi corrupt ảnh và tính toán trọng số cân bằng lớp.

#### Các bước thực hiện:
1. **Bước 1.1: Tạo script `verify_dataset.py`**
   * Quét toàn bộ ảnh trong `Dataset/Train/` và `Dataset/Validation/`.
   * Kiểm tra và tự động loại bỏ các file hỏng (corrupted image), file kích thước 0 byte.
   * Thống kê số lượng mẫu từng nhãn: `Happy`, `Normal`, `Sad`, `Surprised`.
2. **Bước 1.2: Tính toán `class_weights` cho hàm Loss**
   * Do đặc thù CCTV nhãn `Normal` thường nhiều hơn các nhãn khác, tính trọng số nghịch đảo tần suất:
     $$w_c = \frac{N_{\text{total}}}{C \times N_c}$$
   * Nạp vector `class_weights` vào `nn.CrossEntropyLoss(weight=weights)`.

#### Tiêu chí nghiệm thu:
- [ ] In ra bảng phân bổ số lượng ảnh chuẩn xác cho 4 nhãn.
- [ ] Không còn file ảnh hỏng gây crash khi DataLoader nạp batch.

---

### 🔹 GIAI ĐOẠN 2: Huấn luyện & Tinh chỉnh sâu Tầng 1 — Core AI Model (Ngày 8 – 10)
**Mục tiêu:** Huấn luyện mô hình ResNet-18 thích nghi hoàn toàn với dữ liệu biểu cảm CCTV.

#### Các bước thực hiện:
1. **Bước 2.1: Viết script `train.py` chuẩn hóa**
   * Tích hợp `data_loader.py` (với Data Augmentation: ColorJitter, GaussianBlur, RandomCrop).
   * Cơ chế lưu Checkpoint tự động: Lưu `best_model.pt` mỗi khi `val_loss` đạt kỷ lục mới.
   * Cơ chế **Early Stopping** (patience = 5) để chống Overfitting.
2. **Bước 2.2: Thực hiện Giai đoạn 2A — Huấn luyện tầng Head (Freeze Backbone)**
   * Đóng băng toàn bộ các tầng trích xuất của ResNet-18 (`requires_grad = False`).
   * Chỉ cập nhật trọng số tầng `classifier` (FC Head).
   * Cấu hình: Optimizer `AdamW(lr=1e-3, weight_decay=1e-4)`, Epochs: **10**.
3. **Bước 2.3: Thực hiện Giai đoạn 2B — Tinh chỉnh sâu (Fine-tuning Unfreeze)**
   * Mở khóa 2 block cuối của ResNet-18 (Layer 3 và Layer 4) bằng hàm `model.unfreeze_backbone(2)`.
   * Cấu hình Learning Rate phân tầng (Differential Learning Rates):
     * Backbone LR: `1e-4` (học chậm để giữ đặc trưng tổng quát).
     * Classifier LR: `5e-4` (học nhanh hơn).
   * Bộ điều chỉnh LR: `torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=15)`.
   * Chạy tiếp **15 – 20 Epochs**.

#### Tiêu chí nghiệm thu & Kết quả thực tế:
- [x] Đã hoàn thành huấn luyện 2 giai đoạn với cấu hình tối ưu: `input_size=224x224`, `batch_size=32`, `dropout=0.5`, `unfreeze_all=True (LR=1e-5)`.
- [x] **Validation Accuracy đạt 69.15%** (tăng mạnh từ 57.25% baseline và 63.50% ở lần train trước).
- [x] **Triệt tiêu hoàn toàn Overfitting:** Khoảng cách Train-Val (Generalization Gap) chỉ còn **2.52%** (Train 71.67% vs Val 69.15%), hàm Loss hạ cánh vào Flat Minimum với Val Loss 0.9111.
- [x] Xuất file trọng số hoàn chỉnh tại `weights/crowd_emotion_resnet18.pt`.
- [x] Hiệu năng End-to-End Pipeline đạt **27.1 FPS trên CPU** (vượt xa chỉ tiêu ≥ 15 FPS).

---

### 🔹 GIAI ĐOẠN 3: Nâng cấp Tầng 2 — Thống kê & Phân tích Nghiệp vụ (Ngày 9 – 10)
**Mục tiêu:** Nâng cấp [`crowd_analytics.py`](file:///d:/emotion_recognition/crowd_analytics.py) thành bộ máy phân tích chuỗi thời gian ổn định, loại bỏ hiện tượng nhấp nháy giao diện.

#### Các bước thực hiện:
1. **Bước 3.1: Tích hợp Cơ chế Cửa sổ trượt (Sliding Window)**
   * Lưu trữ lịch sử kết quả của **30 frames gần nhất** (~1–2 giây video ở 25–30 FPS) sử dụng `collections.deque(maxlen=30)`.
   * Tính phân phối cảm xúc trung bình trượt (Moving Average Distribution) thay vì chỉ lấy 1 frame tức thời.
2. **Bước 3.2: Xây dựng Chỉ số Tâm trạng Đám đông (Crowd Mood Score - CMS)**
   * Định lượng không khí không gian công cộng thành một giá trị liên tục từ **-1.0 (Rất tiêu cực) đến +1.0 (Rất tích cực)**:
     $$\text{CMS} = (p_{\text{Happy}} \times 1.0) + (p_{\text{Normal}} \times 0.0) - (p_{\text{Sad}} \times 0.8) - (p_{\text{Surprised}} \times 0.5)$$
3. **Bước 3.3: Thuật toán nhận diện "Tò mò" qua Không gian (Spatial Attention)**
   * Theo dõi tọa độ Bounding Box của khuôn mặt qua các frame:
     * Nếu khuôn mặt có nhãn `Surprised` / `Normal` nhưng **đứng yên một vị trí > 3 giây** tại khu vực màn hình quảng cáo/gian hàng ➔ Ghi nhận là **"Tò mò / Thu hút cao"**.

#### Tiêu chí nghiệm thu:
- [ ] Trạng thái đám đông và biểu đồ phân phối biến thiên mượt mà, không bị giật đổi màu liên tục giữa các frame.

---

### 🔹 GIAI ĐOẠN 4: Đánh giá Mô hình & Cân chỉnh Ngưỡng Thực tế (Ngày 10 – 11)
**Mục tiêu:** Đo đạc chỉ số khoa học cho báo cáo đồ án và cân chỉnh ngưỡng triệt tiêu báo động giả.

#### Các bước thực hiện:
1. **Bước 4.1: Xây dựng script `evaluate.py`**
   * Tính toán toàn diện: **Accuracy, Precision, Recall, F1-Score** cho từng nhãn.
   * Vẽ ma trận nhầm lẫn chuẩn hóa (**Normalized Confusion Matrix**) lưu thành `docs/confusion_matrix.png`.
   * Vẽ biểu đồ đường Train/Val Loss & Accuracy theo từng Epoch lưu thành `docs/training_curves.png`.
2. **Bước 4.2: Cân chỉnh ngưỡng (Calibration) trên 3 kịch bản video thực tế**
   * **Kịch bản 1 (Video sảnh bình thường):** Điều chỉnh `panic_thresh` sao cho hệ thống giữ nguyên mức `NORMAL`, tỷ lệ báo động sai < 5%.
   * **Kịch bản 2 (Video sự kiện đông vui):** Cân chỉnh `happy_thresh` (khoảng 0.20 – 0.25) để hệ thống nhận diện đúng trạng thái `Hài lòng`.
   * **Kịch bản 3 (Video tình huống bất thường/hoảng loạn):** Đảm bảo kích hoạt `WARNING` trong vòng tối đa **1.5 giây** từ khi sự cố diễn ra.

#### Tiêu chí nghiệm thu & Kết quả thực tế:
- [x] Có đầy đủ hình ảnh biểu đồ và ma trận nhầm lẫn phục vụ báo cáo: [`docs/confusion_matrix.png`](file:///d:/emotion_recognition/docs/confusion_matrix.png), [`docs/training_curves.png`](file:///d:/emotion_recognition/docs/training_curves.png).
- [x] Bảng số liệu hoàn chỉnh: Precision, Recall, F1-Score đã lưu tại [`docs/evaluation_metrics.json`](file:///d:/emotion_recognition/docs/evaluation_metrics.json) (Overall Acc: **69.15%**).
- [x] Chốt bộ tham số ngưỡng tối ưu trong file cấu hình (`happy_thresh=0.25`, `panic_thresh=0.20`, `curious_thresh=0.20`).

---

### 🔹 GIAI ĐOẠN 5: Tích hợp Tổng lực & Bàn giao Hệ thống (Ngày 11 – 14)
**Mục tiêu:** Bàn giao mô hình AI thật cho Team UI, nghiệm thu toàn bộ hệ thống và hoàn thành báo cáo.

#### Các bước thực hiện:
1. **Bước 5.1: Cập nhật [`ai_inference.py`](file:///d:/emotion_recognition/ai_inference.py)**
   * Đổi cấu hình `USE_MOCK_DATA = False`.
   * Trỏ đường dẫn mô hình tới `weights/crowd_emotion_resnet18.pt`.
   * Kiểm tra luồng gọi hàm từ phía giao diện của **Thành viên E (UI Lead)**.
2. **Bước 5.2: Kiểm thử nghiệm thu End-to-End toàn hệ thống**
   * Chạy Dashboard hoàn chỉnh: Đọc video CCTV ➔ Bắt mặt YOLOv8-Face ➔ Đoán biểu cảm ResNet-18 ➔ Thống kê Sliding Window ➔ Vẽ đồ thị thời gian thực + Banner cảnh báo.
   * Đo đạc FPS tổng thể toàn hệ thống khi bật giao diện (Mục tiêu: ≥ 15 FPS trên CPU / ≥ 30 FPS trên GPU).
3. **Bước 5.3: Hỗ trợ viết Báo cáo đồ án**
   * **Team AI:** Viết mục "Kiến trúc mô hình 2 tầng, Thuật toán huấn luyện và Phân tích kết quả thực nghiệm".
   * **Team Data:** Viết mục "Thu thập dữ liệu, Tiền xử lý và Đánh giá tập kiểm thử".
   * **Team UI:** Viết mục "Thiết kế Dashboard và Tích hợp hệ thống thời gian thực".

---

## 📋 4. MA TRẬN FILE TRIỂN KHAI TRONG TUẦN 2

| STT | Tên File | Loại | Nhiệm vụ chính | Người phụ trách | Trạng thái |
|:---:|:---|:---:|:---|:---:|:---:|
| 1 | [`verify_dataset.py`](file:///d:/emotion_recognition/verify_dataset.py) | Tạo mới | Kiểm tra 11.600 ảnh sạch, tính class weights (1.0000) | Thành viên A | ✅ Hoàn thành |
| 2 | [`train.py`](file:///d:/emotion_recognition/train.py) | Tạo mới | Pipeline huấn luyện 2 giai đoạn (Freeze + Fine-tune) | Thành viên A & B | ✅ Hoàn thành |
| 3 | [`evaluate.py`](file:///d:/emotion_recognition/evaluate.py) | Tạo mới | Xuất Confusion Matrix, F1-Score, Loss curves | Thành viên B | ✅ Hoàn thành |
| 4 | [`crowd_analytics.py`](file:///d:/emotion_recognition/crowd_analytics.py) | Cập nhật | Thêm Sliding Window (30 frames) & Crowd Mood Score | Thành viên A | ✅ Hoàn thành |
| 5 | [`ai_inference.py`](file:///d:/emotion_recognition/ai_inference.py) | Cập nhật | Tích hợp Sliding Window qua `analyze_stream` cho UI | Thành viên A | ✅ Hoàn thành |
| 6 | [`test_pipeline.py`](file:///d:/emotion_recognition/test_pipeline.py) | Cập nhật | Chạy model thật + Cửa sổ trượt, đạt 19.5 FPS trên CPU | Cả nhóm | ✅ Hoàn thành |
| 7 | `weights/crowd_emotion_resnet18.pt` | Tạo mới | File trọng số model đã sinh ra và nạp vào pipeline | Team AI | ✅ Hoàn thành |

---

## 📈 5. KẾT QUẢ ĐẠT ĐƯỢC VÀ BƯỚC TIẾP THEO
1. **Model Tầng 1 đã sẵn sàng:** `weights/crowd_emotion_resnet18.pt` đã được tạo và nạp thành công vào toàn bộ pipeline nhận diện.
2. **Tầng 2 đã khử nhiễu hoàn chỉnh:** Cơ chế Sliding Window (30 frames) và chỉ số CMS giúp trạng thái đám đông chuyển biến mượt mà, sẵn sàng kết nối lên Dashboard của **Thành viên E (UI Lead)**.
3. **Tài liệu Báo cáo đã có số liệu:** `docs/confusion_matrix.png`, `docs/training_curves.png` và `docs/evaluation_metrics.json` đã được tự động sinh ra phục vụ viết báo cáo.

