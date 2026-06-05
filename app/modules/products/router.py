from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies.database import (
    get_current_user,
    get_db,
)

from app.modules.products import service

from app.modules.products.schemas import (
    ProductCreate,
    ProductRead,
    ProductUpdate,
)

router = APIRouter(
    prefix="/api/products",
    tags=["Products"],
)


@router.get(
    "/",
    response_model=list[ProductRead],
)
def list_products(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return service.get_all(db)


@router.get(
    "/{product_id}",
    response_model=ProductRead,
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return service.get_by_id(
        db,
        product_id,
    )


@router.post(
    "/",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return service.create(
        db,
        payload,
    )


@router.put(
    "/{product_id}",
    response_model=ProductRead,
)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return service.update(
        db,
        product_id,
        payload,
    )


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    service.delete(
        db,
        product_id,
    )