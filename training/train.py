"""
train.py — Huấn luyện CustomResNet18 from scratch nhận diện 6 loại cảm xúc
========================================================================
Mô hình: CustomResNet18 (6 nhãn, Grayscale 48x48)
6 nhãn: Contempt, Fear, Happy, Normal, Sad, Surprised
Cơ chế huấn luyện tối ưu:
- 1 Giai đoạn huấn luyện end-to-end từ đầu với khởi tạo Kaiming He.
- Label Smoothing (0.1): Giảm overconfidence và regularization cho nhãn cảm xúc phức tạp.
- CosineAnnealingLR: Giảm mượt mà learning rate về eta_min=1e-6.
- Weight Decay (AdamW): Phạt cực đại độ dốc gradient, hỗ trợ tìm cực tiểu phẳng (Flat Minimum).
- Early Stopping (patience=8): Tự động dừng khi validation loss không còn cải thiện.
- Gradient Clipping (5.0): Giữ ổn định gradient flow trong các tầng Residual.
"""

import os
import sys
import time
import json
import argparse
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR

from model import CustomResNet18, EMOTION_CLASSES
from data_loader import create_dataloaders
from verify_dataset import verify_dataset

# Đảm bảo console Windows in utf-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def train_one_epoch(model, dataloader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in dataloader:
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()

        # Gradient clipping ổn định đạo hàm
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)

        optimizer.step()

        running_loss += loss.item() * images.size(0)
        _, preds = outputs.max(1)
        correct += preds.eq(labels).sum().item()
        total += labels.size(0)

    epoch_loss = running_loss / total
    epoch_acc = correct / total
    return epoch_loss, epoch_acc


