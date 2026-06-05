from pydantic import BaseModel, EmailStr, Field


class UserProfileRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    avatar_url: str | None = None

    model_config = {
        "from_attributes": True,
    }


class UserProfileUpdate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr