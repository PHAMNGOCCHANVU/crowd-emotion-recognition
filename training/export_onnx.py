"""
export_onnx.py — Chuyển đổi và Tối ưu hóa MiniResNetSE sang ONNX (FP32 & INT8)
=============================================================================
1. Xuất mô hình PyTorch (weights/mini_resnet_se_best.pt) sang ONNX FP32 tiêu chuẩn:
   - Input shape: [batch_size, 1, 64, 64] (Dynamic Batch)
   - Output shape: [batch_size, 6] (Dynamic Batch)
   - Opsets: 14 (chuẩn tương thích cao)
2. Lượng tử hóa động (Dynamic Quantization INT8) sang ONNX INT8:
   - Giảm dung lượng file từ ~18.8MB xuống ~3-4MB
   - Tối ưu hóa tốc độ CPU cho hệ thống máy chủ và máy trạm
3. Kiểm tra tính toàn vẹn với onnx.checker và onnxruntime.InferenceSession.
"""

import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import torch
import onnx

from onnxruntime.quantization import quantize_dynamic, QuantType
import onnxruntime as ort

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from model import MiniResNetSE, EMOTION_CLASSES

WEIGHTS_PT = ROOT_DIR / "weights" / "mini_resnet_se_best.pt"
OUTPUT_ONNX = ROOT_DIR / "weights" / "mini_resnet_se_6emo.onnx"
OUTPUT_ONNX_QUANT = ROOT_DIR / "weights" / "mini_resnet_se_6emo_quant.onnx"


def export_to_onnx():
    print("=" * 70)
    print("🚀 BẮT ĐẦU CHUYỂN ĐỔI PYTORCH CHECKPOINT SANG ONNX (64x64 Grayscale)")
    print("=" * 70)

    if not WEIGHTS_PT.exists():
        raise FileNotFoundError(f"Không tìm thấy file trọng số tại: {WEIGHTS_PT}")

    pt_size_mb = WEIGHTS_PT.stat().st_size / (1024 * 1024)
    print(f"📦 Checkpoint PyTorch gốc: {WEIGHTS_PT} ({pt_size_mb:.2f} MB)")

    # 1. Khởi tạo mô hình và nạp trọng số
    model = MiniResNetSE(num_classes=6, dropout_rate=0.0)
    checkpoint = torch.load(str(WEIGHTS_PT), map_location="cpu")
    model.load_state_dict(checkpoint)
    model.eval()
    print("✅ Đã nạp state_dict thành công vào MiniResNetSE.")

    # 2. Tạo dummy input (batch=1, channel=1, height=64, width=64)
    dummy_input = torch.randn(1, 1, 64, 64, dtype=torch.float32)

    # 3. Xuất sang ONNX FP32
    print(f"\n⏳ Đang xuất mô hình ONNX FP32 sang: {OUTPUT_ONNX}...")
    torch.onnx.export(
        model,
        dummy_input,
        str(OUTPUT_ONNX),
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        dynamo=False,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input": {0: "batch_size"},
            "output": {0: "batch_size"},
        },
    )


    # Kiểm tra model ONNX
    onnx_model = onnx.load(str(OUTPUT_ONNX))
    onnx.checker.check_model(onnx_model)
    onnx_size_mb = OUTPUT_ONNX.stat().st_size / (1024 * 1024)
    print(f"✅ Xuất ONNX FP32 thành công: {OUTPUT_ONNX.name} ({onnx_size_mb:.2f} MB)")

    # 4. Lượng tử hóa sang INT8 (Dynamic Quantization)
    print(f"\n⏳ Đang thực hiện Dynamic Quantization sang INT8: {OUTPUT_ONNX_QUANT}...")
    quantize_dynamic(
        model_input=str(OUTPUT_ONNX),
        model_output=str(OUTPUT_ONNX_QUANT),
        weight_type=QuantType.QInt8,
    )
    quant_size_mb = OUTPUT_ONNX_QUANT.stat().st_size / (1024 * 1024)
    reduction = (1 - quant_size_mb / pt_size_mb) * 100
    print(f"✅ Lượng tử hóa INT8 thành công: {OUTPUT_ONNX_QUANT.name} ({quant_size_mb:.2f} MB)")
    print(f"🎉 Tiết kiệm dung lượng: Giảm {reduction:.1f}% so với file .pt gốc!")

    # 5. Kiểm tra chạy thử bằng ONNX Runtime
    print("\n🔍 Kiểm thử chạy thử với ONNX Runtime...")
    test_tensor = torch.randn(2, 1, 64, 64, dtype=torch.float32).numpy()

    for name, path in [("FP32", OUTPUT_ONNX), ("INT8 Quantized", OUTPUT_ONNX_QUANT)]:
        session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
        input_name = session.get_inputs()[0].name
        outputs = session.run(None, {input_name: test_tensor})[0]
        print(f"   • {name:<15}: Output shape={outputs.shape}, Inference OK!")

    print("\n" + "=" * 70)
    print("✨ CHUYỂN ĐỔI & TỐI ƯU HÓA ONNX HOÀN TẤT THÀNH CÔNG 100%!")
    print("=" * 70)


if __name__ == "__main__":
    export_to_onnx()
