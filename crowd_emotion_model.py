import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models

# 4 nhãn cảm xúc chuẩn hóa quốc tế (tương thích FER-2013, RAF-DB, AffectNet)
EMOTION_CLASSES = ['Happy', 'Normal', 'Sad', 'Surprised']


class CrowdEmotionModel(nn.Module):
    """
    Tier 1: Mô hình nhận diện biểu cảm cá nhân từ khuôn mặt.
    - Backbone: ResNet-18 pre-trained trên ImageNet (năng lực trích xuất vượt trội mạng CNN nhỏ).
    - Head: Classification layer cho 4 nhãn chuẩn (Happy, Normal, Sad, Surprised).
    """
    def __init__(self, num_classes=4, freeze_backbone=True):
        super(CrowdEmotionModel, self).__init__()
        self.num_classes = num_classes

        # Load ResNet-18 với trọng số pre-trained ImageNet mặc định
        resnet = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)

        # Lấy toàn bộ các tầng ngoại trừ FC layer cuối (1000 classes của ImageNet)
        self.backbone = nn.Sequential(*list(resnet.children())[:-1])
        self.feature_dim = 512  # ResNet-18 xuất ra 512 features

        # Khóa tầng Backbone nếu freeze_backbone=True (chỉ train FC)
        if freeze_backbone:
            for param in self.backbone.parameters():
                param.requires_grad = False

        # Tầng phân loại mới cho 4 nhãn
        self.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(self.feature_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, num_classes)
        )

    def forward(self, x):
        """
        Input: Tensor ảnh [batch_size, 3, H, W] (khuyến nghị H=W=112 hoặc 224)
        Output: Raw logits [batch_size, num_classes]
        """
        x = self.backbone(x)
        x = x.view(x.size(0), -1)  # Flatten -> [batch, 512]
        x = self.classifier(x)     # Logits -> [batch, num_classes]
        return x

    def predict(self, x):
        """Trả về index của nhãn dự đoán có điểm số cao nhất."""
        scores = self.forward(x)
        _, predictions = scores.max(1)
        return predictions

    def predict_proba(self, x):
        """
        Trả về (max_probability, predicted_label_idx)
        áp dụng Softmax để lấy xác suất tin cậy.
        """
        scores = self.forward(x)
        probs = F.softmax(scores, dim=1)
        max_probs, predictions = probs.max(1)
        return max_probs, predictions

    def unfreeze_backbone(self, num_layers_to_unfreeze=2):
        """
        Mở khóa một số tầng cuối của backbone để fine-tuning sâu hơn ở Tuần 2.
        """
        children = list(self.backbone.children())
        for child in children[-num_layers_to_unfreeze:]:
            for param in child.parameters():
                param.requires_grad = True
        print(f"[INFO] Unfroze last {num_layers_to_unfreeze} layers of ResNet-18 backbone.")


if __name__ == '__main__':
    print("--- Test CrowdEmotionModel ---")
    model = CrowdEmotionModel(num_classes=4, freeze_backbone=True)
    model.eval()

    # Kiểm tra với kích thước ảnh chuẩn 112x112 và batch 2
    dummy_input = torch.randn(2, 3, 112, 112)
    with torch.no_grad():
        logits = model(dummy_input)
        probs, labels = model.predict_proba(dummy_input)

    print(f"Input shape:        {dummy_input.shape}")
    print(f"Logits shape:       {logits.shape}")
    print(f"Confidence probs:   {probs.tolist()}")
    print(f"Predicted labels:   {[EMOTION_CLASSES[i] for i in labels.tolist()]}")
    assert logits.shape == (2, 4), f"Expected shape (2, 4), got {logits.shape}"
    print("[OK] CrowdEmotionModel test PASSED!")
