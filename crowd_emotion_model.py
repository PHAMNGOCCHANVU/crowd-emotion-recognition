import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models


EMOTION_CLASSES = ["Happy", "Normal", "Sad", "Surprised"]


class CrowdEmotionModel(nn.Module):
    """ResNet-18 backbone with a four-class emotion head."""

    def __init__(self, num_classes=4, freeze_backbone=True, pretrained_backbone=True):
        super().__init__()
        weights = models.ResNet18_Weights.DEFAULT if pretrained_backbone else None
        resnet = models.resnet18(weights=weights)
        self.backbone = nn.Sequential(*list(resnet.children())[:-1])
        if freeze_backbone:
            for parameter in self.backbone.parameters():
                parameter.requires_grad = False
        self.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(512, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, num_classes),
        )

    def forward(self, x):
        features = self.backbone(x).flatten(1)
        return self.classifier(features)

    def predict_proba(self, x):
        probabilities = F.softmax(self.forward(x), dim=1)
        return probabilities.max(dim=1)
