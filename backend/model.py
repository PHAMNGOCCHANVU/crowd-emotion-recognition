import torch
import torch.nn as nn
import torch.nn.functional as F

# 6 nhãn cảm xúc chuẩn hóa
EMOTION_CLASSES = ['Contempt', 'Fear', 'Happy', 'Normal', 'Sad', 'Surprised']


class BasicBlock(nn.Module):
    """
    Residual Block cơ bản với 2 lớp tích chập 3x3 và đường tắt Skip Connection.
    """
    expansion = 1

    def __init__(self, in_channels, out_channels, stride=1, downsample=None):
        super(BasicBlock, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)

        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)

        self.downsample = downsample

    def forward(self, x):
        identity = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)

        if self.downsample is not None:
            identity = self.downsample(x)

        out += identity
        out = self.relu(out)
        return out


class CustomResNet18(nn.Module):
    """
    CustomResNet18 viết hoàn toàn from scratch (không dùng pre-trained weights)
    Tối ưu hóa chuyên biệt cho ảnh biểu cảm khuôn mặt 48x48 Grayscale (1 channel).
    
    Đặc điểm kiến trúc:
    - Conv1 dùng kernel 3x3 (stride=1, padding=1) thay vì 7x7 để bảo toàn đặc trưng ảnh nhỏ 48x48.
    - Lược bỏ MaxPool đầu vào tránh làm mất thông tin không gian quá sớm.
    - 4 Layer groups (mỗi group gồm 2 BasicBlock): 64 -> 128 -> 256 -> 512 channels.
    - AdaptiveAvgPool2d((1, 1)) gom cụm đặc trưng.
    - Dropout (chống overfit khi train from scratch).
    - Fully Connected phân loại 6 nhãn cảm xúc.
    - Trọng số khởi tạo theo chuẩn Kaiming / He Normal tối ưu cho hàm kích hoạt ReLU.
    """
    def __init__(self, num_classes=6, in_channels=1, dropout_rate=0.5):
        super(CustomResNet18, self).__init__()
        self.num_classes = num_classes
        self.in_channels = in_channels

        # Stem layer cho ảnh 48x48
        self.conv1 = nn.Conv2d(in_channels, 64, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)

        # 4 nhóm tầng Residual
        self.layer1 = self._make_layer(64, 64, num_blocks=2, stride=1)
        self.layer2 = self._make_layer(64, 128, num_blocks=2, stride=2)   # 48 -> 24
        self.layer3 = self._make_layer(128, 256, num_blocks=2, stride=2)  # 24 -> 12
        self.layer4 = self._make_layer(256, 512, num_blocks=2, stride=2)  # 12 -> 6

        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.dropout = nn.Dropout(dropout_rate)
        self.fc = nn.Linear(512 * BasicBlock.expansion, num_classes)

        # Khởi tạo trọng số Kaiming He
        self._initialize_weights()

    def _make_layer(self, in_channels, out_channels, num_blocks, stride):
        downsample = None
        if stride != 1 or in_channels != out_channels * BasicBlock.expansion:
            downsample = nn.Sequential(
                nn.Conv2d(in_channels, out_channels * BasicBlock.expansion, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(out_channels * BasicBlock.expansion)
            )

        layers = []
        layers.append(BasicBlock(in_channels, out_channels, stride, downsample))
        for _ in range(1, num_blocks):
            layers.append(BasicBlock(out_channels * BasicBlock.expansion, out_channels))

        return nn.Sequential(*layers)

    def _initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.constant_(m.bias, 0)

    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.dropout(x)
        x = self.fc(x)
        return x

    def predict(self, x):
        """Trả về nhãn dự đoán có score cao nhất"""
        scores = self.forward(x)
        _, predictions = scores.max(1)
        return predictions

    def predict_proba(self, x):
        """Trả về xác suất (confidence) và nhãn dự đoán"""
        scores = self.forward(x)
        probs = F.softmax(scores, dim=1)
        max_probs, predictions = probs.max(1)
        return max_probs, predictions


# =============================================================================
# Compact Residual-SE Network (Mini-ResNet-SE)
# Tối ưu hóa đặc chế cho nhận diện 6 nhãn cảm xúc với Squeeze-and-Excitation
# =============================================================================

class SEBlock(nn.Module):
    """Squeeze-and-Excitation Block tái hiệu chỉnh trọng số kênh đặc trưng."""
    def __init__(self, channels, reduction=16):
        super(SEBlock, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(channels, channels // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(channels // reduction, channels, bias=False),
            nn.Sigmoid()
        )

    def forward(self, x):
        b, c, _, _ = x.size()
        y = x.view(b, c, -1).mean(dim=2)
        y = self.fc(y).view(b, c, 1, 1)
        return x * y


class MiniResBlock(nn.Module):
    """Khối Residual nhỏ tích hợp SE Attention và Skip Connection."""
    def __init__(self, in_channels, out_channels, stride=1):
        super(MiniResBlock, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)
        self.se = SEBlock(out_channels)

        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(out_channels)
            )

    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out = self.se(out)
        out += self.shortcut(x)
        return F.relu(out)


class MiniResNetSE(nn.Module):
    """
    Mini-ResNet-SE (~3.1M tham số) tối ưu cho nhận diện 6 nhãn biểu cảm.
    Đầu vào: Ảnh xám Grayscale 1 kênh (mặc định 64x64).
    """
    def __init__(self, num_classes=6, dropout_rate=0.4):
        super(MiniResNetSE, self).__init__()
        self.in_channels = 32

        # Tầng Conv đầu tiên thích ứng trực tiếp ảnh xám 1 kênh
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(32)

        # 4 Khối Residual-SE thu nhỏ kích thước không gian và tăng kênh
        self.layer1 = MiniResBlock(32, 64, stride=2)   # 64x64 -> 32x32
        self.layer2 = MiniResBlock(64, 128, stride=2)  # 32x32 -> 16x16
        self.layer3 = MiniResBlock(128, 256, stride=2) # 16x16 -> 8x8
        self.layer4 = MiniResBlock(256, 512, stride=2) # 8x8 -> 4x4

        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.dropout = nn.Dropout(p=dropout_rate)
        self.fc = nn.Linear(512, num_classes)

    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.layer1(out)
        out = self.layer2(out)
        out = self.layer3(out)
        out = self.layer4(out)
        out = self.global_pool(out)
        out = torch.flatten(out, 1)
        out = self.dropout(out)
        return self.fc(out)

    def predict(self, x):
        scores = self.forward(x)
        _, preds = scores.max(1)
        return preds

    def predict_proba(self, x):
        scores = self.forward(x)
        probs = F.softmax(scores, dim=1)
        max_probs, preds = probs.max(1)
        return max_probs, preds


# Alias để tương thích tên gọi cũ
Model = MiniResNetSE



if __name__ == '__main__':
    print("--- Test CustomResNet18 Architecture ---")
    model = CustomResNet18(num_classes=6, in_channels=1, dropout_rate=0.5)
    model.eval()

    # Thử nghiệm với batch=4 ảnh Grayscale 48x48
    dummy_input = torch.randn(4, 1, 48, 48)
    with torch.no_grad():
        logits = model(dummy_input)
        probs, preds = model.predict_proba(dummy_input)

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

    print(f"Input shape:        {dummy_input.shape}")
    print(f"Logits shape:       {logits.shape}")
    print(f"Confidence probs:   {probs.tolist()}")
    print(f"Predicted labels:   {[EMOTION_CLASSES[i] for i in preds.tolist()]}")
    print(f"Total parameters:   {total_params:,}")
    print(f"Trainable params:   {trainable_params:,}")

    assert logits.shape == (4, 6), f"Expected shape (4, 6), got {logits.shape}"
    print("[OK] CustomResNet18 test PASSED!")
