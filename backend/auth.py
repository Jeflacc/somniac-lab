import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
import jwt
import httpx
import random
import time
from sqlalchemy.orm import Session

from database import get_db
import models
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 1 week
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password[:72], hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password[:72])

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    return user

async def send_otp_email(email: str, otp: str):
    if not RESEND_API_KEY:
        print("[AUTH] RESEND_API_KEY not set, skipping email")
        return False
    
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }
    html_content = f"""
    <div style="font-family: sans-serif; max-width: 500px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
        <h2 style="color: #333; text-align: center;">Somniac Lab Security Code</h2>
        <p style="font-size: 16px; color: #555;">Hello,</p>
        <p style="font-size: 16px; color: #555;">Your verification code for Somniac Lab is:</p>
        <div style="background: #f4f4f4; padding: 20px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #000; border-radius: 5px; margin: 20px 0;">
            {otp}
        </div>
        <p style="font-size: 14px; color: #999; text-align: center;">This code will expire in 10 minutes.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;" />
        <p style="font-size: 12px; color: #bbb; text-align: center;">&copy; 2026 Somniac Lab. All rights reserved.</p>
    </div>
    """
    
    data = {
        "from": "Somniac Lab <auth@somniac.me>",
        "to": [email],
        "subject": f"{otp} is your Somniac Lab verification code",
        "html": html_content
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, headers=headers, json=data)
            if resp.status_code == 200 or resp.status_code == 201:
                return True
            else:
                print(f"[RESEND ERROR] {resp.status_code}: {resp.text}")
                return False
        except Exception as e:
            print(f"[RESEND EXCEPTION] {e}")
            return False

# --- Router ---
auth_router = APIRouter()

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    username: Optional[str] = None

class VerifyRequest(BaseModel):
    username: str
    otp: str

@auth_router.post("/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(
        (models.User.username == user.username) | (models.User.email == user.email)
    ).first()
    
    if db_user:
        # If user exists but is not verified, we can overwrite/update OTP
        if db_user.is_verified:
            if db_user.username == user.username:
                raise HTTPException(status_code=400, detail="Username already registered")
            else:
                raise HTTPException(status_code=400, detail="Email already registered")
        else:
            # Update password if it changed during retry
            db_user.hashed_password = get_password_hash(user.password)
    else:
        hashed_password = get_password_hash(user.password)
        db_user = models.User(username=user.username, email=user.email, hashed_password=hashed_password, is_verified=False)
        db.add(db_user)

    # Generate OTP
    otp = "".join([str(random.randint(0, 9)) for _ in range(6)])
    db_user.otp = otp
    db_user.otp_expiry = time.time() + 600 # 10 mins
    db.commit()

    # Send Email
    success = await send_otp_email(user.email, otp)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send verification email")

    return {"msg": "Verification code sent to your email"}

@auth_router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate OTP for login
    otp = "".join([str(random.randint(0, 9)) for _ in range(6)])
    user.otp = otp
    user.otp_expiry = time.time() + 600 # 10 mins
    db.commit()

    # Send Email
    success = await send_otp_email(user.email, otp)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send verification email")

    return {"msg": "Verification code sent to your email", "require_otp": True}

@auth_router.post("/verify-otp", response_model=Token)
async def verify_otp(req: VerifyRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == req.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.otp or user.otp != req.otp:
        raise HTTPException(status_code=400, detail="Invalid verification code")
    
    if time.time() > user.otp_expiry:
        raise HTTPException(status_code=400, detail="Verification code expired")
    
    # Clear OTP and verify user
    user.otp = None
    user.otp_expiry = None
    user.is_verified = True
    db.commit()
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "username": user.username}
