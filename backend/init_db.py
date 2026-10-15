import sys
from pathlib import Path

# Đảm bảo import được module backend
BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
for p in [str(BACKEND_DIR), str(ROOT_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Đảm bảo UTF-8 console output trên Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.database import engine, DATABASE_URL, Base
import backend.models  # Nạp toàn bộ ORM Models vào Base.metadata


def init_database():
    """
    Ánh xạ các model SQLAlchemy (ORM) thành các bảng trong Database
    dựa trên cấu hình biến môi trường DATABASE_URL.
    """
    # Ẩn mật khẩu khi in ra console để bảo mật
    safe_url = DATABASE_URL
    if "@" in safe_url and ":" in safe_url:
        try:
            prefix, rest = safe_url.split("://", 1)
            creds, host_part = rest.split("@", 1)
            user = creds.split(":", 1)[0]
            safe_url = f"{prefix}://{user}:****@{host_part}"
        except Exception:
            pass

    print(f"🔗 Đang kết nối tới Database: {safe_url}")
    print("⏳ Đang ánh xạ ORM Models sang các bảng...")

    # Tạo toàn bộ bảng được định nghĩa trong models.py nếu chưa tồn tại
    Base.metadata.create_all(bind=engine)

    # Tự động bổ sung cột video_url nếu bảng session_details đã tồn tại từ trước
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        if "session_details" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("session_details")]
            if "video_url" not in columns:
                print("⚡ Phát hiện thiếu cột video_url trong session_details, đang tự động cập nhật...")
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE session_details ADD COLUMN video_url VARCHAR(500);"))
                    conn.commit()
                print("✅ Đã bổ sung cột video_url thành công!")
    except Exception as e:
        print(f"⚠️ Kiểm tra cột video_url: {e}")

    print("\n✅ ÁNH XẠ THÀNH CÔNG! Danh sách các bảng đã được đồng bộ:")
    for table_name in Base.metadata.tables.keys():
        print(f"   - 📋 Bảng: {table_name}")
    print("\n🎉 Cơ sở dữ liệu đã sẵn sàng cho ứng dụng!")


if __name__ == "__main__":
    init_database()
