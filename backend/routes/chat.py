from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from database import get_db
from models import User, ChatSession, ChatMessage
from utils.auth import verify_token
from utils.agent_manager import run_agent

router = APIRouter()

class ChatMessageCreate(BaseModel):
    content: str

class ChatSessionCreate(BaseModel):
    title: Optional[str] = None

class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    timestamp: str

class ChatSessionResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.updated_at.desc()).all()
    
    return [
        ChatSessionResponse(
            id=session.id,
            title=session.title,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat() if session.updated_at else session.created_at.isoformat(),
            message_count=len(session.messages)
        )
        for session in sessions
    ]

@router.get("/sessions/{session_id}/messages")
async def get_chat_messages(
    session_id: str,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    # Verify session belongs to user
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.timestamp).all()
    
    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at.isoformat(),
        "messages": [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "timestamp": message.timestamp.isoformat()
            }
            for message in messages
        ]
    }

@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    message_data: ChatMessageCreate,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    # Verify session belongs to user
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Add user message
    user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=message_data.content
    )
    db.add(user_message)
    db.commit()
    
    # Generate AI response
    try:
        # Get user's recent lab reports and extract markers
        from models import Report
        recent_reports = db.query(Report).filter(
            Report.user_id == current_user.id
        ).order_by(Report.uploaded_at.desc()).limit(3).all()
        
        # Extract all markers from recent reports
        all_markers = []
        for report in recent_reports:
            if report.extracted_markers:
                for marker_name, marker_data in report.extracted_markers.items():
                    all_markers.append({
                        "name": marker_name,
                        "value": marker_data.get("value", 0),
                        "unit": marker_data.get("unit", ""),
                        "status": marker_data.get("status", "normal"),
                        "recommendation": marker_data.get("recommendation", "")
                    })
        
        # Get conversation context (last 10 messages for context)
        recent_messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.timestamp.desc()).limit(10).all()
        
        # Build chat history for context
        chat_history = []
        for msg in reversed(recent_messages):
            chat_history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Generate AI response with markers and chat history using RAG
        ai_response = run_agent(
            prompt=message_data.content,
            markers=all_markers if all_markers else None,
            chat_history=chat_history if chat_history else None,
            user_id=str(current_user.id)
        )
        
    except Exception as e:
        ai_response = "I'm sorry, I'm having trouble processing your request right now. Please try again later."
    
    # Add AI response
    ai_message = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=ai_response
    )
    db.add(ai_message)
    
    # Update session timestamp
    session.updated_at = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.timestamp.desc()).first().timestamp
    
    db.commit()
    
    return {
        "id": ai_message.id,
        "role": ai_message.role,
        "content": ai_message.content,
        "timestamp": ai_message.timestamp.isoformat()
    }

@router.get("/rag-test/{user_id}")
async def test_rag_system(
    user_id: str,
    query: str,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Test endpoint for RAG system."""
    try:
        from utils.rag_manager import rag_manager
        
        # Test RAG retrieval
        context = rag_manager.retrieve_relevant_context(user_id, query)
        
        # Get user markers summary
        markers_summary = rag_manager.get_user_markers_summary(user_id)
        
        return {
            "query": query,
            "context": context,
            "markers_summary": markers_summary,
            "status": "success"
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }

@router.post("/sessions")
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    title = session_data.title
    if not title:
        title = f"New Chat - {db.query(ChatSession).filter(ChatSession.user_id == current_user.id).count() + 1}"
    
    session = ChatSession(
        user_id=current_user.id,
        title=title
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return ChatSessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat() if session.updated_at else session.created_at.isoformat(),
        message_count=0
    )

@router.get("/last-session")
async def get_last_session(
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get user's last used session"""
    # Get the most recently updated session
    session = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.updated_at.desc()).first()
    
    if not session:
        return None
    
    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat() if session.updated_at else session.created_at.isoformat()
    }

@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Delete a chat session and all its messages"""
    # Verify the session belongs to the current user
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Delete all messages in the session
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    
    # Delete the session
    db.delete(session)
    db.commit()
    
    return {"message": "Session deleted successfully"}

@router.post("/test-ai")
async def test_ai_with_markers(
    test_data: dict
):
    """Test endpoint for AI functionality with specific markers."""
    try:
        # Extract test data
        markers = test_data.get("markers", [])
        user_message = test_data.get("message", "")
        chat_history = test_data.get("chat_history", [])
        user_id = test_data.get("user_id", "test_user")
        
        # Generate AI response
        from utils.agent_manager import run_agent
        ai_response = run_agent(
            prompt=user_message,
            markers=markers if markers else None,
            chat_history=chat_history if chat_history else None,
            user_id=user_id
        )
        
        return {
            "user_message": user_message,
            "ai_response": ai_response,
            "markers_used": [m.get("name") for m in markers],
            "chat_history_length": len(chat_history)
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "user_message": user_message,
            "markers_used": [m.get("name") for m in markers] if markers else []
        }
