import os
import torch
import torch.nn as nn
from model import Model


class FeatureExtractor(nn.Module):
    """
    Bóc tách Backbone (mạng trích xuất đặc trưng) từ mô hình gốc patrikken.
    Backbone gồm 4 tầng Conv2D (self.cov_net), trích xuất vector đặc trưng 256 chiều.
    """
    def __init__(self, pretrained_model_path='Trained_Model'):
        super(FeatureExtractor, self).__init__()
        self.feature_dim = 64 * 2 * 2  # 256

        if os.path.exists(pretrained_model_path):
            # Load toàn bộ object mô hình gốc
            original_model = torch.load(pretrained_model_path, weights_only=False)
            self.cov_net = original_model.cov_net
            print(f"Loaded backbone weights successfully from {pretrained_model_path}")
        else:
            print(f"Warning: {pretrained_model_path} not found. Initializing untrained backbone.")
            temp_model = Model()
            self.cov_net = temp_model.cov_net

    def forward(self, x):
        """
        Input: Tensor ảnh [batch_size, 3, 64, 64]
        Output: Feature vector [batch_size, 256]
        """
        x = self.cov_net(x)
        x = x.view(x.size(0), -1)  # Flatten -> [batch, 256]
        return x


if __name__ == '__main__':
    # Kiểm tra trích xuất đặc trưng với tensor ngẫu nhiên
    print("--- Test FeatureExtractor ---")
    extractor = FeatureExtractor('Trained_Model')
    extractor.eval()

    sample_input = torch.randn(2, 3, 64, 64)
    with torch.no_grad():
        features = extractor(sample_input)

    print(f"Input shape:   {sample_input.shape}")
    print(f"Output shape:  {features.shape}")
    assert features.shape == (2, 256), f"Expected shape (2, 256), got {features.shape}"
    print("[OK] FeatureExtractor test PASSED! Feature vector dimension: 256")

