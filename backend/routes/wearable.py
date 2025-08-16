from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from database import get_db
from models import User, WearableData
from utils.auth import verify_token

router = APIRouter()

class WearableDataCreate(BaseModel):
    device_type: str  # fitbit, apple_watch, garmin, etc.
    data_type: str    # steps, heart_rate, sleep, calories, etc.
    value: Optional[float] = None
    unit: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

class WearableDataResponse(BaseModel):
    id: str
    device_type: str
    data_type: str
    value: Optional[float]
    unit: Optional[str]
    timestamp: str
    raw_data: Optional[Dict[str, Any]]

@router.post("/data", response_model=WearableDataResponse)
async def add_wearable_data(
    data: WearableDataCreate,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    wearable_data = WearableData(
        user_id=current_user.id,
        device_type=data.device_type,
        data_type=data.data_type,
        value=data.value,
        unit=data.unit,
        raw_data=data.raw_data
    )
    
    db.add(wearable_data)
    db.commit()
    db.refresh(wearable_data)
    
    return WearableDataResponse(
        id=wearable_data.id,
        device_type=wearable_data.device_type,
        data_type=wearable_data.data_type,
        value=wearable_data.value,
        unit=wearable_data.unit,
        timestamp=wearable_data.timestamp.isoformat(),
        raw_data=wearable_data.raw_data
    )

@router.get("/data", response_model=List[WearableDataResponse])
async def get_wearable_data(
    device_type: Optional[str] = None,
    data_type: Optional[str] = None,
    days: Optional[int] = 7,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    query = db.query(WearableData).filter(WearableData.user_id == current_user.id)
    
    if device_type:
        query = query.filter(WearableData.device_type == device_type)
    
    if data_type:
        query = query.filter(WearableData.data_type == data_type)
    
    if days:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(WearableData.timestamp >= cutoff_date)
    
    data = query.order_by(WearableData.timestamp.desc()).all()
    
    return [
        WearableDataResponse(
            id=item.id,
            device_type=item.device_type,
            data_type=item.data_type,
            value=item.value,
            unit=item.unit,
            timestamp=item.timestamp.isoformat(),
            raw_data=item.raw_data
        )
        for item in data
    ]

@router.get("/data/summary")
async def get_wearable_summary(
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get a summary of wearable data for the last 7 days"""
    cutoff_date = datetime.utcnow() - timedelta(days=7)
    
    # Get latest data for each type
    summary = {}
    
    # Steps
    steps_data = db.query(WearableData).filter(
        WearableData.user_id == current_user.id,
        WearableData.data_type == "steps",
        WearableData.timestamp >= cutoff_date
    ).order_by(WearableData.timestamp.desc()).first()
    
    if steps_data:
        summary["steps"] = {
            "latest": steps_data.value,
            "unit": steps_data.unit,
            "device": steps_data.device_type
        }
    
    # Heart rate
    heart_rate_data = db.query(WearableData).filter(
        WearableData.user_id == current_user.id,
        WearableData.data_type == "heart_rate",
        WearableData.timestamp >= cutoff_date
    ).order_by(WearableData.timestamp.desc()).first()
    
    if heart_rate_data:
        summary["heart_rate"] = {
            "latest": heart_rate_data.value,
            "unit": heart_rate_data.unit,
            "device": heart_rate_data.device_type
        }
    
    # Sleep
    sleep_data = db.query(WearableData).filter(
        WearableData.user_id == current_user.id,
        WearableData.data_type == "sleep",
        WearableData.timestamp >= cutoff_date
    ).order_by(WearableData.timestamp.desc()).first()
    
    if sleep_data:
        summary["sleep"] = {
            "latest": sleep_data.value,
            "unit": sleep_data.unit,
            "device": sleep_data.device_type
        }
    
    # Calories
    calories_data = db.query(WearableData).filter(
        WearableData.user_id == current_user.id,
        WearableData.data_type == "calories",
        WearableData.timestamp >= cutoff_date
    ).order_by(WearableData.timestamp.desc()).first()
    
    if calories_data:
        summary["calories"] = {
            "latest": calories_data.value,
            "unit": calories_data.unit,
            "device": calories_data.device_type
        }
    
    return summary

@router.post("/data/bulk")
async def add_bulk_wearable_data(
    data_list: List[WearableDataCreate],
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Add multiple wearable data points at once"""
    wearable_data_list = []
    
    for data in data_list:
        wearable_data = WearableData(
            user_id=current_user.id,
            device_type=data.device_type,
            data_type=data.data_type,
            value=data.value,
            unit=data.unit,
            raw_data=data.raw_data
        )
        wearable_data_list.append(wearable_data)
    
    db.add_all(wearable_data_list)
    db.commit()
    
    return {"message": f"Successfully added {len(data_list)} data points"}

@router.delete("/data/{data_id}")
async def delete_wearable_data(
    data_id: str,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    data = db.query(WearableData).filter(
        WearableData.id == data_id,
        WearableData.user_id == current_user.id
    ).first()
    
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wearable data not found"
        )
    
    db.delete(data)
    db.commit()
    
    return {"message": "Data deleted successfully"}