def validate(model, dataloader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in dataloader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * images.size(0)
            _, preds = outputs.max(1)
            correct += preds.eq(labels).sum().item()
            total += labels.size(0)

    val_loss = running_loss / total
    val_acc = correct / total
    return val_loss, val_acc


def run_training(
    data_dir='Data/Dataset',
    epochs=50,
    batch_size=64,
    input_size=48,
    lr=1e-3,
    dropout_rate=0.5,
    label_smoothing=0.1,
    weight_decay=1e-4,
    patience=8,
    save_path='weights/custom_resnet18_6emo.pt',
    history_path='train_history.json'
):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    print("=" * 72)
    print("🚀 BẮT ĐẦU HUẤN LUYỆN CUSTOMRESNET18 (FROM SCRATCH) — 6 NHÃN CẢM XÚC")
    print(f"   Thiết bị tính toán:   {device}")
    print(f"   Thư mục dữ liệu:     {data_dir}")
    print(f"   Số nhãn phân loại:   {len(EMOTION_CLASSES)} ({', '.join(EMOTION_CLASSES)})")
    print(f"   Kích thước đầu vào:  {input_size}x{input_size} (Grayscale 1 channel)")
    print(f"   Batch size:          {batch_size}")
    print(f"   Epochs tối đa:       {epochs}")
    print(f"   Learning Rate khởi điểm: {lr}")
    print(f"   Dropout Rate:        {dropout_rate}")
    print(f"   Label Smoothing:     {label_smoothing}")
    print(f"   Weight Decay (AdamW):{weight_decay}")
    print(f"   Patience:            {patience} epochs")
    print(f"   File lưu model:      {save_path}")
    print("=" * 72)

    # 1. Xác thực dữ liệu và lấy trọng số cân bằng lớp
    _, class_weights = verify_dataset(data_dir)
    if class_weights is not None:
        class_weights = class_weights.to(device)
        criterion = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=label_smoothing)
        print(f"[INFO] Đã cấu hình CrossEntropyLoss với Class Weights và Label Smoothing ({label_smoothing}).")
    else:
        criterion = nn.CrossEntropyLoss(label_smoothing=label_smoothing)

    # 2. Tạo DataLoaders (Grayscale 48x48 + Data Augmentation)
    train_loader, val_loader, classes = create_dataloaders(
        data_dir=data_dir, batch_size=batch_size, input_size=input_size
    )

    # 3. Khởi tạo CustomResNet18 from scratch
    model = CustomResNet18(
        num_classes=len(classes),
        in_channels=1,
        dropout_rate=dropout_rate
    ).to(device)

    total_params = sum(p.numel() for p in model.parameters())
    print(f"[INFO] Tổng số tham số của CustomResNet18: {total_params:,}")

    # 4. Thiết lập Optimizer và LR Scheduler
    optimizer = AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)

    best_val_acc = 0.0
    best_val_loss = float('inf')
    best_epoch = 0
    patience_counter = 0

    history = {
        'train_loss': [], 'train_acc': [],
        'val_loss': [], 'val_acc': [],
        'learning_rates': []
    }

    print("\n" + "=" * 72)
    print("🔹 BẮT ĐẦU CHU KỲ HUẤN LUYỆN")
    print("=" * 72)

    for epoch in range(1, epochs + 1):
        t0 = time.time()
        current_lr = optimizer.param_groups[0]['lr']

        tr_loss, tr_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = validate(model, val_loader, criterion, device)
        scheduler.step()
        elapsed = time.time() - t0

        history['train_loss'].append(round(tr_loss, 4))
        history['train_acc'].append(round(tr_acc, 4))
        history['val_loss'].append(round(val_loss, 4))
        history['val_acc'].append(round(val_acc, 4))
        history['learning_rates'].append(current_lr)

        print(
            f"Epoch [{epoch:02d}/{epochs:02d}] ({elapsed:.1f}s, lr={current_lr:.1e}) | "
            f"Train Loss: {tr_loss:.4f} - Acc: {tr_acc * 100:.2f}% | "
            f"Val Loss: {val_loss:.4f} - Acc: {val_acc * 100:.2f}%"
        )

        # Lưu checkpoint khi đạt Best Validation Accuracy
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_val_loss = val_loss
            best_epoch = epoch
            patience_counter = 0
            torch.save(model.state_dict(), save_path)
            print(f"  --> [LƯU MODEL] Đạt kỷ lục Val Acc: {val_acc * 100:.2f}% (Loss: {val_loss:.4f})")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"\n[EARLY STOPPING] Dừng sớm tại Epoch {epoch} vì Val Loss không cải thiện sau {patience} epochs liên tiếp.")
                break

    # Lưu lịch sử huấn luyện
    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2)

    print("\n" + "=" * 72)
    print("🎉 HOÀN TẤT QUÁ TRÌNH HUẤN LUYỆN!")
    print(f"   Trọng số tối ưu đã lưu tại:        {save_path}")
    print(f"   Độ chính xác Validation tốt nhất:   {best_val_acc * 100:.2f}% (Epoch {best_epoch})")
    print(f"   File lịch sử huấn luyện:          {history_path}")
    print("=" * 72)
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Huấn luyện CustomResNet18 6 nhãn cảm xúc from scratch")
    parser.add_argument('--data-dir', type=str, default='Data/Dataset', help='Thư mục dữ liệu')
    parser.add_argument('--epochs', type=int, default=50, help='Số epoch tối đa (mặc định 50)')
    parser.add_argument('--batch-size', type=int, default=64, help='Batch size (mặc định 64)')
    parser.add_argument('--input-size', type=int, default=48, help='Kích thước ảnh đầu vào (mặc định 48)')
    parser.add_argument('--lr', type=float, default=1e-3, help='Learning rate khởi điểm (mặc định 1e-3)')
    parser.add_argument('--dropout', type=float, default=0.5, help='Hệ số Dropout (mặc định 0.5)')
    parser.add_argument('--label-smoothing', type=float, default=0.1, help='Hệ số Label Smoothing')
    parser.add_argument('--weight-decay', type=float, default=1e-4, help='Hệ số Weight Decay')
    parser.add_argument('--patience', type=int, default=8, help='Số epoch chờ Early Stopping (mặc định 8)')
    parser.add_argument('--save-path', type=str, default='weights/custom_resnet18_6emo.pt', help='Đường dẫn lưu model')
    parser.add_argument('--history-path', type=str, default='train_history.json', help='Đường dẫn lưu history')
    args = parser.parse_args()

    run_training(
        data_dir=args.data_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        input_size=args.input_size,
        lr=args.lr,
        dropout_rate=args.dropout,
        label_smoothing=args.label_smoothing,
        weight_decay=args.weight_decay,
        patience=args.patience,
        save_path=args.save_path,
        history_path=args.history_path
    )
