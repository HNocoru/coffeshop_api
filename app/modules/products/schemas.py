from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=255,
    )

    price: float = Field(
        gt=0,
    )

    image_url: str | None = None

    available: bool = True

    category_id: int


class ProductUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=255,
    )

    price: float | None = Field(
        default=None,
        gt=0,
    )

    image_url: str | None = None

    available: bool | None = None

    category_id: int | None = None


class ProductRead(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    image_url: str | None
    available: bool
    category_id: int

    model_config = {
        "from_attributes": True,
    }