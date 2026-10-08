Để mô hình **học tốt và hoạt động chính xác trên camera CCTV thực tế** (thay vì chỉ học vẹt trên ảnh chụp đẹp trong phòng lab), Team Data cần nắm rõ đặc thù của bài toán. 

Khuôn mặt cắt ra từ camera CCTV góc rộng treo cao sẽ **rất nhỏ (30–80px), mờ do chuyển động, ánh sáng phức tạp và góc nhìn nghiêng/cúi đầu**. Nếu Team Data chỉ tải ảnh selfie hoặc chân dung chất lượng cao, mô hình sẽ gặp hiện tượng **Domain Shift** (đạt 95% độ chính xác khi train nhưng khi cắm camera CCTV thật vào thì đoán sai toàn bộ).

Dưới đây là cẩm nang hướng dẫn chi tiết từ AI Lead gửi Team Data (Thành viên C & D):

---

### 1. Chiến lược phối trộn dữ liệu: Quy tắc 70 - 30

Tuyệt đối không lấy 100% dữ liệu từ một nguồn duy nhất. Tỷ lệ tối ưu nhất để train trong 2 tuần:

* **70% Dữ liệu nền tảng (Foundation Data) từ các bộ dữ liệu mở chuẩn quốc tế:**
  * **Nguồn khuyên dùng:** **RAF-DB** (Real-world Affective Faces Database) hoặc **FER-2013**, **AffectNet**. 
  * Đây là những tập dữ liệu khuôn mặt tự nhiên ngoài đời thực (in-the-wild) đã được gán nhãn chuẩn hóa, giúp mạng ResNet-18 học vững các biểu cảm cơ bản.
* **30% Dữ liệu thực chiến CCTV (Surveillance Domain Data):**
  * **Nguồn:** Trích xuất từ bộ dữ liệu giám sát **ChokePoint**, **SCface** hoặc cắt từ 10–15 video hành lang/sảnh CCTV góc rộng trên YouTube.
  * Đây là "vũ khí bí mật" giúp mô hình quen với góc nhìn từ trên cao xuống (Top-down view), ánh sáng đèn trần và độ mờ khi người đi lại.

---

### 2. Dùng chính `face_detector.py` để trích xuất ảnh CCTV (Bí quyết quan trọng nhất!)

> [!IMPORTANT]
> **Khuyến nghị sống còn:** Team Data **KHÔNG NÊN** dùng chuột cắt khuôn mặt thủ công bằng tay!

