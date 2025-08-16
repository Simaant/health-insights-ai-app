from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import timedelta
from typing import Optional
from database import get_db
from models import User
from utils.auth import (
    authenticate_user, 
    create_access_token, 
    get_password_hash, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    verify_token,
    generate_password_reset_token,
    verify_password_reset_token,
    is_valid_reset_token
)
import os

router = APIRouter()

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class PasswordResetResponse(BaseModel):
    message: str

@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return UserResponse(
        id=db_user.id,
        email=db_user.email,
        first_name=db_user.first_name,
        last_name=db_user.last_name
    )

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_current_user(current_user: User = Depends(verify_token)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name
    )

@router.post("/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset for an email"""
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        # Don't reveal if email exists or not for security
        return PasswordResetResponse(
            message="If the email exists, a password reset link has been sent."
        )
    
    # Generate reset token
    reset_token = generate_password_reset_token(request.email)
    
    # In a real application, you would send this via email
    # For now, we'll return it in the response for testing
    # TODO: Implement email sending functionality
    
    return PasswordResetResponse(
        message=f"Password reset token generated. In production, this would be sent via email. Token: {reset_token}"
    )

@router.post("/reset-password", response_model=PasswordResetResponse)
async def reset_password(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Reset password using token"""
    # Verify token and get email
    email = verify_password_reset_token(request.token)
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Find user
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.password_hash = get_password_hash(request.new_password)
    db.commit()
    
    return PasswordResetResponse(
        message="Password has been reset successfully"
    )

@router.get("/verify-reset-token/{token}")
async def verify_reset_token(token: str):
    """Verify if a reset token is valid"""
    is_valid = is_valid_reset_token(token)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    return {"valid": True, "message": "Token is valid"}
