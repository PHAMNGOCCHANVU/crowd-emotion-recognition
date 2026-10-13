"""
evaluate.py — Đánh giá toàn diện mô hình CustomResNet18 6 nhãn cảm xúc
======================================================================
1. Đánh giá độ chính xác tổng thể (Overall Accuracy).
2. Tính toán Ma trận nhầm lẫn (Confusion Matrix 6x6).
3. Đo lường chi tiết Precision, Recall, F1-Score cho từng nhãn cảm xúc:
   (Contempt, Fear, Happy, Normal, Sad, Surprised).
4. Xuất biểu đồ Confusion Matrix và Đường cong huấn luyện (training_curves.png).
5. Trích xuất file metrics JSON phục vụ báo cáo khoa học.
"""

import os
import sys
import json
import torch
import numpy as np
import matplotlib.pyplot as plt
from torchvision import datasets
from torch.utils.data import DataLoader

from model import CustomResNet18, EMOTION_CLASSES
from data_loader import get_transforms, find_dataset_path

# Đảm bảo console Windows in utf-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def evaluate_model(
    model_path='weights/custom_resnet18_6emo.pt',
    data_dir='Data/Dataset/Validation',
    output_dir='docs',
    history_path='train_history.json',
    input_size=48
):
    os.makedirs(output_dir, exist_ok=True)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    print("=" * 70)
    print("📊 BẮT ĐẦU ĐÁNH GIÁ MÔ HÌNH CUSTOMRESNET18 — 6 NHÃN CẢM XÚC")
    print(f"   Trọng số mô hình: {model_path}")
    print(f"   Thư mục dữ liệu: {data_dir}")
    print(f"   Kích thước ảnh:  {input_size}x{input_size} (Grayscale)")
    print(f"   Thiết bị:        {device}")
    print("=" * 70)

    # Fallback tìm kiếm model nếu đường dẫn mặc định chưa có
    if not os.path.exists(model_path):
        alt_paths = ['weights/crowd_emotion_resnet18.pt', '../weights/custom_resnet18_6emo.pt']
        found = False
        for alt in alt_paths:
            if os.path.exists(alt):
                model_path = alt
                found = True
                break
        if not found:
            print(f"[ERROR] Không tìm thấy file trọng số '{model_path}'! Hãy chạy train.py trước.")
            return False

    # Tìm đường dẫn tập validation nếu cần
    if not os.path.exists(data_dir):
        base_dir = find_dataset_path('Data/Dataset')
        candidate_val = os.path.join(base_dir, 'Validation')
        if os.path.exists(candidate_val):
            data_dir = candidate_val

    # 1. Khởi tạo mô hình và tải trọng số
    model = CustomResNet18(num_classes=len(EMOTION_CLASSES), in_channels=1).to(device)
    checkpoint = torch.load(model_path, map_location=device, weights_only=True)
    model.load_state_dict(checkpoint)
    model.eval()

    # 2. Nạp dữ liệu Validation (Grayscale 48x48)
    val_dataset = datasets.ImageFolder(
        data_dir,
        transform=get_transforms(input_size=input_size, is_training=False)
    )
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

    # Tính Precision, Recall, F1-Score
    metrics = {}
    total_samples = len(all_targets)
    correct_samples = np.trace(cm)
    overall_accuracy = correct_samples / total_samples

    print("\n📈 BẢNG ĐÁNH GIÁ ĐỘ CHÍNH XÁC CHI TIẾT THEO TỪNG NHÃN (6 NHÃN):")
    print(f"{'Lớp (Emotion)':<15} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'Mẫu (Support)':<10}")
    print("-" * 70)

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

    print("-" * 70)
    print(f"{'ĐỘ CHÍNH XÁC CHUNG (ACCURACY)':<35} : {overall_accuracy * 100:.2f}%\n")

    metrics["overall_accuracy"] = round(float(overall_accuracy), 4)
    metrics["total_samples"] = int(total_samples)

    # Lưu metrics ra file JSON
    metrics_file = os.path.join(output_dir, 'evaluation_metrics.json')
    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"[XUẤT FILE] Bảng chỉ số đã lưu tại: {metrics_file}")

    # 4. Vẽ Confusion Matrix 6x6
    row_sums = cm.sum(axis=1)[:, np.newaxis]
    cm_norm = np.divide(cm.astype('float'), row_sums, out=np.zeros_like(cm, dtype=float), where=row_sums != 0)

    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(cm_norm, interpolation='nearest', cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    ax.set(
        xticks=np.arange(num_classes),
        yticks=np.arange(num_classes),
        xticklabels=EMOTION_CLASSES,
        yticklabels=EMOTION_CLASSES,
        title=f'Confusion Matrix 6-Classes (Acc: {overall_accuracy * 100:.1f}%)',
        ylabel='Thực tế (True Label)',
        xlabel='Dự đoán (Predicted Label)'
    )
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", rotation_mode="anchor")

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

    # 5. Vẽ biểu đồ Training History nếu có
    if os.path.exists(history_path):
        with open(history_path, 'r', encoding='utf-8') as f:
            hist = json.load(f)

        if 'train_loss' in hist and len(hist['train_loss']) > 0:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.5))

            epochs = range(1, len(hist['train_loss']) + 1)
            ax1.plot(epochs, hist['train_loss'], 'b-', label='Train Loss', linewidth=2)
            ax1.plot(epochs, hist['val_loss'], 'r--', label='Val Loss', linewidth=2)
            ax1.set_title('Loss theo từng Epoch')
            ax1.set_xlabel('Epoch')
            ax1.set_ylabel('Cross-Entropy Loss')
            ax1.legend()
            ax1.grid(True)

            ax2.plot(epochs, [x * 100 for x in hist['train_acc']], 'b-', label='Train Acc', linewidth=2)
            ax2.plot(epochs, [x * 100 for x in hist['val_acc']], 'r--', label='Val Acc', linewidth=2)
            ax2.set_title('Độ chính xác theo từng Epoch (%)')
            ax2.set_xlabel('Epoch')
            ax2.set_ylabel('Accuracy (%)')
            ax2.legend()
            ax2.grid(True)

            fig.tight_layout()
            curves_path = os.path.join(output_dir, 'training_curves.png')
            plt.savefig(curves_path, dpi=200)
            plt.close()
            print(f"[XUẤT ẢNH] Biểu đồ đường huấn luyện đã lưu tại: {curves_path}")

    print("=" * 70)
    print("✅ ĐÁNH GIÁ MÔ HÌNH VÀ XUẤT TÀI LIỆU HOÀN TẤT THÀNH CÔNG!")
    return True


if __name__ == '__main__':
    evaluate_model()
