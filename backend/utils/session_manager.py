import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

class SessionManager:
    """Manages per-session context, markers, and chat history."""
    
    def __init__(self):
        # In-memory storage for session data (in production, use Redis or database)
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Create a new session with initial context."""
        session_data = {
            "user_id": user_id,
            "session_id": session_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "markers": [],  # Dynamic markers added during session
            "chat_history": [],
            "context_summary": "",
            "active_markers": set(),  # Markers discussed in current conversation
            "session_metadata": {}
        }
        self.sessions[session_id] = session_data
        return session_data
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by ID."""
        return self.sessions.get(session_id)
    
    def add_markers_to_session(self, session_id: str, markers: List[Dict[str, Any]]) -> bool:
        """Add markers to session context."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        # Add new markers, avoiding duplicates
        existing_marker_names = {m.get("name", "").lower() for m in session["markers"]}
        
        for marker in markers:
            marker_name = marker.get("name", "").lower()
            if marker_name not in existing_marker_names:
                session["markers"].append(marker)
                existing_marker_names.add(marker_name)
        
        session["updated_at"] = datetime.utcnow()
        return True
    
    def add_chat_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """Add a chat message to session history."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        message = {
            "id": str(uuid.uuid4()),
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow(),
            "metadata": metadata or {}
        }
        
        session["chat_history"].append(message)
        session["updated_at"] = datetime.utcnow()
        return True
    
    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get complete session context for AI processing."""
        session = self.get_session(session_id)
        if not session:
            return {}
        
        return {
            "session_id": session_id,
            "user_id": session["user_id"],
            "markers": session["markers"],
            "chat_history": session["chat_history"],
            "active_markers": list(session["active_markers"]),
            "context_summary": session["context_summary"],
            "session_metadata": session["session_metadata"]
        }
    
    def update_active_markers(self, session_id: str, marker_names: List[str]) -> bool:
        """Update which markers are currently being discussed."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session["active_markers"].update(marker_names)
        session["updated_at"] = datetime.utcnow()
        return True
    
    def extract_markers_from_message(self, message: str) -> List[str]:
        """Extract marker names mentioned in a message."""
        # This is a simple extraction - can be enhanced with NLP
        marker_names = []
        message_lower = message.lower()
        
        # Common marker patterns
        marker_patterns = [
            "magnesium", "calcium", "iron", "ferritin", "vitamin d", "vitamin b12", "selenium",
            "zinc", "copper", "potassium", "sodium", "chloride", "glucose", "hba1c", "a1c",
            "cholesterol", "hdl", "ldl", "triglycerides", "creatinine", "bun", "alt", "ast",
            "bilirubin", "albumin", "hemoglobin", "hematocrit", "wbc", "platelets", "tsh",
            "t3", "t4", "cortisol", "insulin", "c-peptide", "c reactive protein", "crp"
        ]
        
        for pattern in marker_patterns:
            if pattern in message_lower:
                marker_names.append(pattern)
        
        return marker_names
    
    def update_context_summary(self, session_id: str, summary: str) -> bool:
        """Update session context summary."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session["context_summary"] = summary
        session["updated_at"] = datetime.utcnow()
        return True
    
    def get_relevant_markers_for_query(self, session_id: str, query: str) -> List[Dict[str, Any]]:
        """Get markers relevant to the current query."""
        session = self.get_session(session_id)
        if not session:
            return []
        
        # Extract marker names from query
        mentioned_markers = self.extract_markers_from_message(query)
        
        # If specific markers are mentioned, return those
        if mentioned_markers:
            relevant_markers = []
            for marker in session["markers"]:
                marker_name = marker.get("name", "").lower()
                if any(mentioned in marker_name for mentioned in mentioned_markers):
                    relevant_markers.append(marker)
            return relevant_markers
        
        # Otherwise, return all session markers
        return session["markers"]
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old sessions to prevent memory leaks."""
        current_time = datetime.utcnow()
        sessions_to_remove = []
        
        for session_id, session_data in self.sessions.items():
            age = (current_time - session_data["updated_at"]).total_seconds() / 3600
            if age > max_age_hours:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.sessions[session_id]
        
        return len(sessions_to_remove)

# Global session manager instance
session_manager = SessionManager()
