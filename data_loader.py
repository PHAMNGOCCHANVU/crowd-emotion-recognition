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

# 4 nhãn cảm xúc chuẩn hóa của dự án
TARGET_CLASSES = ['Happy', 'Normal', 'Sad', 'Surprised']

# Chuẩn chuẩn hóa ImageNet tương thích ResNet-18
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def get_transforms(input_size=112, is_training=True):
    """
    Tạo pipeline tiền xử lý ảnh và Data Augmentation thích nghi với CCTV.
    - Ban ngày/ban đêm, ánh sáng đèn: ColorJitter (brightness, contrast).
    - Mờ do người di chuyển nhanh: GaussianBlur.
    - Góc nhìn đa dạng: RandomHorizontalFlip, RandomCrop.
    """
    if is_training:
        return transforms.Compose([
            transforms.Resize((int(input_size * 1.15), int(input_size * 1.15))),
            transforms.RandomCrop((input_size, input_size)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
            transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 1.0)),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
        ])
    else:
        return transforms.Compose([
            transforms.Resize((input_size, input_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
        ])


def create_dataloaders(data_dir='Dataset', batch_size=32, input_size=112, num_workers=0):
    """
    Nạp dữ liệu từ thư mục Dataset theo cấu trúc:
    Dataset/
    ├── Train/{Happy, Normal, Sad, Surprised}/
    └── Validation/{Happy, Normal, Sad, Surprised}/
    """
    train_path = os.path.join(data_dir, 'Train')
    val_path = os.path.join(data_dir, 'Validation')

    if not os.path.exists(train_path) or not os.path.exists(val_path):
        raise FileNotFoundError(
            f"Không tìm thấy thư mục Train/Validation tại '{data_dir}'. "
            "Hãy đảm bảo Team Data đã tạo đúng cấu trúc thư mục."
        )

    train_dataset = datasets.ImageFolder(train_path, transform=get_transforms(input_size, is_training=True))
    val_dataset = datasets.ImageFolder(val_path, transform=get_transforms(input_size, is_training=False))

    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True,
        num_workers=num_workers, pin_memory=torch.cuda.is_available()
    )
    val_loader = DataLoader(
        val_dataset, batch_size=batch_size * 2, shuffle=False,
        num_workers=num_workers, pin_memory=torch.cuda.is_available()
    )

    print(f"[INFO] Loaded Dataset: {train_dataset.classes}")
    print(f"[INFO] Train samples: {len(train_dataset)} | Val samples: {len(val_dataset)}")

    return train_loader, val_loader, train_dataset.classes


def create_dummy_dataset(base_dir='Dataset_Dummy', samples_per_class=5):
    """
    Tạo dữ liệu mẫu nhỏ (dummy images) để test pipeline training trước khi nhận dữ liệu thật.
    """
    for split in ['Train', 'Validation']:
        for cls_name in TARGET_CLASSES:
            cls_dir = os.path.join(base_dir, split, cls_name)
            os.makedirs(cls_dir, exist_ok=True)
            for i in range(samples_per_class):
                img_path = os.path.join(cls_dir, f"sample_{i}.jpg")
                if not os.path.exists(img_path):
                    # Tạo ảnh ngẫu nhiên RGB
                    dummy_img = Image.new('RGB', (112, 112), color=(i * 40 % 255, 100, 150))
                    dummy_img.save(img_path)
    print(f"[INFO] Đã tạo tập dummy dataset tại: {base_dir}")


if __name__ == '__main__':
    print("--- Test DataLoader ---")
    test_dir = 'Dataset_Dummy'
    create_dummy_dataset(test_dir, samples_per_class=4)

    train_loader, val_loader, classes = create_dataloaders(
        data_dir=test_dir, batch_size=4, input_size=112
    )

    # Lấy thử 1 batch
    images, labels = next(iter(train_loader))
    print(f"Batch images shape: {images.shape}")
    print(f"Batch labels shape: {labels.shape}")
    print(f"Batch labels:       {[classes[lbl.item()] for lbl in labels]}")

    assert images.shape == (4, 3, 112, 112), f"Unexpected shape {images.shape}"
    print("[OK] DataLoader test PASSED!")
