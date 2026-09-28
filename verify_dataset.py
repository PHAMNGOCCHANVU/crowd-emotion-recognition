import os
import sys
import torch
from PIL import Image

# Đảm bảo console Windows in utf-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

CLASSES = ['Happy', 'Normal', 'Sad', 'Surprised']


def find_dataset_dir():
    candidates = ['Data/Dataset', 'Dataset']
    for c in candidates:
        if os.path.exists(os.path.join(c, 'Train')) and os.path.exists(os.path.join(c, 'Validation')):
            return c
    return None


def verify_dataset(data_dir=None, sample_check_count=50):
    if data_dir is None:
        data_dir = find_dataset_dir()

    if data_dir is None:
        print("[ERROR] Không tìm thấy thư mục Dataset tại 'Data/Dataset' hoặc 'Dataset'!")
        return False, None

    print("=" * 65)
    print(f"🔍 BẮT ĐẦU XÁC THỰC DỮ LIỆU TẠI: {data_dir}")
    print("=" * 65)

    stats = {'Train': {}, 'Validation': {}}
    corrupt_files = []
    total_train = 0
    total_val = 0

    for split in ['Train', 'Validation']:
        split_dir = os.path.join(data_dir, split)
        for cls in CLASSES:
            cls_dir = os.path.join(split_dir, cls)
            if not os.path.exists(cls_dir):
                print(f"[CẢNH BÁO] Thiếu thư mục: {cls_dir}")
                stats[split][cls] = 0
                continue

            # Đếm nhanh số lượng file
            all_files = [f for f in os.listdir(cls_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            stats[split][cls] = len(all_files)

            if split == 'Train':
                total_train += len(all_files)
            else:
                total_val += len(all_files)

            # Lấy mẫu kiểm tra tính toàn vẹn (Sample verify)
            check_sample = all_files[:sample_check_count]
            for f in check_sample:
                file_path = os.path.join(cls_dir, f)
                try:
                    with Image.open(file_path) as img:
                        img.verify()
                except Exception as e:
                    corrupt_files.append((file_path, str(e)))

    print(f"\n📊 BẢNG PHÂN BỐ DỮ LIỆU THỰC TẾ:")
    print(f"{'Lớp (Class)':<15} | {'Train':<10} | {'Validation':<10} | {'Tổng cộng':<10}")
    print("-" * 55)
    for cls in CLASSES:
        tr = stats['Train'].get(cls, 0)
        va = stats['Validation'].get(cls, 0)
        print(f"{cls:<15} | {tr:<10} | {va:<10} | {tr + va:<10}")
    print("-" * 55)
    print(f"{'TỔNG CỘNG':<15} | {total_train:<10} | {total_val:<10} | {total_train + total_val:<10}")

    if corrupt_files:
        print(f"\n[CẢNH BÁO] Phát hiện {len(corrupt_files)} file ảnh bị lỗi:")
        for path, err in corrupt_files[:5]:
            print(f"  - {path}: {err}")
    else:
        print("\n✅ Mẫu kiểm tra tính toàn vẹn 100% hợp lệ, không có file hỏng.")

    # Tính toán Class Weights cho hàm Loss
    counts = [stats['Train'].get(cls, 1) for cls in CLASSES]
    num_classes = len(CLASSES)
    weights = [total_train / (num_classes * c) if c > 0 else 1.0 for c in counts]
    weights_tensor = torch.tensor(weights, dtype=torch.float32)

    print("\n⚖️  TRỌNG SỐ CÂN BẰNG LỚP (CLASS WEIGHTS):")
    for cls, w in zip(CLASSES, weights):
        print(f"  - {cls:<10}: {w:.4f}")

    print("=" * 65)
    return True, weights_tensor


if __name__ == '__main__':
    verify_dataset()
