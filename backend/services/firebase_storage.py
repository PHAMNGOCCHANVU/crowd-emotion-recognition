import os
import json
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

_firebase_app = None
_bucket = None


def init_firebase() -> bool:
    """
    Khởi tạo Firebase Admin SDK:
    - Tìm file serviceAccountKey.json trong thư mục backend/ hoặc đường dẫn FIREBASE_CREDENTIALS_PATH.
    - Hoặc đọc JSON trực tiếp từ biến môi trường FIREBASE_CREDENTIALS_JSON.
    - Cấu hình Storage Bucket từ FIREBASE_STORAGE_BUCKET.
    - Trả về True nếu khởi tạo thành công, False nếu chưa có thông tin chứng thực.
    """
    global _firebase_app, _bucket

    if _firebase_app is not None and _bucket is not None:
        return True

    try:
        import firebase_admin
        from firebase_admin import credentials, storage

        # 1. Tìm thông tin credentials
        cred = None
        json_env = os.getenv("FIREBASE_CREDENTIALS_JSON")
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")

        backend_dir = Path(__file__).resolve().parent.parent
        default_key_path = backend_dir / "serviceAccountKey.json"

        if json_env:
            try:
                cert_dict = json.loads(json_env)
                cred = credentials.Certificate(cert_dict)
            except Exception as e:
                logger.warning(f"[Firebase Storage] Lỗi parse FIREBASE_CREDENTIALS_JSON: {e}")
        elif cred_path and Path(cred_path).exists():
            cred = credentials.Certificate(cred_path)
        elif default_key_path.exists():
            cred = credentials.Certificate(str(default_key_path))

        if not cred:
            # Chưa có chứng thực, hệ thống hoạt động ở chế độ Fallback
            return False

        # Khởi tạo App Firebase nếu chưa khởi tạo
        if not firebase_admin._apps:
            opts = {"storageBucket": bucket_name} if bucket_name else {}
            _firebase_app = firebase_admin.initialize_app(cred, opts)
        else:
            _firebase_app = firebase_admin.get_app()

        _bucket = storage.bucket(bucket_name, app=_firebase_app)
        print(f"[Firebase Storage] Đã kết nối thành công tới Bucket: {_bucket.name or bucket_name}")
        return True

    except Exception as e:
        logger.warning(f"[Firebase Storage Warning] Không thể khởi tạo Firebase Admin: {e}")
        return False


def upload_interview_video_to_firebase(
    local_path: str,
    session_id: str,
    order_index: int,
) -> Optional[str]:
    """
    Tải file video câu trả lời lên Firebase Cloud Storage:
    - Đường dẫn trên Cloud: interviews/{session_id}/answer_q{order_index}{ext}
    - Tạo Signed URL có thời hạn hoặc Public URL cho Frontend phát video trực tiếp.
    - Nếu chưa cấu hình Firebase, trả về None (an toàn, không gây crash luồng AI).
    """
    if not init_firebase() or _bucket is None:
        print("[Firebase Storage Notice] Chưa cấu hình key Firebase trong .env/serviceAccountKey.json. Bỏ qua tải lên đám mây.")
        return None

    if not os.path.exists(local_path):
        logger.warning(f"[Firebase Storage] Không tìm thấy file cục bộ để upload: {local_path}")
        return None

    try:
        file_ext = os.path.splitext(local_path)[1] or ".webm"
        blob_path = f"interviews/{session_id}/answer_q{order_index}{file_ext}"
        blob = _bucket.blob(blob_path)

        content_type = "video/webm"
        if file_ext.lower() == ".mp4":
            content_type = "video/mp4"

        print(f"[Firebase Storage] Đang tải video câu {order_index} lên: {blob_path}...")
        blob.upload_from_filename(local_path, content_type=content_type)

        # Tạo Signed URL cho phép xem trực tiếp trong 7 ngày
        try:
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(days=7),
                method="GET",
            )
            print(f"[Firebase Storage] Tải lên thành công! Signed URL: {signed_url[:50]}...")
            return signed_url
        except Exception:
            # Nếu bucket hỗ trợ public url
            blob.make_public()
            return blob.public_url

    except Exception as e:
        logger.warning(f"[Firebase Storage Error] Lỗi upload video lên Firebase: {e}")
        return None
