from typing import Optional
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from .database import get_db
from .models import User


def get_current_user(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """
    Xác thực người dùng:
    - Nếu có X-User-Id header, tìm theo ID đó.
    - Nếu có authorization Bearer token chứa user ID hoặc email.
    - Nếu không có, fallback về 'user_123' (ứng viên) hoặc 'admin_123' (quản trị viên)
      để đảm bảo môi trường local/dev hoạt động thông suốt không bị lỗi 401 giả lập.
    """
    user = None
    if x_user_id:
        user = db.query(User).filter(User.id == x_user_id).first()

    if not user and authorization:
        token = authorization.replace("Bearer ", "").strip()
        user = db.query(User).filter((User.id == token) | (User.email == token)).first()

    if not user:
        # Fallback an toàn cho dev/local
        user = db.query(User).filter(User.id == "user_123").first()
        if not user:
            user = db.query(User).filter(User.role == "USER").first()
        if not user:
            user = db.query(User).filter(User.id == "admin_123").first()
        if not user:
            user = db.query(User).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Xác thực người dùng thất bại. Vui lòng chạy init_db.py để nạp dữ liệu mẫu.",
        )
    return user


def get_current_admin_user(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """
    Xác thực quyền Quản trị viên (ADMIN)
    """
    explicit_credentials_provided = bool(x_user_id or authorization)
    user = None
    if x_user_id:
        user = db.query(User).filter(User.id == x_user_id).first()

    if not user and authorization:
        token = authorization.replace("Bearer ", "").strip()
        user = db.query(User).filter((User.id == token) | (User.email == token)).first()

    if not user and not explicit_credentials_provided:
        # Chỉ fallback về admin_123 khi không có thông tin xác thực nào được gửi lên (chế độ dev local)
        user = db.query(User).filter(User.id == "admin_123").first()
        if not user:
            user = db.query(User).filter(User.role == "ADMIN").first()

    if not user or user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền quản trị viên để thực hiện thao tác này",
        )
    return user
