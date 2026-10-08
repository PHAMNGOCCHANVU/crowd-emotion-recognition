Để nén toàn bộ khối lượng công việc của dự án AI Wall-CCTV Monitor (phát triển từ repo patrikken) vào đúng 2 tuần, nhóm bạn cần áp dụng một lịch trình "cuốn chiếu" cực kỳ nghiêm ngặt theo **Kiến trúc Phân tầng (2-Tier Architecture)**:
- **Tầng 1 (AI Core):** Nhận diện 4 biểu cảm cơ bản chuẩn hóa (`Happy, Normal, Sad, Surprised`) từ khuôn mặt bắt bởi YOLOv8-Face.
- **Tầng 2 (Crowd Analytics & Alert):** Thống kê phân phối cảm xúc và kích hoạt trạng thái đám đông (**Hài lòng, Hoang mang, Tò mò, Bình thường**) cùng cảnh báo an ninh.

Dưới đây là bảng phân chia công việc chi tiết theo từng ngày cho 5 thành viên để đảm bảo hoàn thành đúng hạn:

------------------------------
## 📅 TUẦN 1: Chuẩn Bị Dữ Liệu & Nâng Cấp Mô Hình Nền Tảng
**Mục tiêu cuối tuần 1:** Có tập dữ liệu 4 nhãn chuẩn hoàn chỉnh + Mô hình AI đã tích hợp YOLOv8-Face và ResNet-18 + Module thống kê đám đông + Giao diện Dashboard khung sườn kết nối qua Mock Data.

## 🧑‍💻 Team AI (Thành viên A & B)

* **Ngày 1 - 2:** Clone repo patrikken, chạy thử với webcam/video để hiểu cấu trúc đầu vào/đầu ra. Tách riêng phần mạng Backbone và đánh giá hiệu năng so với ResNet-18 pre-trained.
* **Ngày 3 - 4:** Gỡ bỏ Haar Cascade mặc định của repo. Nhúng mã nguồn **YOLOv8-Face** vào để làm nhiệm vụ phát hiện khuôn mặt cự ly xa và góc nghiêng từ camera CCTV.
* **Ngày 5 - 7:** 
  * Xây dựng mô hình với tầng phân loại 4 nhãn chuẩn (`Happy, Normal, Sad, Surprised`) dùng ResNet-18 Backbone.
  * Viết module `crowd_analytics.py` (Tier 2) xử lý ngưỡng kích hoạt trạng thái đám đông (Hài lòng khi Happy cao; Hoang mang khi Surprised/Sad tăng đột biến; Tò mò khi Surprised tập trung trước biển quảng cáo).
  * Viết script Data Loader nạp dữ liệu 4 nhãn chuẩn sẵn sàng chờ Team Data.
  * Bàn giao interface `ai_inference.py` (trả về Mock Data) cho Thành viên E.

## 📊 Team Data (Thành viên C & D)

* **Ngày 1 - 2:** Tải các bộ dữ liệu khuôn mặt học thuật chuẩn quốc tế (**FER-2013, RAF-DB, AffectNet**). Thu thập thêm 10-15 video CCTV góc rộng, hành lang đi lại thực tế (ChokePoint, SCface, YouTube).
* **Ngày 3 - 5 (Trích xuất & Đóng gói dữ liệu):** Lọc và sắp xếp các ảnh khuôn mặt từ các bộ dữ liệu chuẩn vào đúng 4 thư mục nhãn: `Happy`, `Normal` (từ Neutral), `Sad`, `Surprised` (từ Surprise). Cắt trích xuất các khuôn mặt từ video CCTV thực tế để chuẩn bị tập dữ liệu Test.
* **Ngày 6 - 7:** Áp dụng các kỹ thuật Data Augmentation (thêm nhiễu hạt, làm mờ chuyển động, thay đổi độ sáng CCTV). Đóng gói dữ liệu theo đúng cấu trúc `Dataset/{Train, Validation}/{Happy, Normal, Sad, Surprised}` và bàn giao toàn bộ cho Team AI vào cuối ngày 7.

## 💻 Team UI/System (Thành viên E)

* **Ngày 1 - 2:** Thiết kế Mockup giao diện Dashboard giám sát (vùng hiển thị video camera, khung cảnh báo an ninh, bảng phân phối % cảm xúc và khu vực vẽ biểu đồ thời gian thực).
* **Ngày 3 - 5:** Sử dụng Streamlit (hoặc Flask/FastAPI + OpenCV) dựng khung giao diện chạy thực tế theo Mockup. Viết module kết nối và đọc luồng video đầu vào (Video Streaming Pipeline) từ file video test hoặc camera IP.
* **Ngày 6 - 7:** Tích hợp với hàm `predict_emotion_from_frame()` từ `ai_inference.py` của Team AI (nhận Mock Data): Vẽ bounding box khuôn mặt lên video và vẽ biểu đồ biến thiên mật độ cảm xúc đám đông (Time-series chart) cùng widget cảnh báo an ninh tự động.

