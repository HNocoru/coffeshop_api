from fastapi import (
    APIRouter,
    Depends,
    status,
)

from sqlalchemy.orm import Session

from app.dependencies.database import (
    get_current_user,
    get_db,
)

from app.modules.auth.models import User

from app.modules.orders import service

from app.modules.orders.schemas import (
    OrderCreate,
    OrderRead,
    OrderUpdateStatus,
)

router = APIRouter(
    prefix="/api/orders",
    tags=["Orders"],
)


@router.get(
    "/",
    response_model=list[OrderRead],
)
def list_orders(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return service.get_all(db)


@router.get(
    "/{order_id}",
    response_model=OrderRead,
)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return service.get_by_id(
        db,
        order_id,
    )


@router.post(
    "/",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.create(
        db,
        payload,
        current_user.id,
    )


@router.put(
    "/{order_id}",
    response_model=OrderRead,
)
def update_order_status(
    order_id: int,
    payload: OrderUpdateStatus,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return service.update_status(
        db,
        order_id,
        payload.status,
    )


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    service.delete(
        db,
        order_id,
    )