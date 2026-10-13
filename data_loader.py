import os
import sys
import torch
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from PIL import Image

# Đảm bảo console Windows in utf-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 6 nhãn cảm xúc chuẩn hóa của dự án
TARGET_CLASSES = ['Contempt', 'Fear', 'Happy', 'Normal', 'Sad', 'Surprised']


def get_transforms(input_size=48, is_training=True):
    """
    Tạo pipeline tiền xử lý ảnh Grayscale (1 kênh) và Data Augmentation mạnh
    nhằm đạt độ chính xác cao (>= 70%) khi huấn luyện CustomResNet18 from scratch.
    """
    if is_training:
        scale_size = int(input_size * 1.15)
        return transforms.Compose([
            transforms.Grayscale(num_output_channels=1),
            transforms.Resize((scale_size, scale_size)),
            transforms.RandomCrop((input_size, input_size)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=10),
            transforms.RandomAffine(degrees=0, translate=(0.08, 0.08), scale=(0.92, 1.08)),
            transforms.ColorJitter(brightness=0.25, contrast=0.25),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5], std=[0.5]),
            transforms.RandomErasing(p=0.2, scale=(0.02, 0.15), value=0.0)
        ])
    else:
        return transforms.Compose([
            transforms.Grayscale(num_output_channels=1),
            transforms.Resize((input_size, input_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5], std=[0.5])
        ])


def find_dataset_path(candidate_dir='Data/Dataset'):
    if os.path.exists(os.path.join(candidate_dir, 'Train')) and os.path.exists(os.path.join(candidate_dir, 'Validation')):
        return candidate_dir
    alt_candidates = ['Data/Dataset', 'Dataset', '../Data/Dataset']
    for c in alt_candidates:
        if os.path.exists(os.path.join(c, 'Train')) and os.path.exists(os.path.join(c, 'Validation')):
            return c
    return candidate_dir


def create_dataloaders(data_dir='Data/Dataset', batch_size=64, input_size=48, num_workers=0):
    """
    Nạp dữ liệu từ thư mục Dataset theo cấu trúc:
    Data/Dataset/
    ├── Train/{Contempt, Fear, Happy, Normal, Sad, Surprised}/
    └── Validation/{Contempt, Fear, Happy, Normal, Sad, Surprised}/
    """
    data_dir = find_dataset_path(data_dir)
    train_path = os.path.join(data_dir, 'Train')
    val_path = os.path.join(data_dir, 'Validation')

    if not os.path.exists(train_path) or not os.path.exists(val_path):
        raise FileNotFoundError(
            f"Không tìm thấy thư mục Train/Validation tại '{data_dir}'. "
            "Hãy đảm bảo thư mục dữ liệu đã sẵn sàng."
        )

    train_dataset = datasets.ImageFolder(train_path, transform=get_transforms(input_size, is_training=True))
    val_dataset = datasets.ImageFolder(val_path, transform=get_transforms(input_size, is_training=False))

    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True,
        num_workers=num_workers, pin_memory=torch.cuda.is_available()
    )
    val_loader = DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False,
        num_workers=num_workers, pin_memory=torch.cuda.is_available()
    )

    print(f"[INFO] Loaded Dataset Classes: {train_dataset.classes}")
    print(f"[INFO] Train samples: {len(train_dataset)} | Val samples: {len(val_dataset)}")

    return train_loader, val_loader, train_dataset.classes


def create_dummy_dataset(base_dir='Dataset_Dummy', samples_per_class=4, img_size=48):
    """
    Tạo dữ liệu mẫu nhỏ (dummy grayscale images) để kiểm tra pipeline.
    """
    for split in ['Train', 'Validation']:
        for cls_name in TARGET_CLASSES:
            cls_dir = os.path.join(base_dir, split, cls_name)
            os.makedirs(cls_dir, exist_ok=True)
            for i in range(samples_per_class):
                img_path = os.path.join(cls_dir, f"sample_{i}.jpg")
                if not os.path.exists(img_path):
                    dummy_img = Image.new('L', (img_size, img_size), color=(i * 40 % 255))
                    dummy_img.save(img_path)
    print(f"[INFO] Đã tạo tập dummy dataset tại: {base_dir}")


if __name__ == '__main__':
    print("--- Test DataLoader ---")
    # Kiểm tra trực tiếp trên Data/Dataset thật
    train_loader, val_loader, classes = create_dataloaders(
        data_dir='Data/Dataset', batch_size=8, input_size=48
    )

    images, labels = next(iter(train_loader))
    print(f"Batch images shape: {images.shape}")
    print(f"Batch labels shape: {labels.shape}")
    print(f"Batch labels:       {[classes[lbl.item()] for lbl in labels]}")

    assert images.shape == (8, 1, 48, 48), f"Unexpected shape {images.shape}"
    print("[OK] DataLoader test PASSED!")
