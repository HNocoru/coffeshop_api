from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.categories.models import Category

from app.modules.products.models import Product

from app.modules.products.schemas import (
    ProductCreate,
    ProductUpdate,
)


def get_all(
    db: Session,
) -> list[Product]:

    return db.query(Product).all()


def get_by_id(
    db: Session,
    product_id: int,
) -> Product:

    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado",
        )

    return product


def create(
    db: Session,
    payload: ProductCreate,
) -> Product:

    category = (
        db.query(Category)
        .filter(Category.id == payload.category_id)
        .first()
    )

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada",
        )

    product = Product(
        **payload.model_dump()
    )

    db.add(product)

    db.commit()

    db.refresh(product)

    return product


def update(
    db: Session,
    product_id: int,
    payload: ProductUpdate,
) -> Product:

    product = get_by_id(
        db,
        product_id,
    )

    update_data = payload.model_dump(
        exclude_none=True
    )

    # Validar FK si viene category_id
    if "category_id" in update_data:

        category = (
            db.query(Category)
            .filter(
                Category.id == update_data["category_id"]
            )
            .first()
        )

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoría no encontrada",
            )

    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()

    db.refresh(product)

    return product


def delete(
    db: Session,
    product_id: int,
) -> None:

    product = get_by_id(
        db,
        product_id,
    )

    db.delete(product)

    db.commit()