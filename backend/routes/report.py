from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from datetime import datetime
from database import get_db
from models import User, Report, ChatSession, ChatMessage
from utils.auth import verify_token
from utils.parse_markers import parse_markers
from utils.prompts import build_prompt
from utils.agent_manager import run_agent
from utils.ocr import ocr_any
from utils.constants import NO_MARKERS_FOUND_MSG, ALL_NORMAL_MSG
from utils.health_marker_detector import HealthMarkerDetector
# Try to import advanced OCR, but provide fallback if not available
try:
    from utils.advanced_ocr import AdvancedOCR
    advanced_ocr = AdvancedOCR()
    ADVANCED_OCR_AVAILABLE = True
except Exception as e:
    print(f"Warning: Advanced OCR not available: {e}")
    advanced_ocr = None
    ADVANCED_OCR_AVAILABLE = False

router = APIRouter()

# Initialize the health marker detector
marker_detector = HealthMarkerDetector()

# Ensure upload directory exists
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/debug-ocr")
async def debug_ocr(
    file: UploadFile = File(...)
):
    """Debug endpoint to see what text is extracted from uploaded files."""
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Only PDF and images are allowed."
        )
    
    try:
        # Extract text from file
        text_content = ""
        
        if file.content_type == "application/pdf":
            # Handle PDF files
            import PyPDF2
            import io
            pdf_content = await file.read()
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
        else:
            # Handle image files
            from PIL import Image
            import io
            image_content = await file.read()
            image = Image.open(io.BytesIO(image_content))
            
            # Use OCR for text extraction
            try:
                if ADVANCED_OCR_AVAILABLE and advanced_ocr:
                    # Try advanced OCR first
                    text_content = advanced_ocr.extract_text_with_multiple_configs(image)
                    
                    # If no text found, try region-based extraction
                    if not text_content.strip():
                        region_texts = advanced_ocr.extract_text_regions(image)
                        text_content = ' '.join(region_texts)
                
                # Fall back to basic OCR if advanced OCR not available or failed
                if not text_content.strip():
                    import pytesseract
                    # Basic preprocessing
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    
                    # Resize if too small
                    width, height = image.size
                    if width < 800 or height < 600:
                        scale_factor = max(800 / width, 600 / height)
                        new_width = int(width * scale_factor)
                        new_height = int(height * scale_factor)
                        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Basic OCR
                    custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz:()./\- ngmLµ%'
                    text_content = pytesseract.image_to_string(image, config=custom_config, lang='eng')
                    
                    if not text_content.strip():
                        text_content = pytesseract.image_to_string(image, lang='eng')
                        
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Error processing image with OCR: {str(e)}"
                )
        
        # Try to detect markers
        detected_markers = marker_detector.detect_markers(text_content)
        
        return {
            "extracted_text": text_content,
            "text_length": len(text_content),
            "detected_markers": len(detected_markers),
            "markers": [
                {
                    "name": m.name,
                    "value": m.value,
                    "unit": m.unit,
                    "status": m.status,
                    "raw_text": m.raw_text
                } for m in detected_markers
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )

@router.post("/debug-text")
async def debug_text(
    text_data: dict
):
    """Debug endpoint to test marker detection with manual text input."""
    
    try:
        text_content = text_data.get("text", "")
        
        if not text_content.strip():
            raise HTTPException(
                status_code=400,
                detail="No text provided."
            )
        
        # Try to detect markers
        detected_markers = marker_detector.detect_markers(text_content)
        
        return {
            "extractedText": text_content,
            "textLength": len(text_content),
            "markersFound": len(detected_markers),
            "markers": [
                {
                    "name": m.name,
                    "value": m.value,
                    "unit": m.unit,
                    "status": m.status,
                    "normalRange": f"{m.normal_range.get('min', '')}-{m.normal_range.get('max', '')}",
                    "recommendation": m.recommendation
                } for m in detected_markers
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing text: {str(e)}"
        )

@router.post("/upload")
async def upload_report(
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db),
    filename: Optional[str] = Form(None),
    text_content: Optional[str] = Form(None)
):
    try:
        # Handle manual entry vs file upload
        if file is None and text_content is not None:
            # Manual entry mode
            text = text_content or ""
            file_path = None
            file_type = "manual_entry"
            report_filename = filename or "Manual Entry"
            
            # Use the new marker detector for manual entry
            detected_markers = marker_detector.detect_markers(text)
            
            # Convert to the expected format
            extracted = {}
            flagged = {}
            
            for marker in detected_markers:
                marker_data = {
                    "value": marker.value,
                    "unit": marker.unit,
                    "normal_range": marker.normal_range,
                    "status": marker.status,
                    "recommendation": marker.recommendation
                }
                extracted[marker.name] = marker_data
                
                if marker.status != "normal":
                    flagged[marker.name] = marker_data
        else:
            # File upload mode
            if file is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either a file or manual data must be provided."
                )
            
            # Validate file type
            allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]
            if file.content_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid file type. Only PDF and images are allowed."
                )
            
            # Read file content
            file_bytes = await file.read()
            
            # Save file to disk
            file_id = str(uuid.uuid4())
            file_extension = file.filename.split('.')[-1] if file.filename else 'pdf'
            file_path = os.path.join(UPLOAD_DIR, f"{file_id}.{file_extension}")
            
            with open(file_path, "wb") as f:
                f.write(file_bytes)
            
            # Extract text using OCR
            text = ocr_any(file_bytes, filename=file.filename or "", content_type=file.content_type)
            
            # Parse markers using the new detector
            detected_markers = marker_detector.detect_markers(text)
            
            # Convert to the expected format
            extracted = {}
            flagged = {}
            
            for marker in detected_markers:
                marker_data = {
                    "value": marker.value,
                    "unit": marker.unit,
                    "normal_range": marker.normal_range,
                    "status": marker.status,
                    "recommendation": marker.recommendation
                }
                extracted[marker.name] = marker_data
                
                if marker.status != "normal":
                    flagged[marker.name] = marker_data
            
            report_filename = file.filename or f"report_{file_id}"
            file_type = file.content_type
        
        # Generate AI recommendations
        recommendations_text = ""
        if extracted:
            if flagged:
                prompt = build_prompt(flagged, wearable=None)
                try:
                    recommendations_text = run_agent(prompt)
                except Exception as e:
                    items = ", ".join(f"{m}: {d['value']} {d.get('unit','')}".strip() for m, d in flagged.items())
                    recommendations_text = f"Abnormal markers detected: {items}. (AI recommendation temporarily unavailable.)"
            else:
                recommendations_text = ALL_NORMAL_MSG
        else:
            recommendations_text = NO_MARKERS_FOUND_MSG
        
        # Save report to database
        report = Report(
            user_id=current_user.id,
            filename=report_filename,
            file_path=file_path,
            file_type=file_type,
            extracted_text=text,
            extracted_markers=extracted,
            flagged_markers=flagged,
            ai_recommendations=recommendations_text
        )
        
        db.add(report)
        db.commit()
        db.refresh(report)
        
        # Create chat session and add messages
        chat_session = ChatSession(
            user_id=current_user.id,
            title=f"Report Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)
        
        # Add user message
        user_message = ChatMessage(
            session_id=chat_session.id,
            role="user",
            content=f"Uploaded report: {report_filename}"
        )
        db.add(user_message)
        
        # Add assistant message
        assistant_message = ChatMessage(
            session_id=chat_session.id,
            role="assistant",
            content=recommendations_text
        )
        db.add(assistant_message)
        
        db.commit()
        
        return {
            "report_id": report.id,
            "chat_session_id": chat_session.id,
            "recommendations": recommendations_text,
            "flagged": flagged,
            "extracted": extracted
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing file: {str(e)}"
        )

@router.get("/reports")
async def get_user_reports(
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    reports = db.query(Report).filter(Report.user_id == current_user.id).order_by(Report.uploaded_at.desc()).all()
    return reports

@router.get("/reports/{report_id}")
async def get_report(
    report_id: str,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.user_id == current_user.id
    ).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    return report
