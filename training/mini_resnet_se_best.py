# Định nghĩa Kiến Trúc Đặc Chế: Compact Residual-SE Network (Mini-ResNet-SE)

# import torch
# import torch.nn as nn
# import torch.nn.functional as F

# class SEBlock(nn.Module):
#     def __init__(self, channels, reduction=16):
#         super(SEBlock, self).__init__()
#         self.fc = nn.Sequential(
#             nn.Linear(channels, channels // reduction, bias=False),
#             nn.ReLU(inplace=True),
#             nn.Linear(channels // reduction, channels, bias=False),
#             nn.Sigmoid()
#         )

#     def forward(self, x):
#         b, c, _, _ = x.size()
#         y = x.view(b, c, -1).mean(dim=2)
#         y = self.fc(y).view(b, c, 1, 1)
#         return x * y

# class MiniResBlock(nn.Module):
#     def __init__(self, in_channels, out_channels, stride=1):
#         super(MiniResBlock, self).__init__()
#         self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1, bias=False)
#         self.bn1 = nn.BatchNorm2d(out_channels)
#         self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1, bias=False)
#         self.bn2 = nn.BatchNorm2d(out_channels)
#         self.se = SEBlock(out_channels)

#         self.shortcut = nn.Sequential()
#         if stride != 1 or in_channels != out_channels:
#             self.shortcut = nn.Sequential(
#                 nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride, bias=False),
#                 nn.BatchNorm2d(out_channels)
#             )

#     def forward(self, x):
#         out = F.relu(self.bn1(self.conv1(x)))
#         out = self.bn2(self.conv2(out))
#         out = self.se(out)
#         out += self.shortcut(x)
#         return F.relu(out)

# class MiniResNetSE(nn.Module):
#     def __init__(self, num_classes=6, dropout_rate=0.4):
#         super(MiniResNetSE, self).__init__()
#         self.in_channels = 32

#         # Tầng Convolution đầu tiên thích ứng trực tiếp 1 kênh màu xám
#         self.conv1 = nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1, bias=False)
#         self.bn1 = nn.BatchNorm2d(32)

#         # Các khối Residual nông
#         self.layer1 = MiniResBlock(32, 64, stride=2)   # 64x64 -> 32x32
#         self.layer2 = MiniResBlock(64, 128, stride=2)  # 32x32 -> 16x16
#         self.layer3 = MiniResBlock(128, 256, stride=2) # 16x16 -> 8x8
#         self.layer4 = MiniResBlock(256, 512, stride=2) # 8x8 -> 4x4

#         self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
#         self.dropout = nn.Dropout(p=dropout_rate)
#         self.fc = nn.Linear(512, num_classes)

#     def forward(self, x):
#         out = F.relu(self.bn1(self.conv1(x)))
#         out = self.layer1(out)
#         out = self.layer2(out)
#         out = self.layer3(out)
#         out = self.layer4(out)
#         out = self.global_pool(out)
#         out = torch.flatten(out, 1)
#         out = self.dropout(out)
#         return self.fc(out)

# # Khởi tạo mô hình
# model_mini_resnet = MiniResNetSE(num_classes=CONFIG['num_classes'], dropout_rate=0.4).to(device)

# total_params = sum(p.numel() for p in model_mini_resnet.parameters())
# print(f"🧱 Mô hình Mini-ResNet-SE đã sẵn sàng!")
# print(f"📌 Tổng số tham số tối ưu: {total_params:,} (~3.1 triệu tham số - đúng điểm 'Sweet Spot'!)")


# # 1. Khởi tạo lại cấu trúc mô hình Mini-ResNet-SE
# model_resume = MiniResNetSE(num_classes=CONFIG['num_classes'], dropout_rate=0.45).to(device)

# # 2. Tải trọng số tốt nhất đã huấn luyện (61.63%) vào mô hình
# weights_path = CONFIG['save_path_mini_resnet']
# if os.path.exists(weights_path):
#     checkpoint = torch.load(weights_path, map_location=device)
#     model_resume.load_state_dict(checkpoint)
#     print(f"✅ Đã nạp thành công trọng số Best Model từ: {weights_path}")
# else:
#     print(f"⚠️ Không tìm thấy file trọng số tại {weights_path}, vui lòng kiểm tra lại đường dẫn.")

# # 3. Thiết lập chu kỳ huấn luyện mới (Fine-tuning tiếp tục)
# # Khởi tạo Learning Rate nhỏ hơn một chút so với ban đầu (ví dụ: 3e-4) để tránh phá hỏng cấu trúc đã tối ưu
# optimizer_resume = torch.optim.AdamW(model_resume.parameters(), lr=3e-4, weight_decay=3e-4)

# # Sử dụng CosineAnnealingLR với chu kỳ mới dài hơn (ví dụ: 25 epochs)
# scheduler_resume = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer_resume, T_max=25, eta_min=1e-6)
# criterion_resume = nn.CrossEntropyLoss(weight=class_weights_tensor, label_smoothing=0.1)

# print("⚙️ Bộ tối ưu và Scheduler mới đã được thiết lập sẵn sàng để huấn luyện tiếp tục!")

