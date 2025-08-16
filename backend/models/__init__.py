from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    date_of_birth = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    reports = relationship("Report", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")
    wearable_data = relationship("WearableData", back_populates="user")

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=True)
    file_type = Column(String)  # pdf, image, etc.
    extracted_text = Column(Text)
    extracted_markers = Column(JSON)  # Store parsed markers
    flagged_markers = Column(JSON)  # Store abnormal markers
    ai_recommendations = Column(Text)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="reports")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")

class WearableData(Base):
    __tablename__ = "wearable_data"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    device_type = Column(String, nullable=False)  # fitbit, apple_watch, etc.
    data_type = Column(String, nullable=False)  # steps, heart_rate, sleep, etc.
    value = Column(Float)
    unit = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    raw_data = Column(JSON)  # Store complete data from device
    
    # Relationships
    user = relationship("User", back_populates="wearable_data")
