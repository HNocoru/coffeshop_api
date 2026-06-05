from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.dependencies.database import get_db
from app.modules.auth.schemas import (TokenResponse, UserCreate, UserLogin, UserRead,)
from app.modules.auth.service import (login_user, register_user,)

router = APIRouter(prefix="/api/auth", tags=["auth"],)

@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: UserCreate,
    db: Session = Depends(get_db),
):
    return register_user(
        db,
        payload,
    )

@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    payload: UserLogin,
    db: Session = Depends(get_db),
):
    token = login_user(
        db,
        payload.email,
        payload.password,
    )

    return TokenResponse(
        access_token=token,
    )