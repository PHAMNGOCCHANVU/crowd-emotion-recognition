# Nhiệm vụ ngày 6–7 đã cập nhật

> **Trạng thái ngày 26/09/2026: hoàn thành.** Dữ liệu đã được chia, tăng cường và đóng gói theo cấu trúc Team AI yêu cầu.

## Kết quả bàn giao

| Tập | Happy | Normal | Sad | Surprised | Tổng |
|---|---:|---:|---:|---:|---:|
| Train | 2.400 | 2.400 | 2.400 | 2.400 | 9.600 |
| Validation | 500 | 500 | 500 | 500 | 2.000 |
| **Tổng** | **2.900** | **2.900** | **2.900** | **2.900** | **11.600** |

Mười nghìn ảnh gốc được chia 80/20: 8.000 train và 2.000 validation. Tập train được bổ sung 1.600 ảnh tăng cường, gồm 400 ảnh mỗi lớp. Vì augmentation chỉ áp dụng cho train, tỷ lệ của toàn bộ file sau tăng cường không còn đúng 80/20, nhưng tỷ lệ ảnh gốc vẫn đúng 80/20.

## Cấu trúc

```text
nv_ngay6_7/
├── Dataset/
│   ├── Train/
│   │   ├── Happy/
│   │   ├── Normal/
│   │   ├── Sad/
│   │   └── Surprised/
│   └── Validation/
│       ├── Happy/
│       ├── Normal/
│       ├── Sad/
│       └── Surprised/
├── CCTV_Test_Unlabeled/
│   ├── images/                    # 50 crop CCTV đạt tối thiểu 40 px
│   └── manifest.csv
├── scripts/
│   ├── dong_goi_ngay6_7.py
│   └── kiem_tra_ban_giao.py
├── dataset_manifest.csv
├── class_mapping.json
├── ket_qua_dong_goi.json
├── kiem_tra_ban_giao.json
├── xem_nhanh_augmentation.jpg
└── bao_cao_ngay_6_7.md
```

## Tăng cường dữ liệu

Mỗi lớp có thêm đúng 400 ảnh train:

- 100 ảnh nhiễu Gaussian.
- 100 ảnh mờ chuyển động.
- 100 ảnh giảm sáng.
- 100 ảnh ánh sáng không đều theo một hướng ngẫu nhiên có thể tái tạo.

Validation không được tăng cường. Mọi ảnh sinh thêm đều có tên bắt đầu bằng `aug_` và có thông tin ảnh cha trong `dataset_manifest.csv`.

## Chống rò rỉ dữ liệu

- FER-2013 và RAF-DB giữ split train/test gốc; phần test gốc được đưa vào Validation.
- ExpW được chia theo `source_file`, nên nhiều khuôn mặt trong cùng ảnh nguồn không thể nằm ở cả Train và Validation.
- Ảnh tăng cường luôn ở cùng Train với ảnh cha.
- Kết quả xác nhận không có giao nhau giữa ảnh nguồn Train và Validation.

## Dữ liệu CCTV

Năm mươi crop CCTV đạt chuẩn được đóng gói riêng trong `CCTV_Test_Unlabeled/`. Chúng không được trộn vào Train/Validation vì chưa có ground truth cảm xúc và cần giữ làm dữ liệu kiểm thử thực tế chưa từng dùng để train.

## Cách dùng

Team AI trỏ bộ nạp dữ liệu vào `nv_ngay6_7/Dataset`. Tên bốn thư mục con chính là tên lớp. Thứ tự lớp cố định nằm trong `class_mapping.json`.

