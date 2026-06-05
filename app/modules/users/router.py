from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.orm import Session

from app.dependencies.database import (
    get_current_user,
    get_db,
)

from app.modules.auth.models import User

from app.modules.users import service

from app.modules.users.schemas import (
    UserProfileRead,
    UserProfileUpdate,
)

router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=UserProfileRead,
)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_profile(
        db,
        current_user.id,
    )


@router.put(
    "/me",
    response_model=UserProfileRead,
)
def update_my_profile(
    payload: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.update_profile(
        db,
        current_user.id,
        payload,
    )