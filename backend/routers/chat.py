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

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session."""
    session = ChatSession(
        user_id=current_user.id,
        title=session_data.title or f"New Chat - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
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
    """Send a message in a chat session and get AI response."""
    # Verify session belongs to user
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # Save user message
    user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=message_data.content
    )
    db.add(user_message)
    db.commit()
    
    # Get user's recent lab reports for context
    recent_reports = db.query(Report).filter(
        Report.user_id == current_user.id
    ).order_by(Report.uploaded_at.desc()).limit(3).all()
    
    # Extract markers from recent reports
    all_markers = []
    for report in recent_reports:
        if report.markers:
            all_markers.extend(report.markers)
    
    # Generate AI response with marker context
    ai_response_content = run_agent(message_data.content, all_markers if all_markers else None)
    
    # Save AI response
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


