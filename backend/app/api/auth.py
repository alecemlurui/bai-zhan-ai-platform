"""
api/auth.py

认证相关 API。
"""

from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import get_current_active_user
from ..models import User
from ..schemas import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from ..services.auth import authenticate_user, create_access_token, register_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(payload: UserRegisterRequest):
    try:
        user = await register_user(payload.username, payload.password, payload.email)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return user


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLoginRequest):
    user = await authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token({"sub": str(user.id), "username": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 3600,
    }


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_active_user)):
    return current_user
