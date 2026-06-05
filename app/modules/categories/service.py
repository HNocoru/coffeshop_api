from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.categories.models import Category
from app.modules.categories.schemas import (
    CategoryCreate,
    CategoryUpdate,
)


def get_all(
    db: Session,
) -> list[Category]:

    return db.query(Category).all()


def get_by_id(
    db: Session,
    category_id: int,
) -> Category:

    category = (
        db.query(Category)
        .filter(Category.id == category_id)
        .first()
    )

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada",
        )

    return category


def create(
    db: Session,
    payload: CategoryCreate,
) -> Category:

    category = Category(
        **payload.model_dump()
    )

    db.add(category)

    db.commit()

    db.refresh(category)

    return category


def update(
    db: Session,
    category_id: int,
    payload: CategoryUpdate,
) -> Category:

    category = get_by_id(
        db,
        category_id,
    )

    update_data = payload.model_dump(
        exclude_none=True
    )

    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()

    db.refresh(category)

    return category


def delete(
    db: Session,
    category_id: int,
) -> None:

    category = get_by_id(
        db,
        category_id,
    )

    db.delete(category)

    db.commit()