from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import os
from dotenv import load_dotenv
from database import get_db
from models import User
import secrets
import string

load_dotenv()

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_security = HTTPBearer(auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(_security), db: Session = Depends(get_db)):
    if credentials is None or not getattr(credentials, "credentials", None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

# Add password reset token functions
def generate_password_reset_token(email: str) -> str:
    """Generate a secure password reset token"""
    # Create a random token
    token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    
    # Create JWT with email and token
    payload = {
        "email": email,
        "reset_token": token,
        "exp": datetime.utcnow() + timedelta(hours=24)  # 24 hour expiry
    }
    
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify password reset token and return email if valid"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("email")
        if email is None:
            return None
        return email
    except jwt.PyJWTError:
        return None

def is_valid_reset_token(token: str) -> bool:
    """Check if reset token is valid and not expired"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return True
    except jwt.PyJWTError:
        return False
