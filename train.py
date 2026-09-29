"""
train.py — Huấn luyện 2 giai đoạn (Freeze Head -> Fine-tune Backbone)
======================================================================
Mô hình: ResNet-18 ImageNet pre-trained
4 nhãn: Happy, Normal, Sad, Surprised
Cơ chế chống Overfitting & Đạt Flat Minimum:
- Label Smoothing (0.1): Làm phẳng mục tiêu, giảm độ tự tin thái quá.
- CosineAnnealingLR: Giảm dần learning rate về 0, hạ cánh êm ái vào đáy hàm loss.
- Weight Decay (AdamW): Phạt độ dốc lớn, tìm cực tiểu phẳng (Flat Minimum).
- Early Stopping (patience=6): Chống overfit khi validation loss ngừng giảm.
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

from data_loader import create_dataloaders
from crowd_emotion_model import CrowdEmotionModel, EMOTION_CLASSES
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

        # Gradient clipping nhẹ để ổn định hướng hội tụ
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
    epochs_head=6,
    epochs_finetune=14,
    batch_size=32,
    input_size=224,
    dropout_rate=0.5,
    unfreeze_all=True,
    lr_head=1e-3,
    lr_backbone=1e-5,
    lr_classifier=3e-4,
    label_smoothing=0.1,
    weight_decay=1e-4,
    save_path='weights/crowd_emotion_resnet18.pt',
    history_path='train_history.json'
):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print("=" * 70)
    print("🚀 BẮT ĐẦU HUẤN LUYỆN CORE AI MODEL — CẤU HÌNH NÂNG CẤP FLAT MINIMUM")
    print(f"   Thiết bị tính toán:   {device}")
    print(f"   Thư mục dữ liệu:     {data_dir}")
    print(f"   Kích thước đầu vào:  {input_size}x{input_size}")
    print(f"   Batch size:          {batch_size}")
    print(f"   Dropout:             {dropout_rate} (Thu hẹp Generalization Gap)")
    print(f"   Unfreeze Backbone:   {'TOÀN BỘ (All layers)' if unfreeze_all else '2 tầng cuối'}")
    print(f"   LR Backbone:         {lr_backbone} (Bảo toàn trọng số ImageNet)")
    print(f"   LR Classifier:       {lr_classifier}")
    print(f"   Label Smoothing:     {label_smoothing} (Chống Overfitting)")
    print(f"   Weight Decay (AdamW):{weight_decay} (Phạt độ dốc lớn)")
    print(f"   File lưu model:      {save_path}")
    print("=" * 70)

    # 1. Xác thực dữ liệu và lấy trọng số cân bằng lớp
    _, class_weights = verify_dataset(data_dir)
    if class_weights is not None:
        class_weights = class_weights.to(device)
        criterion = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=label_smoothing)
        print(f"[INFO] Đã áp dụng Class Weights và Label Smoothing ({label_smoothing}) vào hàm Loss.")
    else:
        criterion = nn.CrossEntropyLoss(label_smoothing=label_smoothing)

    # 2. Tạo DataLoaders (kèm Data Augmentation cho CCTV)
    train_loader, val_loader, classes = create_dataloaders(
        data_dir=data_dir, batch_size=batch_size, input_size=input_size
    )

    # 3. Khởi tạo mô hình ResNet-18 (Head mới, freeze backbone, Dropout 0.5)
    model = CrowdEmotionModel(
        num_classes=4, freeze_backbone=True, dropout_rate=dropout_rate
    ).to(device)

    best_val_acc = 0.0
    best_val_loss = float('inf')
    history = {
        'train_loss': [], 'train_acc': [],
        'val_loss': [], 'val_acc': []
    }

    # =========================================================================
    # GIAI ĐOẠN 2A: HUẤN LUYỆN TẦNG HEAD (FREEZE BACKBONE)
    # =========================================================================
    print("\n" + "=" * 70)
    print(f"🔹 GIAI ĐOẠN 2A: ĐỊNH HÌNH TẦNG PHÂN LOẠI CLASSIFIER ({epochs_head} EPOCHS)")
    print("=" * 70)

    optimizer_head = AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=lr_head,
        weight_decay=weight_decay
    )
    scheduler_head = CosineAnnealingLR(optimizer_head, T_max=epochs_head, eta_min=1e-4)

    for epoch in range(1, epochs_head + 1):
        t0 = time.time()
        tr_loss, tr_acc = train_one_epoch(model, train_loader, criterion, optimizer_head, device)
        val_loss, val_acc = validate(model, val_loader, criterion, device)
        current_lr = optimizer_head.param_groups[0]['lr']
        scheduler_head.step()
        elapsed = time.time() - t0

        history['train_loss'].append(round(tr_loss, 4))
        history['train_acc'].append(round(tr_acc, 4))
        history['val_loss'].append(round(val_loss, 4))
        history['val_acc'].append(round(val_acc, 4))

        print(
            f"Epoch [{epoch:02d}/{epochs_head:02d}] ({elapsed:.1f}s, lr={current_lr:.1e}) | "
            f"Train Loss: {tr_loss:.4f} - Acc: {tr_acc * 100:.2f}% | "
            f"Val Loss: {val_loss:.4f} - Acc: {val_acc * 100:.2f}%"
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_val_loss = val_loss
            torch.save(model.state_dict(), save_path)
            print(f"  --> [LƯU MODEL] Đạt kỷ lục Val Acc: {val_acc * 100:.2f}%")

    # =========================================================================
    # GIAI ĐOẠN 2B: FINE-TUNE SÂU BACKBONE (HẠ CÁNH VÀO FLAT MINIMUM)
    # =========================================================================
    print("\n" + "=" * 70)
    print(f"🔹 GIAI ĐOẠN 2B: FINE-TUNING SÂU TOÀN BỘ BACKBONE & HẠ CÁNH ÊM ÁI ({epochs_finetune} EPOCHS)")
    print("=" * 70)

    # Nạp lại checkpoint tốt nhất của Giai đoạn 2A
    if os.path.exists(save_path):
        model.load_state_dict(torch.load(save_path, map_location=device, weights_only=True))

    if unfreeze_all:
        model.unfreeze_backbone(num_layers_to_unfreeze=None)
    else:
        model.unfreeze_backbone(num_layers_to_unfreeze=2)

    optimizer_ft = AdamW([
        {'params': model.backbone.parameters(), 'lr': lr_backbone},
        {'params': model.classifier.parameters(), 'lr': lr_classifier}
    ], weight_decay=weight_decay)

    # Cosine Annealing giảm dần learning rate xuống 1e-6 để hạ cánh cực êm vào đáy phẳng
    scheduler_ft = CosineAnnealingLR(optimizer_ft, T_max=epochs_finetune, eta_min=1e-6)

    patience = 6
    patience_counter = 0

    for epoch in range(1, epochs_finetune + 1):
        t0 = time.time()
        tr_loss, tr_acc = train_one_epoch(model, train_loader, criterion, optimizer_ft, device)
        val_loss, val_acc = validate(model, val_loader, criterion, device)
        bb_lr = optimizer_ft.param_groups[0]['lr']
        cls_lr = optimizer_ft.param_groups[1]['lr']
        scheduler_ft.step()
        elapsed = time.time() - t0

        history['train_loss'].append(round(tr_loss, 4))
        history['train_acc'].append(round(tr_acc, 4))
        history['val_loss'].append(round(val_loss, 4))
        history['val_acc'].append(round(val_acc, 4))

        print(
            f"Epoch [{epoch:02d}/{epochs_finetune:02d}] ({elapsed:.1f}s, lr_bb={bb_lr:.1e}, lr_cls={cls_lr:.1e}) | "
            f"Train Loss: {tr_loss:.4f} - Acc: {tr_acc * 100:.2f}% | "
            f"Val Loss: {val_loss:.4f} - Acc: {val_acc * 100:.2f}%"
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_val_loss = val_loss
            patience_counter = 0
            torch.save(model.state_dict(), save_path)
            print(f"  --> [LƯU MODEL] Đạt kỷ lục Val Acc: {val_acc * 100:.2f}% (Loss: {val_loss:.4f})")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"[EARLY STOPPING] Đã hội tụ vào điểm cực tiểu phẳng sau {patience} epochs ổn định.")
                break

    # Lưu lịch sử huấn luyện
    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2)

    print("\n" + "=" * 70)
    print("🎉 HOÀN TẤT HUẤN LUYỆN CORE AI MODEL VÀ HẠ CÁNH VÀO ĐÁY HÀM LOSS!")
    print(f"   Trọng số tối ưu đã lưu tại:      {save_path}")
    print(f"   Độ chính xác Validation tốt nhất: {best_val_acc * 100:.2f}%")
    print(f"   Lịch sử huấn luyện đã lưu tại:   {history_path}")
    print("=" * 70)
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Huấn luyện mô hình nhận diện biểu cảm đám đông ResNet-18")
    parser.add_argument('--data-dir', type=str, default='Data/Dataset', help='Thư mục dữ liệu')
    parser.add_argument('--epochs-head', type=int, default=6, help='Số epoch train Head')
    parser.add_argument('--epochs-ft', type=int, default=14, help='Số epoch fine-tuning')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size (mặc định 32)')
    parser.add_argument('--input-size', type=int, default=224, help='Kích thước ảnh đầu vào (mặc định 224)')
    parser.add_argument('--dropout', type=float, default=0.5, help='Hệ số Dropout cho Classifier (mặc định 0.5)')
    parser.add_argument('--lr-backbone', type=float, default=1e-5, help='Learning rate Backbone (mặc định 1e-5)')
    parser.add_argument('--lr-classifier', type=float, default=3e-4, help='Learning rate Classifier (mặc định 3e-4)')
    parser.add_argument('--label-smoothing', type=float, default=0.1, help='Hệ số Label Smoothing')
    parser.add_argument('--unfreeze-all', action='store_true', default=True, help='Mở khóa toàn bộ Backbone')
    args = parser.parse_args()

    run_training(
        data_dir=args.data_dir,
        epochs_head=args.epochs_head,
        epochs_finetune=args.epochs_ft,
        batch_size=args.batch_size,
        input_size=args.input_size,
        dropout_rate=args.dropout,
        unfreeze_all=args.unfreeze_all,
        lr_backbone=args.lr_backbone,
        lr_classifier=args.lr_classifier,
        label_smoothing=args.label_smoothing
    )
