from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import User
from ..schemas import (
    ChangePasswordRequest,
    UserProfileResponse,
    UserProfileUpdate,
)
from ..security import get_password_hash, verify_password

router = APIRouter(prefix="/api/user", tags=["User Profile & Account"])


@router.get("/profile", response_model=UserProfileResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/profile", response_model=UserProfileResponse)
def update_my_profile(
    payload: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    update_data = payload.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(current_user, key, value)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.hashed_password or not verify_password(
        payload.current_password, current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu hiện tại không chính xác",
        )

    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu mới không được trùng với mật khẩu cũ",
        )

    current_user.hashed_password = get_password_hash(payload.new_password)
    db.commit()

    return {
        "message": (
            "Đổi mật khẩu thành công. Vui lòng sử dụng mật khẩu mới "
            "cho lần đăng nhập sau."
        )
    }
