from pydantic import BaseModel, Field

from app.modules.orders.models import OrderStatus


class OrderItemCreate(BaseModel):
    product_id: int

    quantity: int = Field(
        gt=0,
    )


class OrderCreate(BaseModel):
    table_number: int = Field(
        gt=0,
    )

    notes: str | None = None

    items: list[OrderItemCreate]


class OrderUpdateStatus(BaseModel):
    status: OrderStatus


class OrderItemRead(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    subtotal: float

    model_config = {
        "from_attributes": True,
    }


class OrderRead(BaseModel):
    id: int
    table_number: int
    status: OrderStatus
    total: float
    notes: str | None
    items: list[OrderItemRead]

    model_config = {
        "from_attributes": True,
    }