# Báo cáo nhiệm vụ ngày 6–7 đã cập nhật

**Task02 – Thiên Trường · Cập nhật 26/09/2026**

## 1. Yêu cầu thực hiện

Theo tài liệu trong `update/`, ngày 6–7 gồm:

1. Áp dụng nhiễu hạt, mờ chuyển động và thay đổi ánh sáng để ảnh gần điều kiện CCTV.
2. Chia ảnh gốc theo tỷ lệ 80% Train và 20% Validation.
3. Đóng gói `Dataset/{Train,Validation}/{Happy,Normal,Sad,Surprised}`.
4. Giữ cân bằng lớp và tránh rò rỉ người/ảnh nguồn giữa hai tập.

## 2. Chia dữ liệu gốc

Đầu vào là 10.000 ảnh của ngày 3–5, cân bằng 2.500 ảnh mỗi lớp. Kết quả chia ảnh gốc:

| Lớp | Train gốc | Validation | Tổng gốc |
|---|---:|---:|---:|
| Happy | 2.000 | 500 | 2.500 |
| Normal | 2.000 | 500 | 2.500 |
| Sad | 2.000 | 500 | 2.500 |
| Surprised | 2.000 | 500 | 2.500 |
| **Tổng** | **8.000** | **2.000** | **10.000** |

FER-2013 và RAF-DB giữ split gốc. Với ExpW, tất cả khuôn mặt thuộc cùng một `source_file` được đưa vào cùng một tập. Các ảnh ExpW chứa nhiều lớp được giữ trong Train; Validation được chọn từ các nhóm ảnh nguồn đơn lớp để đạt đúng 500 ảnh mỗi lớp.

## 3. Data Augmentation

Chỉ tập Train được tăng cường. Mỗi lớp có thêm 400 ảnh:

| Phép biến đổi | Mỗi lớp | Toàn bộ bốn lớp |
|---|---:|---:|
| Nhiễu Gaussian | 100 | 400 |
| Mờ chuyển động | 100 | 400 |
| Giảm sáng | 100 | 400 |
| Ánh sáng không đều | 100 | 400 |
| **Tổng** | **400** | **1.600** |

Các phép biến đổi giữ nguyên kích thước ảnh. Seed được tạo ổn định từ đường dẫn và tên phép biến đổi nên có thể tái tạo kết quả khi chạy lại trên cùng dữ liệu.

## 4. Bộ dữ liệu cuối

| Tập | Số ảnh mỗi lớp | Tổng |
|---|---:|---:|
| Train | 2.400 | 9.600 |
| Validation | 500 | 2.000 |
| **Tổng** | **2.900** | **11.600** |

Số lượng Train 2.400 ảnh/lớp và Validation 500 ảnh/lớp nằm trong khoảng mục tiêu của tài liệu cập nhật.

## 5. Xử lý khuyến nghị 70/30

Tài liệu `xaydungbodulieu.docx` khuyến nghị 70% dữ liệu nền tảng và 30% dữ liệu CCTV để giảm domain shift. Tài liệu phân công đồng thời yêu cầu video CCTV chưa dùng để train nhằm làm tập Test.

Trong lần bàn giao này, Train/Validation chỉ dùng dữ liệu có ground truth từ FER-2013, RAF-DB và ExpW. Không đưa 50 crop CCTV chưa gán nhãn vào train để tránh nhãn giả và làm mất tính độc lập của tập test. Các crop đó được đóng gói tại `CCTV_Test_Unlabeled/` để gán ground truth và kiểm thử ở tuần 2.

## 6. Kết quả kiểm tra

`scripts/kiem_tra_ban_giao.py` đã kiểm tra toàn bộ đầu ra:

- 11.600/11.600 ảnh Dataset tồn tại và đọc được.
- 50/50 crop CCTV test tồn tại và đọc được.
- Không có đường dẫn đầu ra trùng.
- Không có ảnh nguồn xuất hiện ở cả Train và Validation.
- Validation không chứa ảnh tăng cường.
- Mỗi lớp có đủ 100 ảnh cho từng phép tăng cường.
- Mọi ảnh tăng cường đều khác ảnh cha và giữ nguyên kích thước.

Kết quả máy đọc được nằm trong `kiem_tra_ban_giao.json` với `passed: true`. SHA-256 của `dataset_manifest.csv` là `9db2613966751bfaab64e65dd7b11aceeb5f2338c45236e45d6b567016612d05`.

## 7. Tệp bàn giao cho Team AI

- `Dataset/`: dữ liệu train/validation dùng trực tiếp.
- `dataset_manifest.csv`: nguồn, split, nhãn gốc, phép tăng cường và quan hệ ảnh cha của 11.600 ảnh.
- `class_mapping.json`: thứ tự bốn lớp.
- `CCTV_Test_Unlabeled/`: 50 crop CCTV độc lập chưa có ground truth.
- `ket_qua_dong_goi.json`: thống kê quá trình đóng gói.
- `kiem_tra_ban_giao.json`: kết quả kiểm tra cuối.
- `xem_nhanh_augmentation.jpg`: ảnh tổng hợp bốn kỹ thuật tăng cường trên bốn lớp.

## 8. Kết luận

Nhiệm vụ ngày 6–7 đã hoàn thành. Dataset đã cân bằng, nằm đúng cấu trúc, có augmentation chỉ ở Train, không có rò rỉ ảnh nguồn và sẵn sàng bàn giao cho Team AI huấn luyện ResNet-18.

