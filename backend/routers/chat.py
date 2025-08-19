from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from ..database import get_db
from ..models.chat import ChatSession, ChatMessage
from ..models.user import User
from ..models.report import Report
from ..schemas.chat import ChatSessionCreate, ChatSessionResponse, ChatMessageCreate, ChatMessageResponse
from ..auth import get_current_user
from ..utils.agent_manager import run_agent
from ..utils.session_manager import session_manager
from ..utils.health_marker_detector import HealthMarkerDetector

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize marker detector
marker_detector = HealthMarkerDetector()

@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session with enhanced session management."""
    # Create database session
    session = ChatSession(
        user_id=current_user.id,
        title=session_data.title or f"New Chat - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Initialize session manager with user's existing markers
    session_manager.create_session(str(current_user.id), session.id)
    
    # Get user's recent lab reports and add markers to session
    recent_reports = db.query(Report).filter(
        Report.user_id == current_user.id
    ).order_by(Report.uploaded_at.desc()).limit(5).all()
    
    all_markers = []
    for report in recent_reports:
        if report.markers:
            all_markers.extend(report.markers)
    
    # Add markers to session context
    if all_markers:
        session_manager.add_markers_to_session(session.id, all_markers)
    
    return session

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all chat sessions for the current user."""
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).all()
    return sessions

@router.post("/sessions/{session_id}/messages", response_model=dict)
async def send_message(
    session_id: str,
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message in a chat session with enhanced context management."""
    # Verify session belongs to user
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # Get or create session manager context
    session_context = session_manager.get_session(session_id)
    if not session_context:
        # Initialize session if not exists
        session_manager.create_session(str(current_user.id), session_id)
        session_context = session_manager.get_session(session_id)
    
    # Extract markers from user message if any
    extracted_markers = marker_detector.extract_markers_from_text(message_data.content)
    if extracted_markers:
        # Convert to dict format for session manager
        marker_dicts = []
        for marker in extracted_markers:
            marker_dicts.append({
                "name": marker.name,
                "value": marker.value,
                "unit": marker.unit,
                "status": marker.status,
                "normalRange": f"{marker.normal_range.get('min', 'N/A')}-{marker.normal_range.get('max', 'N/A')}",
                "recommendation": marker.recommendation
            })
        
        # Add new markers to session
        session_manager.add_markers_to_session(session_id, marker_dicts)
    
    # Add user message to session history
    session_manager.add_chat_message(session_id, "user", message_data.content)
    
    # Save user message to database
    user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=message_data.content
    )
    db.add(user_message)
    db.commit()
    
    # Get session context for AI processing
    session_context = session_manager.get_session_context(session_id)
    
    # Extract mentioned markers from user message
    mentioned_markers = session_manager.extract_markers_from_message(message_data.content)
    if mentioned_markers:
        session_manager.update_active_markers(session_id, mentioned_markers)
    
    # Get relevant markers for this query
    relevant_markers = session_manager.get_relevant_markers_for_query(session_id, message_data.content)
    
    # Convert chat history to format expected by agent_manager
    chat_history = []
    for msg in session_context.get("chat_history", [])[:-1]:  # Exclude current message
        chat_history.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Generate AI response with enhanced context
    ai_response_content = run_agent(
        message_data.content, 
        markers=relevant_markers if relevant_markers else None,
        chat_history=chat_history,
        user_id=str(current_user.id)
    )
    
    # Add AI response to session history
    session_manager.add_chat_message(session_id, "assistant", ai_response_content)
    
    # Save AI response to database
    ai_message = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=ai_response_content
    )
    db.add(ai_message)
    
    # Update session message count
    session.message_count += 2  # User message + AI response
    session.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "user_message": {
            "id": user_message.id,
            "role": user_message.role,
            "content": user_message.content,
            "timestamp": user_message.timestamp
        },
        "ai_response": {
            "id": ai_message.id,
            "role": ai_message.role,
            "content": ai_message.content,
            "timestamp": ai_message.timestamp
        },
        "session_context": {
            "active_markers": list(session_context.get("active_markers", [])),
            "total_markers": len(session_context.get("markers", [])),
            "message_count": len(session_context.get("chat_history", []))
        }
    }

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_chat_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all messages in a chat session."""
    # Verify session belongs to user
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.timestamp).all()
    
    return messages

@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a chat session and all its messages."""
    # Verify session belongs to user
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # Delete all messages in the session
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    
    # Delete the session
    db.delete(session)
    db.commit()
    
    return {"message": "Chat session deleted successfully"}


