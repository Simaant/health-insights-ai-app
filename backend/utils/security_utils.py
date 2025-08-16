from cryptography.fernet import Fernet
import json, os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Request

load_dotenv()
key = os.getenv("FIELD_ENCRYPTION_KEY").encode()
fernet = Fernet(key)

def encrypt_data(data: dict) -> str:
    return fernet.encrypt(json.dumps(data).encode()).decode()

def decrypt_data(token: str) -> dict:
    return json.loads(fernet.decrypt(token.encode()).decode())

def deidentify_data(data: dict) -> dict:
    return {k: v for k, v in data.items() if k.lower() not in ["name", "dob", "email"]}

def verify_user_role(user: dict, allowed_roles: list):
    if user.get("role") not in allowed_roles:
        raise HTTPException(status_code=403, detail="Access denied")

def verify_token(request: Request):
    token = request.headers.get("Authorization")
    if not token or token != "Bearer your_expected_token":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"user": "mock_user", "role": "patient"}
