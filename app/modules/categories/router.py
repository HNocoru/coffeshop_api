from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies.database import (
    get_current_user,
    get_db,
)

from app.modules.categories import service

from app.modules.categories.schemas import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
)

router = APIRouter(
    prefix="/api/categories",
    tags=["Categories"],
)


@router.get(
    "/",
    response_model=list[CategoryRead],
)
def list_categories(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return service.get_all(db)


@router.get(
    "/{category_id}",
    response_model=CategoryRead,
)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return service.get_by_id(
        db,
        category_id,
    )


@router.post(
    "/",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return service.create(
        db,
        payload,
    )


@router.put(
    "/{category_id}",
    response_model=CategoryRead,
)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return service.update(
        db,
        category_id,
        payload,
    )


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    service.delete(
        db,
        category_id,
    )