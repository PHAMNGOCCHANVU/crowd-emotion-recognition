from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Segment
from ..schemas import SegmentCreate, SegmentResponse, SegmentUpdate

router = APIRouter(prefix="/api/segments", tags=["Segments"])


@router.post("", response_model=SegmentResponse, status_code=status.HTTP_201_CREATED)
def create_segment(payload: SegmentCreate, db: Session = Depends(get_db)):
    duplicate_conditions = [
        (Segment.name == payload.name) & (Segment.position_id == payload.position_id)
    ]
    if payload.code is not None:
        duplicate_conditions.append(Segment.code == payload.code)

    existing_segment = (
        db.query(Segment).filter(or_(*duplicate_conditions)).first()
    )
    if existing_segment:
        raise HTTPException(
            status_code=400,
            detail="Mã phân khúc hoặc Tên phân khúc trong vị trí này đã tồn tại",
        )

    new_segment = Segment(**payload.model_dump())
    db.add(new_segment)
    db.commit()
    db.refresh(new_segment)
    return new_segment


@router.get("", response_model=List[SegmentResponse])
def get_segments(
    industry_id: Optional[str] = Query(None, alias="industryId"),
    position_id: Optional[str] = Query(None, alias="positionId"),
    search: Optional[str] = Query(None, description="Tìm theo tên hoặc mã"),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Segment).filter(Segment.status != "DELETED")

    if industry_id:
        query = query.filter(Segment.industry_id == industry_id)
    if position_id:
        query = query.filter(Segment.position_id == position_id)
    if search:
        query = query.filter(
            or_(Segment.name.ilike(f"%{search}%"), Segment.code.ilike(f"%{search}%"))
        )

    return (
        query.order_by(Segment.sort_order.asc(), Segment.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{id}", response_model=SegmentResponse)
def get_segment_detail(id: str, db: Session = Depends(get_db)):
    segment = (
        db.query(Segment)
        .filter(Segment.id == id, Segment.status != "DELETED")
        .first()
    )
    if not segment:
        raise HTTPException(status_code=404, detail="Không tìm thấy phân khúc")
    return segment


@router.patch("/{id}", response_model=SegmentResponse)
def update_segment(
    id: str, payload: SegmentUpdate, db: Session = Depends(get_db)
):
    segment = (
        db.query(Segment)
        .filter(Segment.id == id, Segment.status != "DELETED")
        .first()
    )
    if not segment:
        raise HTTPException(status_code=404, detail="Không tìm thấy phân khúc")

    update_data = payload.model_dump(exclude_unset=True)

    if "code" in update_data and update_data["code"] is not None:
        duplicate = (
            db.query(Segment)
            .filter(Segment.code == update_data["code"], Segment.id != id)
            .first()
        )
        if duplicate:
            raise HTTPException(status_code=400, detail="Mã định danh đã tồn tại")

    for key, value in update_data.items():
        setattr(segment, key, value)

    db.commit()
    db.refresh(segment)
    return segment


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_segment(id: str, db: Session = Depends(get_db)):
    segment = db.query(Segment).filter(Segment.id == id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="Không tìm thấy phân khúc")
    if segment.status == "DELETED":
        raise HTTPException(status_code=400, detail="Phân khúc này đã bị xóa trước đó")

    segment.status = "DELETED"
    db.commit()
