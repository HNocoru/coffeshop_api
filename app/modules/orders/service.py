from fastapi import HTTPException, status

from sqlalchemy.orm import (
    Session,
    joinedload,
)

from app.modules.orders.models import (
    Order,
    OrderItem,
    OrderStatus,
    VALID_TRANSITIONS,
)

from app.modules.orders.schemas import (
    OrderCreate,
    OrderEdit,
)

from app.modules.products.models import Product


def get_all(
    db: Session,
) -> list[Order]:

    return (
        db.query(Order)
        .options(
            joinedload(Order.items)
            .joinedload(OrderItem.product)
        )
        .all()
    )

def get_active_orders(
    db: Session,
) -> list[Order]:

    return (
        db.query(Order)
        .options(
            joinedload(Order.items)
            .joinedload(OrderItem.product)
        )
        .filter(
            Order.status != OrderStatus.delivered
        )
        .all()
    )
    
def get_by_status(
    db: Session,
    status: OrderStatus,
) -> list[Order]:

    return (
        db.query(Order)
        .options(
            joinedload(Order.items)
            .joinedload(OrderItem.product)
        )
        .filter(
            Order.status == status
        )
        .all()
    )

def get_by_id(
    db: Session,
    order_id: int,
) -> Order:

    order = (
        db.query(Order)
        .options(
            joinedload(Order.items)
            .joinedload(OrderItem.product)
        )
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado",
        )

    return order


def create(
    db: Session,
    payload: OrderCreate,
    user_id: int,
) -> Order:

    if not payload.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La orden debe tener al menos un item",
        )

    try:

        order = Order(
            table_number=payload.table_number,
            notes=payload.notes,
            user_id=user_id,
        )

        db.add(order)

        db.flush()

        total = 0.0

        for item_data in payload.items:

            product = (
                db.query(Product)
                .filter(
                    Product.id == item_data.product_id
                )
                .first()
            )

            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Producto {item_data.product_id} no encontrado",
                )

            if not product.available:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Producto '{product.name}' no está disponible",
                )

            subtotal = (
                product.price
                * item_data.quantity
            )

            total += subtotal

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item_data.quantity,
                unit_price=product.price,
                subtotal=subtotal,
            )

            db.add(order_item)

        order.total = total

        db.commit()

        db.refresh(order)

        return order

    except Exception:
        db.rollback()
        raise

def edit_order(
    db: Session,
    order_id: int,
    payload: OrderEdit,
) -> Order:

    order = get_by_id(
        db,
        order_id,
    )

    if order.status == OrderStatus.delivered:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede editar una orden entregada",
        )

    if payload.table_number is not None:
        order.table_number = payload.table_number

    if payload.notes is not None:
        order.notes = payload.notes

    if payload.items is not None:

        order.items.clear()

        total = 0.0

        for item_data in payload.items:

            product = (
                db.query(Product)
                .filter(
                    Product.id == item_data.product_id
                )
                .first()
            )

            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=(
                        f"Producto "
                        f"{item_data.product_id} "
                        f"no encontrado"
                    ),
                )

            if not product.available:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Producto "
                        f"'{product.name}' "
                        f"no disponible"
                    ),
                )

            subtotal = (
                product.price
                * item_data.quantity
            )

            total += subtotal

            item = OrderItem(
                product_id=product.id,
                quantity=item_data.quantity,
                unit_price=product.price,
                subtotal=subtotal,
            )

            order.items.append(item)

        order.total = total

    db.commit()

    db.refresh(order)

    return order

def update_status(
    db: Session,
    order_id: int,
    new_status: OrderStatus,
) -> Order:

    order = get_by_id(
        db,
        order_id,
    )

    expected_next = VALID_TRANSITIONS[
        order.status
    ]

    if expected_next is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El pedido ya fue entregado",
        )

    if new_status != expected_next:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Transición inválida: "
                f"{order.status} -> {new_status}. "
                f"Esperado: {expected_next}"
            ),
        )

    order.status = new_status

    db.commit()

    db.refresh(order)

    return order


def delete(
    db: Session,
    order_id: int,
) -> None:

    order = get_by_id(
        db,
        order_id,
    )

    if order.status == OrderStatus.delivered:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar un pedido entregado",
        )

    db.delete(order)

    db.commit()