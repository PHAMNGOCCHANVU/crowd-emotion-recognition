"""
evaluate.py — Đánh giá toàn diện mô hình Core AI Model & Trích xuất số liệu Báo cáo
==================================================================================
1. Tính toán Ma trận nhầm lẫn (Confusion Matrix).
2. Tính toán Precision, Recall, F1-Score cho từng nhãn.
3. Xuất biểu đồ Training/Validation Loss & Accuracy (train_curves.png).
"""

import os
import sys
import json
import torch
import numpy as np
import matplotlib.pyplot as plt
from torchvision import datasets, transforms
from torch.utils.data import DataLoader

from crowd_emotion_model import CrowdEmotionModel, EMOTION_CLASSES
from data_loader import get_transforms

# Đảm bảo console Windows in utf-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def evaluate_model(
    model_path='weights/crowd_emotion_resnet18.pt',
    data_dir='Data/Dataset/Validation',
    output_dir='docs',
    history_path='train_history.json'
):
    os.makedirs(output_dir, exist_ok=True)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print("=" * 65)
    print("📊 BẮT ĐẦU ĐÁNH GIÁ MÔ HÌNH VÀ TRÍCH XUẤT KẾT QUẢ")
    print(f"   Model:      {model_path}")
    print(f"   Tập dữ liệu:{data_dir}")
    print(f"   Thiết bị:   {device}")
    print("=" * 65)

    if not os.path.exists(model_path):
        print(f"[ERROR] Không tìm thấy file trọng số '{model_path}'! Hãy chạy train.py trước.")
        return False

    # 1. Nạp mô hình
    model = CrowdEmotionModel(num_classes=4, freeze_backbone=False).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
    model.eval()

    # 2. Nạp dữ liệu Validation
    val_dataset = datasets.ImageFolder(data_dir, transform=get_transforms(input_size=112, is_training=False))
    val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)

    all_preds = []
    all_targets = []

    with torch.no_grad():
        for images, labels in val_loader:
            images = images.to(device)
            outputs = model(images)
            _, preds = outputs.max(1)
            all_preds.extend(preds.cpu().numpy())
            all_targets.extend(labels.numpy())

    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)

    # 3. Tính toán Ma trận nhầm lẫn
    num_classes = len(EMOTION_CLASSES)
    cm = np.zeros((num_classes, num_classes), dtype=int)
    for t, p in zip(all_targets, all_preds):
        cm[t, p] += 1

    # Tính Precision, Recall, F1
    metrics = {}
    total_samples = len(all_targets)
    correct_samples = np.trace(cm)
    overall_accuracy = correct_samples / total_samples

    print("\n📈 BẢNG ĐÁNH GIÁ ĐỘ CHÍNH XÁC CHI TIẾT:")
    print(f"{'Lớp (Emotion)':<15} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'Mẫu (Support)':<10}")
    print("-" * 65)

    for i, cls in enumerate(EMOTION_CLASSES):
        tp = cm[i, i]
        fp = cm[:, i].sum() - tp
        fn = cm[i, :].sum() - tp
        support = cm[i, :].sum()

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        metrics[cls] = {
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "support": int(support)
        }
        print(f"{cls:<15} | {prec * 100:>8.2f}% | {rec * 100:>8.2f}% | {f1:>8.4f}  | {support:>10}")

    print("-" * 65)
    print(f"{'ĐỘ CHÍNH XÁC CHUNG (ACCURACY)':<35} : {overall_accuracy * 100:.2f}%\n")

    metrics["overall_accuracy"] = round(float(overall_accuracy), 4)
    metrics["total_samples"] = int(total_samples)

    # Lưu metrics ra file JSON
    metrics_file = os.path.join(output_dir, 'evaluation_metrics.json')
    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"[XUẤT FILE] Bảng chỉ số đã lưu tại: {metrics_file}")

    # 4. Vẽ Confusion Matrix
    cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm_norm, interpolation='nearest', cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    ax.set(
        xticks=np.arange(num_classes),
        yticks=np.arange(num_classes),
        xticklabels=EMOTION_CLASSES,
        yticklabels=EMOTION_CLASSES,
        title=f'Confusion Matrix (Acc: {overall_accuracy * 100:.1f}%)',
        ylabel='Thực tế (True Label)',
        xlabel='Dự đoán (Predicted Label)'
    )

    fmt = '.2f'
    thresh = cm_norm.max() / 2.
    for i in range(num_classes):
        for j in range(num_classes):
            ax.text(
                j, i, format(cm_norm[i, j], fmt),
                ha="center", va="center",
                color="white" if cm_norm[i, j] > thresh else "black"
            )

    fig.tight_layout()
    cm_path = os.path.join(output_dir, 'confusion_matrix.png')
    plt.savefig(cm_path, dpi=200)
    plt.close()
    print(f"[XUẤT ẢNH] Ma trận nhầm lẫn đã lưu tại: {cm_path}")

    # 5. Vẽ biểu đồ Training History nếu có file
    if os.path.exists(history_path):
        with open(history_path, 'r', encoding='utf-8') as f:
            hist = json.load(f)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

        # Loss
        epochs = range(1, len(hist['train_loss']) + 1)
        ax1.plot(epochs, hist['train_loss'], 'b-', label='Train Loss')
        ax1.plot(epochs, hist['val_loss'], 'r--', label='Val Loss')
        ax1.set_title('Loss theo từng Epoch')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.legend()
        ax1.grid(True)

        # Accuracy
        ax2.plot(epochs, [x * 100 for x in hist['train_acc']], 'b-', label='Train Acc')
        ax2.plot(epochs, [x * 100 for x in hist['val_acc']], 'r--', label='Val Acc')
        ax2.set_title('Accuracy theo từng Epoch (%)')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('Accuracy (%)')
        ax2.legend()
        ax2.grid(True)

        fig.tight_layout()
        curves_path = os.path.join(output_dir, 'training_curves.png')
        plt.savefig(curves_path, dpi=200)
        plt.close()
        print(f"[XUẤT ẢNH] Biểu đồ đường huấn luyện đã lưu tại: {curves_path}")

    print("=" * 65)
    print("✅ ĐÁNH GIÁ VÀ XUẤT TÀI LIỆU BÁO CÁO THÀNH CÔNG!")
    return True


if __name__ == '__main__':
    evaluate_model()
