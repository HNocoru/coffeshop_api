import enum

from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.database import Base


class OrderStatus(str, enum.Enum):
    pending = "pending"
    preparing = "preparing"
    ready = "ready"
    delivered = "delivered"


VALID_TRANSITIONS = {
    OrderStatus.pending: OrderStatus.preparing,
    OrderStatus.preparing: OrderStatus.ready,
    OrderStatus.ready: OrderStatus.delivered,
    OrderStatus.delivered: None,
}


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    table_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus),
        default=OrderStatus.pending,
    )

    notes: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    total: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    user = relationship(
        "User",
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    unit_price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    subtotal: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    order = relationship(
        "Order",
        back_populates="items",
    )

    product = relationship(
        "Product",
    )