# Step 10: Auth routes � paste code here
# backend/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.db.database import get_db
from backend.db.models import User, SubscriptionTier
from backend.config import settings
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["auth"])
pwd = CryptContext(schemes=["bcrypt"])

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AdminRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    admin_secret: str  # Secret key to create admin account

def create_token(user_id: str):
    expire = datetime.utcnow() + timedelta(days=30)
    return jwt.encode({"sub": user_id, "exp": expire}, settings.JWT_SECRET, algorithm="HS256")

@router.post("/register")
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == payload.email))
    existing_user = existing.scalar_one_or_none()  # type: ignore
    if existing_user is not None:  # type: ignore
        raise HTTPException(status_code=400, detail="Email already registered")

    # Enforce bcrypt 72-byte limit and surface clear errors
    pw_bytes = payload.password.encode("utf-8")
    if len(pw_bytes) > 72:
        raise HTTPException(status_code=400, detail="Password too long; maximum 72 bytes. Choose a shorter password.")

    try:
        hashed = pwd.hash(payload.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Password hashing error: {str(e)}")

    user = User(email=payload.email, hashed_password=hashed)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"token": create_token(str(user.id)), "user_id": str(user.id)}  # type: ignore


@router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()  # type: ignore
    if user is None or not pwd.verify(payload.password, user.hashed_password):  # type: ignore
        raise HTTPException(401, "Invalid credentials")
    return {"token": create_token(str(user.id)), "user_id": str(user.id), "tier": user.tier.value, "is_admin": user.is_admin}  # type: ignore


@router.post("/admin/register")
async def admin_register(payload: AdminRegisterRequest, db: AsyncSession = Depends(get_db)):
    """Create an admin account with a secret key."""
    # Use environment variable for admin secret key
    admin_secret = getattr(settings, "ADMIN_SECRET_KEY", "admin_secret_key_changeme")
    
    if payload.admin_secret != admin_secret:
        raise HTTPException(status_code=403, detail="Invalid admin secret")
    
    existing = await db.execute(select(User).where(User.email == payload.email))
    existing_user = existing.scalar_one_or_none()  # type: ignore
    if existing_user is not None:  # type: ignore
        raise HTTPException(status_code=400, detail="Email already registered")

    pw_bytes = payload.password.encode("utf-8")
    if len(pw_bytes) > 72:
        raise HTTPException(status_code=400, detail="Password too long; maximum 72 bytes. Choose a shorter password.")

    try:
        hashed = pwd.hash(payload.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Password hashing error: {str(e)}")

    user = User(
        email=payload.email,
        hashed_password=hashed,
        is_admin=True,
        tier=SubscriptionTier.ADMIN,
        agent_limit=999
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {
        "token": create_token(str(user.id)),  # type: ignore
        "user_id": str(user.id),  # type: ignore
        "tier": user.tier.value,
        "is_admin": user.is_admin,
        "message": "Admin account created successfully"
    }