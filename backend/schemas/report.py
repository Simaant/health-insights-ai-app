from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class MarkerData(BaseModel):
    name: str
    value: float
    unit: str
    normal_range: Dict[str, float]
    status: str  # "normal", "low", "high"
    recommendation: str

class ReportCreate(BaseModel):
    filename: str
    original_filename: str
    file_path: str
    markers: List[Dict[str, Any]]  # List of marker data
    text_content: str
    uploaded_at: datetime

class ReportResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    original_filename: str
    file_path: str
    markers: List[Dict[str, Any]]  # List of marker data
    text_content: str
    uploaded_at: datetime
    
    class Config:
        from_attributes = True

class ReportSummary(BaseModel):
    total_markers: int
    abnormal_markers: int
    normal_markers: int
    recommendations: List[str]


