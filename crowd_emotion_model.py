import torch
import torch.nn as nn
from model import CustomResNet18, EMOTION_CLASSES


class CrowdEmotionModel(nn.Module):
    """
    Wrapper mô hình nhận diện biểu cảm cảm xúc (6 nhãn).
    Sử dụng kiến trúc CustomResNet18 xây dựng from scratch,
    tối ưu cho ảnh khuôn mặt Grayscale kích thước 48x48.
    """
    def __init__(self, num_classes=6, in_channels=1, dropout_rate=0.5, freeze_backbone=False):
        super(CrowdEmotionModel, self).__init__()
        self.num_classes = num_classes
        self.in_channels = in_channels
        self.network = CustomResNet18(
            num_classes=num_classes,
            in_channels=in_channels,
            dropout_rate=dropout_rate
        )

        # Hỗ trợ freeze nếu người dùng cần
        if freeze_backbone:
            for name, param in self.network.named_parameters():
                if not name.startswith('fc'):
                    param.requires_grad = False

    def forward(self, x):
        return self.network(x)

    def predict(self, x):
        return self.network.predict(x)

    def predict_proba(self, x):
        return self.network.predict_proba(x)

    def unfreeze_backbone(self, num_layers_to_unfreeze=None):
        """Mở khóa toàn bộ hoặc một số layer của mạng"""
        for param in self.network.parameters():
            param.requires_grad = True
        print("[INFO] Unfroze parameters in CustomResNet18.")


if __name__ == '__main__':
    print("--- Test CrowdEmotionModel ---")
    model = CrowdEmotionModel(num_classes=6, in_channels=1)
    model.eval()

    dummy_input = torch.randn(2, 1, 48, 48)
    with torch.no_grad():
        logits = model(dummy_input)
        probs, labels = model.predict_proba(dummy_input)

    print(f"Input shape:        {dummy_input.shape}")
    print(f"Logits shape:       {logits.shape}")
    print(f"Confidence probs:   {probs.tolist()}")
    print(f"Predicted labels:   {[EMOTION_CLASSES[i] for i in labels.tolist()]}")
    assert logits.shape == (2, 6), f"Expected shape (2, 6), got {logits.shape}"
    print("[OK] CrowdEmotionModel test PASSED!")
