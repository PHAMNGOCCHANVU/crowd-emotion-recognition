from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from .database import get_db
from .models import User


def get_current_user(
    token: str = "mock_token",
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == "admin_123").first()
    if not user:
        raise HTTPException(status_code=401, detail="Xác thực thất bại")
    return user


def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền quản trị viên để thực hiện thao tác này",
        )
    return current_user