------------------------------
## 📅 TUẦN 2: Huấn Luyện, Tích Hợp Hệ Thống & Viết Báo Cáo
**Mục tiêu cuối tuần 2:** Mô hình train xong + Nhúng hoàn chỉnh vào giao diện + Chạy nghiệm thu hệ thống mượt mà và đóng gói báo cáo.

## 🧑‍💻 Team AI (Thành viên A & B)

* **Ngày 8 - 10 (Huấn luyện mô hình):** Nạp dữ liệu 4 nhãn từ Team Data. Tiến hành khóa các tầng trích xuất (Freeze ResNet-18) và huấn luyện tầng phân loại trên tập dữ liệu. Tối ưu hóa siêu tham số (Learning rate, Batch size) để đạt Accuracy tốt nhất.
* **Ngày 11:** Xuất bản mô hình thành file trọng số cuối cùng (`.pt` hoặc `.onnx`). Cập nhật model thật vào `ai_inference.py`, thay thế Mock Data mà không làm thay đổi interface với UI.
* **Ngày 12 - 14:** Hỗ trợ Thành viên E tinh chỉnh FPS và tối ưu pipeline. Viết chương "Kiến trúc mô hình phân tầng và Thuật toán nhận diện - phân tích đám đông" cho cuốn báo cáo đồ án.

## 📊 Team Data (Thành viên C & D)

* **Ngày 8 - 10:** Hoàn thiện tập dữ liệu video CCTV thực tế (chưa từng dùng để train) để làm dữ liệu kiểm thử thực tế (Test set). Bắt đầu viết chương "Cơ sở dữ liệu, Thu thập và Tiền xử lý ảnh" cho báo cáo đồ án.
* **Ngày 11 - 12 (Kiểm thử viên):** Đóng vai trò Tester độc lập. Lấy tập video test chạy trực tiếp trên ứng dụng đã tích hợp để đánh giá các chỉ số độ chính xác (Accuracy, Precision, Recall, F1-Score). Ghi nhận các trường hợp cảnh báo an ninh kích hoạt đúng/sai.
* **Ngày 13 - 14:** Hoàn thiện các biểu đồ đánh giá chất lượng mô hình, viết chương "Kết quả thực nghiệm & Phân tích đám đông" và tổng hợp tài liệu tham khảo cho cuốn báo cáo.

## 💻 Team UI/System (Thành viên E)

* **Ngày 8 - 10:** Tối ưu hóa luồng OpenCV để đảm bảo việc đọc frame không bị nghẽn (thắt cổ chai). Chuẩn bị sẵn logic hiển thị cảnh báo khi nhận tín hiệu `alert_level == "WARNING"`.
* **Ngày 11 - 12 (Tích hợp tổng lực):** Bật model thật từ Team AI. Kết nối luồng dữ liệu thời gian thực từ AI sang biểu đồ mật độ cảm xúc và banner cảnh báo an ninh. Đảm bảo toàn hệ thống đạt tốc độ xử lý (FPS) mượt mà (≥ 12-15 FPS).
* **Ngày 13 - 14:** Fix các lỗi giao diện, tối ưu độ trễ luồng stream. Viết chương "Thiết kế và Triển khai hệ thống ứng dụng giám sát đám đông" cho báo cáo đồ án.

------------------------------
## 💡 Quy tắc "sống còn" để hoàn thành đúng hạn 2 tuần

1. **Giao tiếp liên tục bằng API/Định dạng chung:** Ngay ngày đầu tiên, Thành viên A (AI) và Thành viên E (UI) đã thống nhất định dạng dữ liệu trong `ai_inference.py` (trả về danh sách `faces` và dict `crowd_insights`). Nhờ vậy, hai team code hoàn toàn độc lập qua Mock Data trong Tuần 1.
2. **Họp nhanh (Daily Stand-up):** Cuối mỗi ngày, cả nhóm dành ra 5-10 phút nhắn tin hoặc gọi điện để báo cáo nhanh: Hôm nay đã làm được gì? Có bị kẹt ở lỗi kỹ thuật nào không? để giải quyết ngay lập tức, tránh dồn việc sang tuần sau.

