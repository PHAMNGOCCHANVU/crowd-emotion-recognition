from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_admin_user
from ..models import Industry, Position, Segment
from ..schemas import IndustryCreate, PositionCreate

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin Management"],
    dependencies=[Depends(get_current_admin_user)],
)


@router.post("/industries", status_code=status.HTTP_201_CREATED)
def create_industry(payload: IndustryCreate, db: Session = Depends(get_db)):
    exist = (
        db.query(Industry)
        .filter((Industry.code == payload.code) | (Industry.name == payload.name))
        .first()
    )
    if exist:
        raise HTTPException(status_code=400, detail="Mã hoặc Tên Ngành đã tồn tại")

    new_ind = Industry(**payload.model_dump())
    db.add(new_ind)
    db.commit()
    db.refresh(new_ind)
    return new_ind


@router.delete("/industries/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_industry(id: str, db: Session = Depends(get_db)):
    industry = db.query(Industry).filter(Industry.id == id).first()
    if not industry:
        raise HTTPException(status_code=404, detail="Không tìm thấy ngành")

    has_positions = (
        db.query(Position)
        .filter(Position.industry_id == id, Position.status != "DELETED")
        .first()
    )
    if has_positions:
        raise HTTPException(
            status_code=400,
            detail="Không thể xóa: Đang có vị trí trực thuộc ngành này",
        )

    industry.status = "DELETED"
    db.commit()


@router.post("/positions", status_code=status.HTTP_201_CREATED)
def create_position(payload: PositionCreate, db: Session = Depends(get_db)):
    industry = (
        db.query(Industry)
        .filter(Industry.id == payload.industry_id, Industry.status != "DELETED")
        .first()
    )
    if not industry:
        raise HTTPException(status_code=404, detail="Ngành không tồn tại")

    new_pos = Position(**payload.model_dump())
    db.add(new_pos)
    db.commit()
    db.refresh(new_pos)
    return new_pos


@router.delete("/positions/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_position(id: str, db: Session = Depends(get_db)):
    pos = db.query(Position).filter(Position.id == id).first()
    if not pos:
        raise HTTPException(status_code=404, detail="Không tìm thấy vị trí")

    has_segments = (
        db.query(Segment)
        .filter(Segment.position_id == id, Segment.status != "DELETED")
        .first()
    )
    if has_segments:
        raise HTTPException(
            status_code=400,
            detail="Không thể xóa: Đang có Phân khúc gắn với vị trí này",
        )

    pos.status = "DELETED"
    db.commit()