* **Lý do:** Khi cắt bằng tay, con người thường cắt rất nắn nót, căn giữa hoàn hảo. Nhưng khi hệ thống chạy thực tế, khuôn mặt được cắt bởi **YOLOv8-Face** (có độ lệch nhẹ, viền bounding box có thể dính tóc, trán hoặc cổ).
* **Cách làm đúng:** Team Data hãy lấy chính file [`face_detector.py`](file:///d:/emotion_recognition/face_detector.py) mà Team AI vừa viết, chạy quét qua các video CCTV thu thập được để **tự động cắt và lưu ra các khuôn mặt**. Sau đó Thành viên C và D chỉ việc nhặt ảnh vào đúng 4 thư mục nhãn. Cách này vừa nhanh gấp 10 lần, vừa đảm bảo dữ liệu train đồng nhất 100% với lúc inference!

---

### 3. Số lượng mẫu & Cân bằng nhãn (Class Balance)

Để train tốt với backbone ResNet-18 trong Tuần 2:

* **Quy mô mục tiêu:** 
  * **Tập Train:** Khoảng **1,500 – 2,500 ảnh / mỗi nhãn** (Tổng tập Train: 6,000 – 10,000 ảnh).
  * **Tập Validation:** Khoảng **300 – 500 ảnh / mỗi nhãn** (Tổng tập Val: ~1,500 – 2,000 ảnh).
  * Tỷ lệ chia chuẩn: **80% Train — 20% Validation**.
* **Đảm bảo cân bằng giữa các nhãn:**
  * Tránh tình trạng nhãn `Normal` có 5,000 ảnh trong khi `Surprised` chỉ có 300 ảnh. Mất cân bằng nặng sẽ khiến mô hình có xu hướng luôn đoán là "Normal".
  * Tỷ lệ phân bố lý tưởng giữa 4 nhãn:
    * `Normal`: ~35% (cho phép nhỉnh hơn vì thực tế CCTV người bình thường chiếm đa số).
    * `Happy`: ~25%.
    * `Sad`: ~20%.
    * `Surprised`: ~20%.

---

### 4. Quy tắc ánh xạ (Mapping) từ các Dataset quốc tế

Khi tải các bộ dữ liệu FER-2013, RAF-DB hay AffectNet về, Team Data lọc vào 4 thư mục theo quy tắc sau:

| Thư mục dự án | Lấy từ nhãn của Dataset chuẩn | Lưu ý khi chọn ảnh |
|:---|:---|:---|
| `Happy/` | Nhãn `Happy` | Lấy đa dạng: Cười tươi thấy răng, mỉm cười nhẹ, vừa đi vừa cười. |
| `Normal/` | Nhãn `Neutral` | Khuôn mặt thả lỏng, không biểu cảm, nhìn thẳng hoặc nhìn xuống khi đi bộ. |
| `Sad/` | Nhãn `Sad` (+ một phần `Anger`/`Disgust`) | Mặt nhăn nhó, khóe miệng trễ xuống, lông mày cụp, thể hiện sự mệt mỏi, khó chịu. |
| `Surprised/` | Nhãn `Surprise` (+ một phần `Fear`) | Mắt mở to, nhướng mày, miệng há tròn (kinh ngạc hoặc hoảng hốt). |

---

### 5. Tiêu chuẩn chất lượng ảnh (Quality Checklist cho Team Data)

Trước khi đóng gói bàn giao vào cuối ngày thứ 7, Team Data cần rà soát:

- [ ] **Định dạng & Kích thước:** Ảnh dạng `.jpg` hoặc `.png`, không lọc bỏ ảnh nhỏ (chấp nhận ảnh từ `40×40` trở lên, không cần phóng to quá mức vì [`data_loader.py`](file:///d:/emotion_recognition/data_loader.py) sẽ tự xử lý).
- [ ] **Chất lượng ảnh:** Giữ lại các ảnh có độ mờ nhẹ (motion blur), ảnh hơi tối hoặc ngược sáng (đây là dữ liệu rất quý cho CCTV). Chỉ loại bỏ các ảnh quá vỡ hạt không thể nhận ra người.
- [ ] **Không trùng lặp giữa Train và Validation:** Ảnh của cùng một người trong một đoạn clip ngắn chỉ được nằm ở Train **HOẶC** Validation, không để người đó xuất hiện ở cả hai tập (tránh hiện tượng Data Leakage làm ảo chỉ số độ chính xác).

---

### 6. Cấu trúc đóng gói bàn giao cuối cùng

Toàn bộ dữ liệu bàn giao đặt trong thư mục `Dataset/` ở thư mục gốc của dự án:

```
d:\emotion_recognition\Dataset\
├── 📂 Train/
│   ├── 📂 Happy/       (chứa ~2000 ảnh: happy_0001.jpg, ...)
│   ├── 📂 Normal/      (chứa ~2500 ảnh)
│   ├── 📂 Sad/         (chứa ~1500 ảnh)
│   └── 📂 Surprised/   (chứa ~1500 ảnh)
└── 📂 Validation/
    ├── 📂 Happy/       (chứa ~400 ảnh)
    ├── 📂 Normal/      (chứa ~500 ảnh)
    ├── 📂 Sad/         (chứa ~300 ảnh)
    └── 📂 Surprised/   (chứa ~300 ảnh)
```

> 💡 **Mẹo:** Ngay khi Team Data chuẩn bị xong, chỉ cần chạy lệnh `python data_loader.py` — script sẽ tự động kiểm tra xem cấu trúc dữ liệu đã đạt chuẩn hay chưa chỉ trong 3 giây!