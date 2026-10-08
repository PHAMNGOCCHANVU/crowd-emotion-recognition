# ĐỀ TÀI: Hệ thống AI phân tích biểu cảm thời gian thực từ Camera CCTV góc rộng phục vụ An ninh & Đánh giá trải nghiệm không gian công cộng

## 🎯 Ý tưởng & Mục tiêu
Ứng dụng AI để phân tích biểu cảm thời gian thực của những người di chuyển qua hành lang, sảnh sự kiện hoặc cửa ra vào qua hệ thống camera góc rộng treo cao. Hệ thống giám sát và phản ánh các trạng thái đám đông:
- **Đánh giá trải nghiệm không gian:** Mức độ **Hài lòng** (dòng người vui vẻ, thoải mái) và mức độ **Tò mò / Thu hút** (chú ý vào gian hàng, biển quảng cáo).
- **Cảnh báo an ninh sớm:** Phát hiện trạng thái **Hoang mang / Bất thường** (dấu hiệu hoảng loạn, sợ hãi, chen lấn, sự cố).
- **Trạng thái nền tảng:** Duy trì dòng lưu thông **Bình thường / Ổn định** (chiếm 80-90% lưu lượng).

---

## 🏗️ Kiến trúc Kỹ thuật Phân tầng (2-Tier Architecture)

Nhằm đảm bảo tính chính xác và tránh suy diễn chủ quan ở cấp độ khuôn mặt từ camera xa, dự án áp dụng mô hình 2 tầng:

1. **Tầng 1 - Core AI Model (Inference khuôn mặt):**
   * **Phát hiện khuôn mặt:** Sử dụng **YOLOv8-Face** (hoặc RetinaFace) để bắt chính xác các khuôn mặt kích thước nhỏ, góc nhìn từ trên cao xuống (Top-down) và bị che khuất một phần.
   * **Nhận diện biểu cảm:** Mô hình CNN (ResNet-18 Backbone) nhận diện **4 biểu cảm cơ bản chuẩn hóa quốc tế**: `Happy` (Vui vẻ), `Normal` (Bình thường), `Sad` (Buồn/Căng thẳng), `Surprised` (Kinh ngạc/Bất ngờ).
   * **Data Augmentation:** Tăng cường độ sáng, làm mờ, nhiễu hạt để thích nghi với môi trường ánh sáng phức tạp của CCTV.

2. **Tầng 2 - Crowd Analytics & Alert (Thống kê & Cảnh báo ngưỡng):**
   * Tổng hợp phân phối xác suất các biểu cảm cá nhân theo từng khung hình và cửa sổ thời gian (Sliding Window):
     * **Ổn định / Bình thường:** Khi tỷ lệ `Normal > 75%`.
     * **Hài lòng:** Khi tỷ lệ `Happy > 25%` ➔ Đánh giá sự kiện/dịch vụ đạt trải nghiệm tốt.
     * **Cảnh báo Hoang mang / Sự cố an ninh:** Khi tỷ lệ `Surprised` hoặc `Sad` tăng đột biến (> 20%) ➔ Kích hoạt còi/banner cảnh báo an ninh.
     * **Tò mò / Thu hút cao:** Khi tỷ lệ `Surprised` tập trung cao tại khu vực đặt màn hình/gian hàng.

---

## 👥 Phân công Phát triển Kỹ thuật từ Repo patrikken
* **Thành viên A & B (AI Team):** 
  * Thay thế Haar Cascade cũ bằng **YOLOv8-Face**.
  * Thay backbone nhỏ của tác giả bằng **ResNet-18** pre-trained, phân loại 4 nhãn (`Happy, Normal, Sad, Surprised`).
  * Xây dựng module `crowd_analytics.py` tính toán tỷ lệ và kích hoạt cảnh báo ngưỡng đám đông.
  * Cung cấp interface `ai_inference.py` bàn giao cho Team UI.
* **Thành viên C & D (Data Team):**
  * Tận dụng các bộ dữ liệu khuôn mặt lớn chuẩn quốc tế (FER-2013, RAF-DB, AffectNet) gom vào 4 nhãn chuẩn, giải phóng áp lực gán nhãn thủ công.
  * Thu thập và cắt clip CCTV góc rộng thực tế (ChokePoint, SCface, YouTube) để làm tập Test đánh giá thực nghiệm.
* **Thành viên E (UI/System):** 
  * Xây dựng luồng xử lý video (Video Streaming Pipeline) ổn định từ camera IP/file video.
  * Thiết kế giao diện Dashboard: Hiển thị luồng video có Bounding Box, biểu đồ mật độ cảm xúc đám đông theo thời gian (Time-series chart) và hộp cảnh báo an ninh tự động.

---

## 📈 Độ khả thi
* **Độ khả thi: 90% (Rất cao).** 
* Việc giữ 4 nhãn chuẩn hóa ở tầng Core AI giúp tận dụng 100% dữ liệu học thuật có sẵn, loại bỏ sai lệch gán nhãn chủ quan. Tách riêng logic đám đông lên tầng Thống kê giúp hệ thống vừa khoa học, vừa đáp ứng trực tiếp nghiệp vụ An ninh và Trải nghiệm không gian.

