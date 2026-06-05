from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import (create_access_token, hash_password, verify_password,)
from app.modules.auth.models import User
from app.modules.auth.schemas import UserCreate

def register_user(db: Session, payload: UserCreate,) -> User:

    existing = (
        db.query(User)
        .filter(User.email == payload.email)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado",
        )

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(
            payload.password
        ),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

def login_user(db: Session, email: str, password: str,) -> str:

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
        
    if not verify_password(
        password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
    return create_access_token({
        "sub": str(user.id),
    })