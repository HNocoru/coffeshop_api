from fastapi import HTTPException, status

from sqlalchemy.orm import Session

from app.modules.auth.models import User

from app.modules.users.schemas import (
    UserProfileUpdate,
)


def get_profile(
    db: Session,
    user_id: int,
) -> User:

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    return user


def update_profile(
    db: Session,
    user_id: int,
    payload: UserProfileUpdate,
) -> User:

    user = get_profile(
        db,
        user_id,
    )

    existing_user = (
        db.query(User)
        .filter(
            User.email == payload.email,
            User.id != user_id,
        )
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado",
        )

    user.name = payload.name
    user.email = payload.email

    db.commit()

    db.refresh(user)

    return user